#!/usr/bin/env python3
"""s_intent_probe_armc3 — 意図調べ arm-C3: 汚染ゲート / held-out 例文 / 理由一級市民 / 二階建て評価。

arm-C2 の 0.88 は 8 fixture 中 7 個が正解付きで例文に混入(汚染)＝記憶の測定だった(再監査 FINDING §1)。
本器は是正版:
- **汚染を機械ゲートに**(--check の CONTAMINATION 検査。fixture 文の 5 文字以上が例文に出たら RED。negative control で実証)。
- **held-out 例文**(fixture と素性の異なる例)。**A/B 並び順 正/逆 両方**で position bias を数値化。
- **理由(reason)を必須**(根拠なき claim を弾く=EGL 中核と同型)。think OFF 固定(精度寄与ゼロ・15倍コスト測定済)。
- **applicable フラグ**(その二択が確定ツリー経路で実参照されたか)。精度は applicable 行で。
- **二階建て**: 一階=label_agreement(seed 平均・**"正解率"でなく regression detector**)。二階=DISAGREEMENTS を材料として出す
  (別解/誤り/空回りの判定は IMPL でなく DESIGN propose→Taka 承認。fixture の acceptable_strategies に後で書き戻す器を用意)。

metric は seed 平均で arm-C(0.5833)/C2(0.8333)と統一。measure-first: 汚染除去で下がるのが正常・隠さない。
record-occurrence: LLM 出力記録・--check は LLM 非再実行で決定論再適用。

usage:  s_intent_probe_armc3.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
import unicodedata
from collections import Counter

import s_intent_probe_proto as P

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_PROBE_ARMC3.jsonl")
MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
MAX_TOKENS = 160
ENABLE_THINKING = False   # 固定(再測不要=FINDING §3)
PROMPT_ID = "armc3-heldout-reasons-v1"
MAX_PARALLEL = 16
REASON_MAX = 40

# ── fixtures(各戦略≥3・21件)。acceptable_strategies は二階承認の書き戻し器(今は空)。──────────
def _fx(i, req, strat, ctx="", acc=None):
    return {"id": i, "request": req, "context": ctx, "expected_strategy": strat,
            "acceptable_strategies": acc or []}


FIXTURES = [
    _fx("D1", "Windows 10 の一般提供開始日は？", "DIRECT"),
    _fx("D2", "1024 は 2 の何乗ですか？", "DIRECT"),
    _fx("D3", "1 マイルは何キロメートル？", "DIRECT"),
    _fx("CR1", "プーチンの今後の動向は？", "CONTEXT_RESOLVE", ctx="直前の会話はロシア・ウクライナ戦争の軍事・経済損失の分析が支配的。"),
    _fx("CR2", "彼の評価はどう？", "CONTEXT_RESOLVE", ctx="直前は、ある先発投手の今季成績と防御率の議論が続いている。"),
    _fx("CR3", "次のリリースはいつ？", "CONTEXT_RESOLVE", ctx="直前は、ある OSS ライブラリの開発ロードマップの話をしていた。"),
    _fx("CH1", "どのデータベースを採用すべき？", "CHOICE"),
    _fx("CH2", "週末はどこへ行こう？", "CHOICE"),
    _fx("CH3", "プーチンの今後は？", "CHOICE"),   # CR1 と対(文脈の有無で切替を見る)
    _fx("BV1", "白樺の木材としての価値は？", "BOUNDED_MULTI_VIEW"),
    _fx("BV2", "リモートワーク導入の是非は？", "BOUNDED_MULTI_VIEW"),
    _fx("BV3", "この設計案の得失は？", "BOUNDED_MULTI_VIEW"),
    _fx("IP1", "あれ、どこにあったっけ？", "INTENT_PROBE"),
    _fx("IP2", "それ、その後どうなった？", "INTENT_PROBE"),
    _fx("IP3", "例のやつ、進んでる？", "INTENT_PROBE"),
    _fx("PP1", "以前作った Watcher 仕様ってどこ？", "PREMISE_PROBE"),
    _fx("PP2", "先週決めた方針のメモある？", "PREMISE_PROBE"),
    _fx("PP3", "君が言ってた予備の鍵はどこ？", "PREMISE_PROBE"),
    _fx("DF1", "asdf ;; // @@@", "DEFER"),
    _fx("DF2", "。。。！？！？", "DEFER"),
    _fx("DF3", "   \t   ", "DEFER"),
]

# ── 二択(canonical A=第1意味/B=第2意味)。例文は held-out(意味ベース・letter に依存しない)。──────────
BINARIES = [
    {"id": "b_malformed", "q": "この依頼は次のどちらか。",
     "A": "意味の通る依頼", "B": "記号の羅列等で解釈不能な不正形",
     "def": "", "ex": "例:「今日は何曜日?」→意味が通る /「zxcv!!!!」→不正形。"},
    {"id": "b_needs_probe", "q": "この依頼は次のどちらか。",
     "A": "そのまま解釈して回答/調査を始められる", "B": "始める前に一度確認(聞き返し)が要る",
     "def": "対象と意図が十分特定できていれば始められる。指示語で対象不明・前提が怪しい等なら聞き返しが要る。",
     "ex": "例:「地球の半径は?」→始められる /「あっち持ってって」→聞き返しが要る。"},
    {"id": "b_probe_type", "q": "確認が要るとして、不確かなのは次のどちらか。",
     "A": "対象が何を指すか自体が不明(INTENT)", "B": "対象は名指しできるが、前提した事実/存在が確認せず信じられない(PREMISE)",
     "def": "INTENT=指示語などで対象自体が曖昧。PREMISE=対象は特定できるが、その存在/成立が怪しい。",
     "ex": "例:「これ誰の?」→対象不明(INTENT) /「昨日の会議の議事録ある?」→議事録の存在が前提(PREMISE)。"},
    {"id": "b_determinacy", "q": "この依頼の合理的な回答は次のどちらか。",
     "A": "概ね1つに絞れる", "B": "絞れず複数ありうる",
     "def": "", "ex": "例:「水の沸点は?」→1つに絞れる /「教育の理想像は?」→複数ありうる。"},
    {"id": "b_context", "q": "直前の文脈を踏まえると次のどちらか。",
     "A": "支配的な解釈があり文脈で絞れる", "B": "文脈でも絞れない",
     "def": "", "ex": "例: 直前がある技術討論で「その結論は?」→文脈で絞れる / 文脈なしで「どう思う?」→絞れない。"},
    {"id": "b_multi_type", "q": "複数ありうるとして、次のどちらか。",
     "A": "一つ選ばせる有限選択肢型(CHOICE)", "B": "複数観点を比較提示する型(BMV)",
     "def": "CHOICE=主要 branch が有限でユーザは一つを選びたい。BMV=複数観点を比較して見せること自体が答え。",
     "ex": "例:「昼は寿司/カレー/パスタどれ?」→有限選択肢(CHOICE) /「原発の是非は?」→観点比較(BMV)。"},
]
BINMAP = {b["id"]: b for b in BINARIES}
# 弱2二択の expected(的中率評価用・canonical A/B)
EXPECTED_BINARY = {"IP1": {"b_probe_type": "A"}, "IP2": {"b_probe_type": "A"}, "IP3": {"b_probe_type": "A"},
                   "PP1": {"b_probe_type": "B"}, "PP2": {"b_probe_type": "B"}, "PP3": {"b_probe_type": "B"},
                   "CH1": {"b_multi_type": "A"}, "CH2": {"b_multi_type": "A"},
                   "BV1": {"b_multi_type": "B"}, "BV2": {"b_multi_type": "B"}, "BV3": {"b_multi_type": "B"}}


def _prompt(b, fx, order):
    a, bb = (b["A"], b["B"]) if order == "fwd" else (b["B"], b["A"])
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    body = "依頼:「%s」%s\n%s %s A) %s / B) %s。%s" % (fx["request"], ctx, b["q"], b["def"], a, bb, b["ex"])
    return body + '\n出力は JSON のみ: {"choice":"A" または "B" または "unsure","reason":"なぜそう判断したか1文40字以内"}'


def _canon(order, raw_choice):
    """順序を canonical(A=b['A'])へ正規化。fwd はそのまま・rev は A↔B 反転。unsure/None は不変。"""
    if raw_choice not in ("A", "B"):
        return raw_choice
    if order == "fwd":
        return raw_choice
    return "B" if raw_choice == "A" else "A"


def parse_binary(raw, finish_reason):
    """(choice_raw∈{A,B,unsure} or None, reason or None, verdict)。理由欠落=DIVERGE_NO_REASON。"""
    if finish_reason == "length":
        return None, None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, None, "DIVERGE_SCHEMA"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None, None, "DIVERGE_SCHEMA"
    c = d.get("choice")
    if c not in ("A", "B", "unsure"):
        return None, None, "DIVERGE_SCHEMA"
    reason = (d.get("reason") or "").strip()
    if not reason:
        return c, None, "DIVERGE_NO_REASON"
    return c, reason, "OK"


# ── 決定論集計ツリー + applicable 追跡(canonical 値)────────────────────────────
def _tree(get):
    """get(bid)->canonical A/B/None。返り (strategy, consulted set)。"""
    consulted = []

    def g(k):
        consulted.append(k)
        v = get(k)
        return v if v in ("A", "B") else None
    if g("b_malformed") is None:
        return "UNRESOLVED_AGG", consulted
    if get("b_malformed") == "B":
        return "DEFER", consulted
    if g("b_needs_probe") is None:
        return "UNRESOLVED_AGG", consulted
    if get("b_needs_probe") == "B":
        if g("b_probe_type") is None:
            return "UNRESOLVED_AGG", consulted
        return ("INTENT_PROBE" if get("b_probe_type") == "A" else "PREMISE_PROBE"), consulted
    if g("b_determinacy") is None:
        return "UNRESOLVED_AGG", consulted
    if get("b_determinacy") == "A":
        return "DIRECT", consulted
    if g("b_context") is None:
        return "UNRESOLVED_AGG", consulted
    if get("b_context") == "A":
        return "CONTEXT_RESOLVE", consulted
    if g("b_multi_type") is None:
        return "UNRESOLVED_AGG", consulted
    return ("CHOICE" if get("b_multi_type") == "A" else "BOUNDED_MULTI_VIEW"), consulted


def _majority(vals):
    c = Counter(v for v in vals if v is not None)
    if not c:
        return None
    top, n = c.most_common(1)[0]
    return top if n > len(vals) / 2 else "unsure"


# ── 汚染ゲート(--check の中核)────────────────────────────────────────────────
EXCLUDE_WORDS = []   # 固有名詞単独一致の誤検知が出たら明示的にここへ(記録・黙って緩めない)


def _norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"[\s、。・「」『』（）()\[\]【】,.!?！？:：;；/／]", "", s)


def contamination_violations():
    """fixture request の連続5文字以上が binary の prompt template に出現→違反 list。"""
    tmpl = _norm(" ".join(b["q"] + b["def"] + b["A"] + b["B"] + b["ex"] for b in BINARIES))
    viol = []
    for fx in FIXTURES:
        req = _norm(fx["request"])
        for i in range(len(req) - 4):
            frag = req[i:i + 5]
            if frag in EXCLUDE_WORDS:
                continue
            if frag and frag in tmpl:
                viol.append({"fixture_id": fx["id"], "fragment": frag})
                break
    return viol


def run():
    import time as _t
    tasks = [(fx, b, order, s) for fx in FIXTURES for b in BINARIES for order in ("fwd", "rev") for s in SEEDS]

    def _one(t):
        fx, b, order, s = t
        raw, fr, ct = _llm(_prompt(b, fx, order), s)
        craw, reason, verdict = parse_binary(raw, fr)
        return {"fixture_id": fx["id"], "binary_id": b["id"], "order": order, "seed": s,
                "raw_output": raw, "finish_reason": fr, "completion_tokens": ct,
                "choice_raw": craw, "choice": _canon(order, craw), "reason": reason, "parse_verdict": verdict}
    t0 = _t.time()
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        rows = list(ex.map(_one, tasks))
    wall = round(_t.time() - t0, 2)
    rows.sort(key=lambda r: (r["fixture_id"], r["binary_id"], r["order"], r["seed"]))
    return rows, wall


def _llm(prompt, seed):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": 0.7, "max_tokens": MAX_TOKENS,
                       "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason"), out.get("usage", {}).get("completion_tokens")


def _choice(rows, fid, bid, order, seed):
    for r in rows:
        if r["fixture_id"] == fid and r["binary_id"] == bid and r["order"] == order and r["seed"] == seed:
            return r["choice"]
    return None


def aggregate(rows):
    # 一階: label_agreement(seed 平均・fwd 順序で・"正解率でなく regression detector")
    hit = tot = 0
    consulted_map = {}
    disagreements = []
    for fx in FIXTURES:
        for s in SEEDS:
            got, consulted = _tree(lambda bid: _choice(rows, fx["id"], bid, "fwd", s))
            consulted_map[(fx["id"], s)] = set(consulted)
            tot += 1
            ok = got == fx["expected_strategy"] or got in fx["acceptable_strategies"]
            hit += int(ok)
            if not ok:
                reasons = {r["binary_id"]: r["reason"] for r in rows
                           if r["fixture_id"] == fx["id"] and r["order"] == "fwd" and r["seed"] == s}
                disagreements.append({"fixture_id": fx["id"], "seed": s, "got": got,
                                      "expected": fx["expected_strategy"], "reasons": reasons})
    # position bias: (fixture,binary,seed) の fwd canonical と rev canonical の一致率
    pb_tot = pb_agree = 0
    for fx in FIXTURES:
        for b in BINARIES:
            for s in SEEDS:
                f, r = _choice(rows, fx["id"], b["id"], "fwd", s), _choice(rows, fx["id"], b["id"], "rev", s)
                if f is not None and r is not None:
                    pb_tot += 1
                    pb_agree += int(f == r)
    # 弱2二択的中(多数決・fwd)
    weak_tot = weak_hit = 0
    for fid, exp in EXPECTED_BINARY.items():
        for bid, ev in exp.items():
            vals = [r["choice"] for r in rows if r["fixture_id"] == fid and r["binary_id"] == bid and r["order"] == "fwd"]
            weak_tot += 1
            weak_hit += int(_majority(vals) == ev)
    # applicable 率 / reason 欠落 / 40字超過 / seed一貫
    applic = sum(1 for r in rows if r["binary_id"] in consulted_map.get((r["fixture_id"], r["seed"]), set()) and r["order"] == "fwd")
    applic_tot = sum(1 for r in rows if r["order"] == "fwd")
    no_reason = sum(1 for r in rows if r["parse_verdict"] == "DIVERGE_NO_REASON")
    over40 = sum(1 for r in rows if r["reason"] and len(r["reason"]) > REASON_MAX)
    seedcons = {}
    for fx in FIXTURES:
        sset = set()
        for s in SEEDS:
            g, _ = _tree(lambda bid: _choice(rows, fx["id"], bid, "fwd", s))
            sset.add(g)
        seedcons[fx["id"]] = len(sset) == 1
    return {
        "label_agreement_seedavg": round(hit / tot, 4) if tot else None,
        "label_agreement_raw": "%d/%d" % (hit, tot),
        "seed_consistent_fixtures": "%d/%d" % (sum(seedcons.values()), len(seedcons)),
        "position_bias_agreement": round(pb_agree / pb_tot, 4) if pb_tot else None,
        "weak2_binary_accuracy": "%d/%d" % (weak_hit, weak_tot),
        "applicable_rate": "%d/%d" % (applic, applic_tot),
        "diverge_rate": round(sum(1 for r in rows if r["parse_verdict"] != "OK") / len(rows), 4) if rows else 0.0,
        "no_reason_n": no_reason, "reason_over40_n": over40,
        "n_disagreements": len(disagreements),
        "diverge_kinds": dict(Counter(r["parse_verdict"] for r in rows if r["parse_verdict"] != "OK")),
    }, disagreements


def _ser(rows, wall, agg, disagreements):
    hdr = {"_meta": "INTENT_PROBE_ARMC3(汚染ゲート/held-out例/理由必須/二階建て/seed平均metric)。弁別は決定論集計・LLMは二択+理由のみ。",
           "arm": "C3", "aggregate": agg, "wall_seconds": wall, "model": MODEL, "prompt_id": PROMPT_ID,
           "enable_thinking": ENABLE_THINKING, "orders": ["fwd", "rev"], "seeds": list(SEEDS),
           "binaries": [b["id"] for b in BINARIES], "n_fixtures": len(FIXTURES),
           "exclude_words": EXCLUDE_WORDS, "reason_max": REASON_MAX,
           "note": "label_agreement は正解率でなく regression detector。数字は能力主張でない(単一fixture・非決定論)。"}
    lines = [json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps({"row": "binary", **r}, sort_keys=True, ensure_ascii=False) for r in rows]
    lines += [json.dumps({"row": "disagreement", **d}, sort_keys=True, ensure_ascii=False) for d in disagreements]
    return "\n".join(lines) + "\n"


def _report(agg):
    a = agg
    print("  label_agreement(seed平均)=%s [%s] seed一貫=%s | position_bias一致=%s | 弱2二択=%s | applicable=%s"
          % (a["label_agreement_seedavg"], a["label_agreement_raw"], a["seed_consistent_fixtures"],
             a["position_bias_agreement"], a["weak2_binary_accuracy"], a["applicable_rate"]))
    print("  発散=%.2f%s no_reason=%d reason>40字=%d DISAGREEMENTS=%d"
          % (a["diverge_rate"], a["diverge_kinds"] or "", a["no_reason_n"], a["reason_over40_n"], a["n_disagreements"]))


def check():
    red = []
    # ★汚染ゲート(本器の中核): fixture 文が例文に混入していないか
    viol = contamination_violations()
    if viol:
        red.append("CONTAMINATION: fixture 文が例文に混入 %s" % viol[:8])
    # negative control: わざと fixture 文を例文へ入れたら検出できることを実証(検査が効いている証明)
    _saved = BINARIES[0]["ex"]
    try:
        BINARIES[0]["ex"] = _saved + FIXTURES[0]["request"]   # D1 を b_malformed 例文に注入
        if not contamination_violations():
            red.append("CONTAMINATION_GATE_DEAD: 注入した fixture 文を検出できない(negative control 失敗)")
    finally:
        BINARIES[0]["ex"] = _saved
    if not os.path.isfile(OUT):
        red.append("NOT_GENERATED: 先に main(:8005)")
        print("INTENT_PROBE_ARMC3 --check: RED")
        for m in red:
            print("  " + m)
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    rows = [l for l in lines[1:] if l.get("row") == "binary"]
    # 決定論再適用: 記録 raw→parser→canonical→集計が header と一致(LLM 非再実行)
    for r in rows:
        c, reason, v = parse_binary(r["raw_output"], r["finish_reason"])
        if (c, _canon(r["order"], c), reason, v) != (r["choice_raw"], r["choice"], r["reason"], r["parse_verdict"]):
            red.append("PARSE_NONDET[%s/%s/%s/s%d]" % (r["fixture_id"], r["binary_id"], r["order"], r["seed"]))
    re_agg, _dis = aggregate(rows)
    if re_agg != header.get("aggregate"):
        red.append("AGGREGATE_NONDET (parser/canonical/tree/多数決 再適用が記録と不一致)")
    if red:
        print("INTENT_PROBE_ARMC3 --check: RED")
        for m in red[:12]:
            print("  " + m)
        return 1
    print("INTENT_PROBE_ARMC3 --check: GREEN (汚染ゲート健全[negative control 実証]; 決定論再現; provenance 完全)")
    _report(header["aggregate"])
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    v = contamination_violations()
    if v:
        print("INTENT_PROBE_ARMC3: ABORT — 例文に fixture 文が混入(汚染) %s。held-out に直せ。" % v[:8])
        return 3
    if not P._infra_ok():
        print("INTENT_PROBE_ARMC3: NO_INFRA — :8005 で実推論が返らない")
        return 2
    rows, wall = run()
    agg, disagreements = aggregate(rows)
    open(OUT, "w", encoding="utf-8").write(_ser(rows, wall, agg, disagreements))
    n = len(FIXTURES) * len(BINARIES) * 2 * len(SEEDS)
    print("Arm C3 実測: %d 呼出(%d fixture×%d binary×2順序×%d seed) 並列=%d wall=%.1fs think=OFF"
          % (len(rows), len(FIXTURES), len(BINARIES), len(SEEDS), MAX_PARALLEL, wall))
    _report(agg)
    print("  ※ metric=seed平均で arm-C(0.5833)/C2(0.8333)と同一物差し。汚染除去で下がるのが正常(measure-first)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
