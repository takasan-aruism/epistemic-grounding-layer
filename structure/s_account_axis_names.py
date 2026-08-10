#!/usr/bin/env python3
"""s_account_axis_names — 勘定科目(v2 凍結棚)の命名(2b-2)。LLM 3-seed consensus・id正典/name装飾・幾何不変。

MGR/DESIGN 裁定: 凍結棚(ACCOUNT_AXES_v2 の AX-72ead44e / AX2-48354b9a)に人間可読名を付け帳簿を可読化。
- **id が正典・name は後で変えられる装飾**。命名で凍結メンバーシップ/軸幾何を**一切変えない**(v2/membership_v2 は byte 不変)。
- name は**別 versioned 台帳** `ACCOUNT_AXIS_NAMES.jsonl`(sole-writer=本 stage)に記録。frozen artifact を可変 name で汚さない。
- **決定論部**(対象軸・サンプル選択・consensus 判定)は決定論。**LLM 呼出のみ非決定論**。
- measure-first・捏造ゼロ: consensus 未成立は `UNRESOLVED_NO_CONSENSUS`(無理に付けない)。

初の実 :8005 CALL_SITE(Qwen3.6-35B-A3B・Taka が USE_VLLM_INFERENCE 開放)。--check は LLM を再実行せず
「決定論の封筒(サンプル再現・consensus 規則の記録 proposals への再適用)＋記録の完全性」を検証(record-occurrence 型)。

usage:
  s_account_axis_names.py          # サンプリング→:8005 3-seed→consensus→ACCOUNT_AXIS_NAMES.jsonl 生成
  s_account_axis_names.py --check   # 幾何不変 + サンプル決定論 + consensus 再判定 + provenance 完全性(LLM 不使用)
"""
import hashlib
import json
import os
import re
import sys
import unicodedata

import s_embed_axes as R   # _content_records(クラスタを形成した実 content)を継承

STRUCT = os.path.dirname(os.path.abspath(__file__))
IN_AXES2 = os.path.join(STRUCT, "ACCOUNT_AXES_v2.json")
IN_MEMB2 = os.path.join(STRUCT, "ACCOUNT_MEMBERSHIP_v2.jsonl")
OUT = os.path.join(STRUCT, "ACCOUNT_AXIS_NAMES.jsonl")

MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"   # 実 CALL_SITE(:8005)
SEEDS = (0, 1, 2)
TEMPERATURE = 0.7           # 固定(>0=seed が発散し consensus が意味を持つ)
# Qwen3.6 は reasoning モデル。**曖昧/ノイズ入り prompt だと thinking が発散**(実測: gen-nonce ノイズ+12重複+
# 途中切断だと 8192 でも終端せず)。prompt を clean 化(ノイズ除去+重複除去+文正規化)すると ~3083 tok で正常終端。
# ゆえ prompt 品質が要。budget は観測 ~3083 に余裕をみて 6144(約2x)。truncation(content=None)は明示エラー(捏造しない)。
MAX_TOKENS = 6144
SAMPLE_K = 12
CLIP = 220                  # 各代表 content の提示長(文脈は保ちつつ reasoning を境界づける)
PROMPT_ID = "axis-name-v2"  # v2 = clean 化 prompt(ノイズ除去+重複除去)
PROMPT_HEAD = ("以下は同一カテゴリに分類された依頼群の代表例です。共通の主題を表す簡潔なカテゴリ名"
               "(日本語10〜15文字・体言止め)を1つだけ出力してください。名前のみ、説明不要。\n\n")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _content_map():
    return {nid: txt for nid, kind, txt in R._content_records()}


def _sample(axis_id, memb):
    """§2 決定論サンプル: 軸所属要素を margin_over_null 降順・element_id 昇順で上位 K。"""
    rows = []
    for m in memb:
        for a in m.get("axes", []):
            if a["axis_id"] == axis_id:
                rows.append((m["element_id"], a["margin_over_null"]))
                break
    rows.sort(key=lambda r: (-r[1], str(r[0])))
    return [rid for rid, _ in rows[:min(SAMPLE_K, len(rows))]]


def _clean(txt):
    """prompt 用に content を clean 化(決定論)。gen-nonce 等のノイズ行を除去+空白正規化+CLIP。
    ノイズ/12重複/途中切断は reasoning を発散させるため、意味の要点だけ残す。"""
    lines = [l for l in (txt or "").splitlines() if not l.strip().startswith("# gen-nonce")]
    return " ".join(" ".join(lines).split())[:CLIP]


def _build_prompt(sample_ids, cmap):
    """代表 content を clean 化+重複除去して bullet 提示(決定論)。全12が同一なら1件=曖昧さゼロ。"""
    seen, distinct = set(), []
    for rid in sample_ids:
        c = _clean(cmap.get(rid, ""))
        if c and c not in seen:
            seen.add(c)
            distinct.append(c)
    return PROMPT_HEAD + "\n".join("- %s" % d for d in distinct)


def _norm(s):
    """consensus 比較用 正規化(決定論): NFKC(全半角統一)+ 空白/句読点除去。"""
    s = unicodedata.normalize("NFKC", s or "").strip()
    return re.sub(r"[\s、。・「」『』（）()\[\]【】,.!?！？:：;；]", "", s)


# script-boundary トークン化: 連続する latin / digit / katakana / hiragana / kanji の run を1トークン(決定論)。
_TOKEN_RE = re.compile(r"[A-Za-z]+|[0-9]+|[゠-ヿ]+|[぀-ゟ]+|[一-鿿々〆ヶ]+")


def _tokenize(s):
    """例「JSONLファイル解析CLI作成」→ [JSONL, ファイル, 解析, CLI, 作成](NFKC 正規化後)。"""
    return _TOKEN_RE.findall(unicodedata.normalize("NFKC", s or ""))


def consensus(proposals):
    """記録 proposals({seed:name})を2段で決定論 consolidation(LLM 不使用・drift-tolerant)。
    返り dict: name / name_status / agreement_count(=exact 完全一致の最良数) / consolidated_tokens。"""
    from collections import Counter
    # 1. fast-path: 正規化後 完全一致 ≥2/3
    groups = {}
    for seed in sorted(proposals):
        groups.setdefault(_norm(proposals[seed]), []).append(proposals[seed])
    best = max(sorted(groups), key=lambda k: len(groups[k]))
    agree = len(groups[best])
    if agree >= 2:
        c = Counter(groups[best])
        name = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]   # 最頻の原表記(tie=辞書順)
        return {"name": name, "name_status": "CONSENSUS_EXACT", "agreement_count": agree,
                "consolidated_tokens": None}
    # 2. consolidation(drift 許容): script-boundary トークンが ≥2/3 の proposal に出るものを初出順連結
    n = len(proposals)
    thresh = 2 if n == 3 else max(2, (2 * n + 2) // 3)   # ≥2/3(3seed=2)
    tok_count, first_order = Counter(), []
    for seed in sorted(proposals):
        for t in dict.fromkeys(_tokenize(proposals[seed])):   # 同 proposal 内重複は1回
            tok_count[t] += 1
            if t not in first_order:
                first_order.append(t)
    kept = [t for t in first_order if tok_count[t] >= thresh]
    if kept:
        return {"name": "".join(kept), "name_status": "CONSENSUS_CONSOLIDATED", "agreement_count": agree,
                "consolidated_tokens": [{"token": t, "count": tok_count[t]} for t in kept]}
    return {"name": None, "name_status": "UNRESOLVED_NO_CONSENSUS", "agreement_count": agree,
            "consolidated_tokens": None}


def _llm_propose(prompt, seed):
    """:8005 Qwen に命名させる(実 CALL_SITE)。非決定論部はここだけ。prompt は clean 済み(発散防止)。"""
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    content = ch["message"].get("content")
    if not content:   # thinking が max_tokens を使い切った等=握り潰さず明示(捏造/空名を作らない)
        raise RuntimeError("LLM returned empty content (finish=%s, seed=%d) — MAX_TOKENS 不足の可能性"
                           % (ch.get("finish_reason"), seed))
    return content.strip()


def _paths(version="v2"):
    """★入口を版で選ぶ(★既定は v2=★既存の呼び方を1文字も変えない=★退行0)。"""
    return (os.path.join(STRUCT, "ACCOUNT_AXES_%s.json" % version),
            os.path.join(STRUCT, "ACCOUNT_MEMBERSHIP_%s.jsonl" % version))


def _axes(version="v2"):
    return json.load(open(_paths(version)[0], encoding="utf-8"))["axes"]


def _memb(version="v2"):
    return [json.loads(l) for l in open(_paths(version)[1], encoding="utf-8") if l.strip()]


def _mkrow(aid, sample_ids, proposals, version="v2"):
    con = consensus(proposals)
    return {
        "axis_id": aid, "axes_version": version, "name": con["name"], "name_status": con["name_status"],
        "model": MODEL, "endpoint": ":8005", "seeds": list(SEEDS),
        "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
        "proposals": proposals, "agreement_count": con["agreement_count"],
        "consolidated_tokens": con["consolidated_tokens"],
        "sample_element_ids": sample_ids, "prompt_id": PROMPT_ID, "sampled_k": len(sample_ids),
    }


def build(version="v2", only=None):
    """LLM を実行して命名台帳行を生成(初回 main 用)。
    ★version=版を選ぶ(既定 v2) ／ ★only=軸 id を絞る(★凍結棚に在る軸だけ=★無理に通さない)。"""
    axes, memb, cmap = _axes(version), _memb(version), _content_map()
    rows = []
    for ax in axes:
        aid = ax["axis_id"]
        if only and aid not in only:
            continue
        sample_ids = _sample(aid, memb)
        prompt = _build_prompt(sample_ids, cmap)
        proposals = {str(s): _llm_propose(prompt, s) for s in SEEDS}
        rows.append(_mkrow(aid, sample_ids, proposals, version))
    rows.sort(key=lambda r: r["axis_id"])
    return rows


def reconsolidate(existing_rows):
    """LLM 再呼出なし: 記録済み proposals に新 consensus(2段)を再適用。proposals/sample_ids/model/seeds は不変。"""
    rows = []
    for r in existing_rows:
        con = consensus(r["proposals"])
        nr = dict(r)
        nr.update(name=con["name"], name_status=con["name_status"],
                  agreement_count=con["agreement_count"], consolidated_tokens=con["consolidated_tokens"])
        rows.append(nr)
    rows.sort(key=lambda r: r["axis_id"])
    return rows


def _header():
    return {"_meta": "ACCOUNT_AXIS_NAMES(v2 凍結棚の命名・id正典/name装飾/幾何不変)。LLM 3-seed → 2段 consensus"
                     "(fast-path 完全一致 → drift-tolerant script-boundary トークン consolidation)。"
                     "未成立=UNRESOLVED_NO_CONSENSUS(捏造ゼロ)。--check=決定論再判定+記録完全性(name byte 再現は不要)。",
            "v2_axes_sha256": _sha(IN_AXES2), "v2_membership_sha256": _sha(IN_MEMB2),
            "model": MODEL, "endpoint": ":8005", "prompt_id": PROMPT_ID}


def _header_for(version):
    """★版に合わせた鍵を返す(★v2 は従来の鍵をそのまま=★退行0 ／ ★他の版は axes_version 付きで足す)。"""
    if version == "v2":
        return _header()
    ax, mb = _paths(version)
    h = dict(_header())
    h.update({"axes_version": version, "axes_sha256": _sha(ax), "membership_sha256": _sha(mb)})
    return h


def _ser(rows, header):
    return "\n".join([json.dumps(header, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows]) + "\n"


def check():
    red = []
    if not os.path.isfile(OUT):
        print("ACCOUNT_AXIS_NAMES --check: RED\n  NOT_GENERATED: ACCOUNT_AXIS_NAMES.jsonl 未生成(main を先に)")
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header, rows = lines[0], lines[1:]
    # 1. 幾何不変(最重要): v2/membership が命名生成時から byte 不変
    if header.get("v2_axes_sha256") != _sha(IN_AXES2):
        red.append("GEOMETRY_MUTATED: ACCOUNT_AXES_v2.json が命名後に変化(id正典/幾何不変違反 or 要再命名)")
    if header.get("v2_membership_sha256") != _sha(IN_MEMB2):
        red.append("GEOMETRY_MUTATED: ACCOUNT_MEMBERSHIP_v2.jsonl が変化")
    # ★裁定/承認で定めた名前は LLM 合議の記録を持たない(proposals={})=★consensus 再判定の対象外。
    # ★2026-08-10: 私(実装)が ADOPTED 行を足した時に この検査の対象から外さず、--check を落としていた。
    rows = [r for r in rows if str(r.get("name_status", "")).startswith("CONSENSUS_")
            or r.get("name_status") == "UNRESOLVED_NO_CONSENSUS"]
    # 2. 対象は v2 凍結棚のみ(scope)
    axis_ids = {a["axis_id"] for a in _axes()}
    if {r["axis_id"] for r in rows} != axis_ids:
        red.append("SCOPE_MISMATCH: 命名対象が v2 凍結軸集合と不一致 %s vs %s"
                   % (sorted(r["axis_id"] for r in rows), sorted(axis_ids)))
    memb = _memb()
    for r in rows:
        # 3. サンプル決定論: 記録 sample_element_ids が固定 K/固定ソートで再現(LLM 不使用)
        if r["sample_element_ids"] != _sample(r["axis_id"], memb):
            red.append("SAMPLE_NONDETERMINISTIC: %s の sample_element_ids が再現しない" % r["axis_id"])
        # 4. consensus 決定論再判定(2段: fast-path→consolidation): 記録 proposals に再適用 → 台帳と一致(LLM 不使用)
        con = consensus(r["proposals"])
        got = (r["name"], r["name_status"], r["agreement_count"], r.get("consolidated_tokens"))
        exp = (con["name"], con["name_status"], con["agreement_count"], con["consolidated_tokens"])
        if got != exp:
            red.append("CONSENSUS_MISAPPLIED: %s 記録 proposals から %r だが台帳は %r" % (r["axis_id"], exp, got))
        # 5. provenance 完全性(consolidated_tokens も CONSOLIDATED 時に必須)
        for k in ("model", "endpoint", "seeds", "proposals", "agreement_count", "sample_element_ids", "prompt_id"):
            if k not in r:
                red.append("PROVENANCE_INCOMPLETE: %s に %s 欠落" % (r["axis_id"], k))
        if r["name_status"] == "CONSENSUS_CONSOLIDATED" and not r.get("consolidated_tokens"):
            red.append("CONSOLIDATED_TOKENS_MISSING: %s は CONSOLIDATED だが consolidated_tokens 空" % r["axis_id"])
        if r["name_status"] == "UNRESOLVED_NO_CONSENSUS" and r["name"] is not None:
            red.append("UNRESOLVED_NOT_NULL: %s は未成立だが name が非 null(捏造)" % r["axis_id"])
        if len(r["proposals"]) != len(SEEDS):
            red.append("SEEDS_INCOMPLETE: %s の proposals が %d seed 分でない" % (r["axis_id"], len(SEEDS)))
    if red:
        print("ACCOUNT_AXIS_NAMES --check: RED")
        for m in red:
            print("  " + m)
        return 1
    named = [r for r in rows if r["name_status"] in ("CONSENSUS_EXACT", "CONSENSUS_CONSOLIDATED")]
    print("ACCOUNT_AXIS_NAMES --check: GREEN (幾何不変; サンプル決定論; consensus 記録再判定一致; provenance 完全; "
          "%d/%d 命名成立)" % (len(named), len(rows)))
    for r in rows:
        print("  %s -> %s [%s agree=%d/%d]" % (r["axis_id"], r["name"], r["name_status"],
                                               r["agreement_count"], len(SEEDS)))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if os.path.isfile(OUT) and "--regen-llm" not in argv:
        # 記録済み proposals を決定論で再 consolidation(LLM 再呼出なし・handoff §0)。--regen-llm で強制再取得。
        existing = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()][1:]
        rows, mode = reconsolidate(existing), "reconsolidate(LLM 再呼出なし)"
    else:
        rows, mode = build(), "build(LLM 3-seed :8005)"
    open(OUT, "w", encoding="utf-8").write(_ser(rows, _header()))
    print("[%s]" % mode)
    for r in rows:
        print("%s -> %r [%s agree=%d/%d tokens=%s] proposals=%s"
              % (r["axis_id"], r["name"], r["name_status"], r["agreement_count"], len(SEEDS),
                 [t["token"] for t in (r.get("consolidated_tokens") or [])], list(r["proposals"].values())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
