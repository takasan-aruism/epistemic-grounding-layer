#!/usr/bin/env python3
"""[Claude実装] s_ledger_account_axis_names — ★台帳の明細から出した軸に 名前を付ける(★Taka 許可 2026-08-23)。

★入口=`LEDGER_ACCOUNT_AXES_CANDIDATE.json`(=`s_ledger_account_axes.py` が 出した 軸)。
★出口=`LEDGER_ACCOUNT_AXIS_NAMES.json`(★この段だけが 書く)。
★id が 正典・name は 装飾=★命名で 軸の 幾何も メンバーも 1つも 変えない。

★Taka 指示 2026-08-23=★『基本英語の方がいいとは思ってる。日本語名も入れといてもらえると私はうれしい』
  ∴ ★英語名(正)と ★日本語名(併記)を ★同じ 呼び出しで 1つずつ 出させる。

★合議=既存 `s_account_axis_names.consensus()` を ★そのまま 呼ぶ(★自作しない)。
  ★英語と 日本語で ★別々に 合議する=★片方だけ 割れた 時に もう片方を 巻き添えにしない。
  ★合議が 成り立たない 時は `UNRESOLVED_NO_CONSENSUS`(★推測で 埋めない)。

★依頼文の 作り=★3段に 割って ★肯定形で ★実例を 見せる(★2026-08-23 の 教訓)。

usage:
  s_ledger_account_axis_names.py           # 3-seed で 命名
  s_ledger_account_axis_names.py --check   # LLM 不使用。記録した proposals に 合議を 再適用して 一致を 見る
"""
import importlib.util
import json
import os
import re
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
IN_CAND = os.path.join(STRUCT, "LEDGER_ACCOUNT_AXES_CANDIDATE.json")
# ★`.jsonl` に しない=★毎回 まるごと 作り直す 控えで あって 追記型の 台帳では ない(★2026-08-23)。
OUT = os.path.join(STRUCT, "LEDGER_ACCOUNT_AXIS_NAMES.json")

MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
TEMPERATURE = 0.7
MAX_TOKENS = 6144
CLIP = 200
PROMPT_ID = "ledger-axis-name-en-then-ja-v2"
PARALLEL = 20          # ★軸と軸の 間の 並列数(★Taka 許可 2026-08-23)
TREE_IN = os.path.join(STRUCT, "LEDGER_ACCOUNT_TREE.json")
TREE_OUT = os.path.join(STRUCT, "LEDGER_ACCOUNT_TREE_NAMES.json")

# ★2026-08-23 実測(3seed × 4形)=★★字数の縛り「10〜15文字」が 発散の 原因。
#   ★字数あり= 6144(空) / 3545 / 6144(空)  ← 2/3 落ちる
#   ★字数なし=  444 /  552 /  627          ← 3/3 通る(★13分の1)
#   ★英語だけ= 1641 / 2170 / 1641          ← 3/3 通る・3seed 完全一致
#   ★英語と日本語を 1回で 出させると 3176〜3634 で ★時々 落ちる。
#   ★∴ ①字数の縛りを 外す ②英語で 決めてから 日本語にする(★2問に 割る)。
#   ★外れた 予想も 残す=★『翻訳は 分類より 狭いから 終わる』は ★誤り。
#     ★字数を 付けたまま 翻訳に 割ると 9回中 7回 空だった。★効いたのは 割った ことでは なく ★字数を 外した こと。

PROMPT_EN = """\
段1. これから、同じ分類に入った依頼の代表例を見せます。
段2. その代表例に共通する主題を1つ見つけてください。
段3. その主題を表すカテゴリ名を、英語の名詞句(2〜4語・Title Case)で1つ書いてください。
     代表例が細かい断片の場合は、それらが共通して扱っている作業の種類を名前にしてください。
     名前のみを1行で出力してください。

例)
代表例:
- 一時workspaceにJSONLファイルを読み込み、総レコード数と不正行数をJSON出力するCLIツールを作成
- JSONLの不正行を数える純関数を作成。標準ライブラリのみ。
出力:
JSONL Parsing Utilities

では本番です。
代表例:
"""

PROMPT_JA = """\
次の英語のカテゴリ名を、短い日本語のカテゴリ名にしてください。名前のみを1行で出力してください。

例) 英語: JSONL Parsing Utilities → JSONL解析ツール
例) 英語: Progress Record Intake → 進捗記録の投函

英語: %s"""


def _names_mod():
    """★既存の 合議部品を 呼ぶだけ(★自作しない)。"""
    sys.path.insert(0, STRUCT)
    sp = importlib.util.spec_from_file_location("_names", os.path.join(STRUCT, "s_account_axis_names.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _memo_map():
    """★台帳は直読しない=rri の公開関数から 引く。"""
    sys.path.insert(0, "/home/takasan/rri")
    from rri import request_thread as RT
    return {str(r.get("question_id")): " ".join(str(r.get("memo") or "").split())
            for r in RT.list_account_proposals()}


def _candidates():
    return json.load(open(IN_CAND, encoding="utf-8"))["axes"]


# ★2026-08-23 実測=★seed1 が finish=length で 空返し。★原因は 予算では なく ★依頼文の 汚れ。
#   ★実物で 数えた 汚れ= ①同じ定型句の 繰り返し(1行に 2〜3回) ②`<<<2DER:...>>>` の 目印
#   ③`DE-0484 / DE-0457 / …` の ID 羅列(★意味0・token だけ 食う) ④先頭の 連番。
#   ★∴ MAX_TOKENS は 上げず、★決定論で 落とす。
_NOISE = (
    "（前回の契約はここに在りましたが、新しく書くために外しました）",
    "(前回の契約はここに在りましたが、新しく書くために外しました)",
)
_MARK_RE = re.compile(r"<<<[^>]*>>>")
_IDLIST_RE = re.compile(r"(前提の\s*出所[^:：]*[:：]\s*)?((DE|RREQ|RINT|ITEM|TASK)-[0-9A-Za-z_-]+\s*/\s*){2,}"
                        r"(DE|RREQ|RINT|ITEM|TASK)-[0-9A-Za-z_-]+")
_ENUM_RE = re.compile(r"^\s*\d+\s*[.)、]\s*")


def _clean(txt):
    """★依頼文を 決定論で 掃除する(★意味の 要点だけ 残す)。"""
    s = txt or ""
    for n in _NOISE:
        s = s.replace(n, " ")
    s = _MARK_RE.sub(" ", s)
    s = _IDLIST_RE.sub(" ", s)
    s = _ENUM_RE.sub("", s)
    return " ".join(s.split())[:CLIP]


def _build_prompt(sample_ids, memo, limit):
    """★代表例を 掃除→重複除去→上位 limit 件(★決定論)。"""
    seen, distinct = set(), []
    for qid in sample_ids:
        c = _clean(memo.get(qid))
        if c and c not in seen:
            seen.add(c)
            distinct.append(c)
    return PROMPT_EN + "\n".join("- %s" % d for d in distinct[:limit]) + "\n出力:\n"


def _first_name(text):
    """★返りから 名前を 1つ 取り出す(★最初の 中身の 在る 行・飾りを 落とす)。"""
    for line in (text or "").splitlines():
        s = line.strip().lstrip("-*・# ").strip().strip('"“”「」')
        if s:
            return s
    return None


def _llm(prompt, seed):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": TEMPERATURE,
                       "max_tokens": MAX_TOKENS}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    content = ch["message"].get("content")
    if not content:
        raise RuntimeError("LLM returned empty content (finish=%s, seed=%d)" % (ch.get("finish_reason"), seed))
    return content.strip()


def _llm_try(prompt, seed, attempts=3):
    """★空返し(finish=length)は ★同じ 依頼文でも 起きたり 起きなかったり する(★実測 2026-08-23)。
    ★∴ 同じ 依頼文で 数回 やり直し、★それでも 出なければ ★None を 返す(★全体を 落とさない)。
    ★何回 空だったかは ★呼び手が 記録に 残す(★黙って 減らさない)。"""
    empties = 0
    for _ in range(attempts):
        try:
            return _llm(prompt, seed), empties
        except RuntimeError as e:
            if "empty content" not in str(e):
                raise
            empties += 1
    return None, empties


def _consensus_latin(N, proposals):
    """★英語の 合議。★既存 `consensus()` を そのまま 使い、★連結の 時だけ 空白で 繋ぎ直す。
    ★理由=既存の 連結は 日本語向けで 空白を 入れない=`Contract`+`Design`→`ContractDesign` になる。
    ★既存部品は 1文字も 変えない(★v2 の --check が 掛かっている)。"""
    con = _consensus(N, proposals)
    if con["name_status"] == "CONSENSUS_CONSOLIDATED" and con.get("consolidated_tokens"):
        con = dict(con, name=" ".join(t["token"] for t in con["consolidated_tokens"]))
    return con


def _consensus(N, proposals):
    """★提案が 0件の 時は 不成立として 返す(★既存 `consensus()` は 空辞書で 落ちる=実測 2026-08-23)。
    ★0件=★名前が 1つも 取れなかった=★推測で 埋めない。"""
    if not proposals:
        return {"name": None, "name_status": "UNRESOLVED_NO_CONSENSUS",
                "agreement_count": 0, "consolidated_tokens": None}
    return N.consensus(proposals)


def _mkrow(N, ax, sample_ids, prop_en, prop_ja, raw):
    con_en, con_ja = _consensus_latin(N, prop_en), _consensus(N, prop_ja)
    return {
        "axis_id": ax["axis_id"], "axes_version": "ledger-v1",
        "name_en": con_en["name"], "name_en_status": con_en["name_status"],
        "name_en_agreement": con_en["agreement_count"],
        "name": con_ja["name"], "name_status": con_ja["name_status"],
        "agreement_count": con_ja["agreement_count"],
        "consolidated_tokens": con_ja["consolidated_tokens"],
        "n_members": len(ax.get("members") or []),
        "model": MODEL, "endpoint": ":8005", "seeds": list(SEEDS),
        "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
        "proposals_en": prop_en, "proposals": prop_ja, "raw_replies": raw,
        "sample_element_ids": sample_ids, "prompt_id": PROMPT_ID, "sampled_k": len(sample_ids),
    }


def _name_one(N, memo, ax):
    """★軸 1本を 命名する(★ここは 直列=英語が 決まってから 日本語を 引く ため)。
    ★軸と軸の 間は 呼び手が 並列に する。"""
    if True:
        sample_ids = ax.get("sample_question_ids") or ax.get("members", [])[:12]
        prop_en, prop_ja, raw, shrinks, empty = {}, {}, {}, {}, {}
        for s in SEEDS:
            # ★問1=英語(★代表例から 主題を 決める)。
            # ★予算を 使い切った 時は ★予算を 上げず ★代表例を 決定論で 減らす(★8→5→3)。
            txt, n_empty = None, 0
            for limit in (8, 5, 3):
                txt, e = _llm_try(_build_prompt(sample_ids, memo, limit), s)
                n_empty += e
                if txt:
                    shrinks[str(s)] = limit
                    break
            empty[str(s) + "-en"] = n_empty
            if txt is None:
                continue                       # ★この seed は 名前を 出せなかった=★記録に 残して 先へ 進む
            en = _first_name(txt)
            raw[str(s) + "-en"] = txt[-300:]
            if en:
                prop_en[str(s)] = en
        # ★問2=日本語。★★合議で 決まった 英語 1つ から 引く(★seed ごとの 英語からでは ない)。
        #   ★実測 2026-08-23=★英語が 完全一致した 軸は 日本語も 完全一致し、
        #     ★英語が 割れた 軸は 日本語も 割れて 不成立に なった。
        #   ★∴ 入力を 1つに 揃えてから 引く。
        #   ★併せて=★日本語の 合議は 漢字の 連続を 1トークンと 数えるため
        #     『契約機能設計/契約設計仕様/契約管理』の ような 組は 重なりを 拾えない。
        #     ★入力を 揃える ことで この 型に 落ちにくく する。
        base_en = _consensus_latin(N, prop_en)["name"]
        if base_en:
            for s in SEEDS:
                jtxt, e = _llm_try(PROMPT_JA % base_en, s)
                empty[str(s) + "-ja"] = e
                if jtxt is None:
                    continue
                ja = _first_name(jtxt)
                raw[str(s) + "-ja"] = jtxt[-300:]
                if ja:
                    prop_ja[str(s)] = ja
        row = _mkrow(N, ax, sample_ids, prop_en, prop_ja, raw)
        row["name_ja_derived_from_en"] = base_en
        row["examples_used_per_seed"] = shrinks
        row["empty_returns_per_call"] = empty       # ★何回 空だったか(★黙って 減らさない)
        for k in ("level", "parent"):               # ★2層(カテゴリ→詳細)の 時だけ 付く
            if k in ax:
                row[k] = ax[k]
        return row


def build(entries=None):
    """★軸と軸の 間を ★並列に する(★Taka 許可 2026-08-23『30並列でも回せる。20くらいでもかまわん』)。
    ★1本の 中は 直列の まま=★英語が 決まってから 日本語を 引く 順序を 崩さない。"""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    N = _names_mod()
    memo = _memo_map()
    items = list(entries if entries is not None else _candidates())
    lock, done = threading.Lock(), [0]

    def work(ax):
        r = _name_one(N, memo, ax)
        with lock:
            done[0] += 1
            print("  [%3d/%d] %s n=%-5d EN=%r [%s] JA=%r"
                  % (done[0], len(items), r["axis_id"], r["n_members"], r["name_en"],
                     r["name_en_status"], r["name"]), flush=True)
        return r

    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        rows = list(ex.map(work, items))
    rows.sort(key=lambda r: (r.get("level", 0), r["axis_id"]))
    return rows


def _ser(rows):
    doc = {"_meta": "LEDGER_ACCOUNT_AXIS_NAMES — 台帳の明細から出した軸の命名(英語=正/日本語=併記)。"
                    "id が正典・name は装飾。合議は s_account_axis_names.consensus を EN/JA 別々に適用。"
                    "未成立=UNRESOLVED_NO_CONSENSUS(捏造ゼロ)。★台帳ではない=毎回まるごと作り直す控え。",
           "model": MODEL, "endpoint": ":8005", "prompt_id": PROMPT_ID, "seeds": list(SEEDS),
           "names": rows}
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def check(entries=None):
    if not os.path.isfile(OUT):
        print("LEDGER_ACCOUNT_AXIS_NAMES --check: RED\n  NOT_GENERATED")
        return 1
    N = _names_mod()
    rows = json.load(open(OUT, encoding="utf-8"))["names"]
    cand_ids = {c["axis_id"] for c in (entries if entries is not None else _candidates())}
    red = []
    if {r["axis_id"] for r in rows} != cand_ids:
        red.append("SCOPE_MISMATCH: 命名対象が候補軸集合と不一致")
    for r in rows:
        # ★英語は 空白で 繋ぐ方(`_consensus_latin`)で 判定する=★build と 同じ 関数を 使う。
        #   ★2026-08-23=★ここで `consensus()` を 呼んでいて ★検査だけが 落ちた(★私の 作りの 誤り)。
        for key, pk, sk, fn in (("name_en", "proposals_en", "name_en_status",
                                 lambda p: _consensus_latin(N, p)),
                                ("name", "proposals", "name_status", lambda p: _consensus(N, p))):
            con = fn(r[pk])
            if (r[key], r[sk]) != (con["name"], con["name_status"]):
                red.append("CONSENSUS_MISAPPLIED: %s の %s" % (r["axis_id"], key))
            if r[sk] == "UNRESOLVED_NO_CONSENSUS" and r[key] is not None:
                red.append("UNRESOLVED_NOT_NULL: %s の %s" % (r["axis_id"], key))
    if red:
        print("LEDGER_ACCOUNT_AXIS_NAMES --check: RED")
        for m in red:
            print("  " + m)
        return 1
    ok = [r for r in rows if str(r["name_en_status"]).startswith("CONSENSUS_")]
    print("LEDGER_ACCOUNT_AXIS_NAMES --check: GREEN (合議再判定一致; 英語命名成立 %d/%d)" % (len(ok), len(rows)))
    for r in rows:
        print("  %s -> EN=%s / JA=%s" % (r["axis_id"], r["name_en"], r["name"]))
    return 0


def _tree_entries():
    d = json.load(open(TREE_IN, encoding="utf-8"))
    return d["categories"] + d["details"]


def main(argv):
    # ★--tree=★2層(カテゴリ→詳細)を 命名する。★入口も 出口も 別ファイル(★1層の 結果を 壊さない)。
    if "--tree" in argv:
        global OUT
        OUT = TREE_OUT
        entries = _tree_entries()
        if "--check" in argv:
            return check(entries)
        rows = build(entries)
        open(OUT, "w", encoding="utf-8").write(_ser(rows))
        n_en = sum(1 for r in rows if str(r["name_en_status"]).startswith("CONSENSUS_"))
        n_ja = sum(1 for r in rows if str(r["name_status"]).startswith("CONSENSUS_"))
        print("[build --tree] 軸=%d(カテゴリ%d/詳細%d) 英語成立=%d 日本語成立=%d"
              % (len(rows), sum(1 for r in rows if r.get("level") == 1),
                 sum(1 for r in rows if r.get("level") == 2), n_en, n_ja))
        return 0
    if "--check" in argv:
        return check()
    rows = build()
    open(OUT, "w", encoding="utf-8").write(_ser(rows))
    print("[build] 軸=%d 英語成立=%d 日本語成立=%d"
          % (len(rows),
             sum(1 for r in rows if str(r["name_en_status"]).startswith("CONSENSUS_")),
             sum(1 for r in rows if str(r["name_status"]).startswith("CONSENSUS_"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
