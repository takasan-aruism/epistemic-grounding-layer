#!/usr/bin/env python3
"""s_intent_probe_proto — 意図調べ(GAP-RRI-5)の最小プロトタイプ + Qwen 実測(measure-first)。

RRI spec §7(4軸)→§9(7戦略)。**メニュー/出力schema/fixture/集計は決定論固定・判断のみ Qwen(:8005)**。
Taka 仮説「良いメニューなら Qwen3.6 級でも矛盾しない選択をする」を measure-first で検証(gate 緩和でなく能力測定)。

発散対策(必須・[[llm-prompt-hygiene-not-budget]] / standing rule): thinking OFF(enable_thinking=false)+ tight menu +
max_tokens 上限 + **finish_reason=length は「発散」扱い**(成功にしない・空出力から捏造しない)。enum/schema 逸脱は決定論
パーサが REJECT(=発散/逸脱の検出)。tight vs loose メニューで発散率を比較(=設計知見)。

record-occurrence: main が Qwen を実行し raw_output を記録。--check は LLM を再実行せず記録 raw_output に
決定論パーサ/集計を再適用して整合を検証(名前 stage と同型)。

usage:
  s_intent_probe_proto.py           # :8005 で fixture×seed×{tight,loose} を実測 → INTENT_PROBE_PROTO.jsonl
  s_intent_probe_proto.py --check    # 決定論(menu/schema/fixture/parser/集計)再現 + provenance 完全 + measure-first サマリ
"""
import json
import os
import re
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_PROBE_PROTO.jsonl")

MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
PROMPT_ID = "intent-probe-v1"
# 実行 config: (config_id, menu, enable_thinking, max_tokens)。
# 発散対策=thinking を切るでなく clean/tight prompt + 十分な budget で正常終端(MGR/Taka 是正)。
# tight_on の budget は thinking 自然終端(~3083 実測)に余裕をみる。真の runaway(budget 到達=length)のみ DIVERGE。
RUN_CONFIGS = [
    ("tight_off", "tight", False, 256),    # baseline(thinking OFF・小 budget)
    ("tight_on", "tight", True, 6144),     # 本命(thinking ON・十分 budget)
    ("loose_off", "loose", False, 256),    # 発散対照(緩い menu)
]

# ── 決定論メニュー(§7 4軸 enum / §9 7戦略)──────────────────────────────────
AXES = {
    "context_anchoring": ["HIGH", "MEDIUM", "LOW", "UNRESOLVED"],
    "answer_determinacy": ["DETERMINATE", "BOUNDED", "OPEN", "UNRESOLVED"],
    "intent_breadth": ["NARROW", "MULTI_AXIS", "UNDERCONSTRAINED", "UNRESOLVED"],
    "premise_stability": ["STABLE", "UNCERTAIN", "SUSPECT", "UNRESOLVED"],
}
STRATEGIES = ["DIRECT", "CONTEXT_RESOLVE", "CHOICE", "BOUNDED_MULTI_VIEW",
              "INTENT_PROBE", "PREMISE_PROBE", "DEFER"]

_MENU_TIGHT = (
    "あなたは依頼の「意図」を評価する分類器です。次の依頼を4軸で評価し戦略を1つ選び、JSON のみ出力(説明/思考不要)。\n\n"
    "【4軸(各 enum から1つ)】\n"
    "- context_anchoring: HIGH/MEDIUM/LOW/UNRESOLVED (文脈で意図がどれだけ固定されるか)\n"
    "- answer_determinacy: DETERMINATE/BOUNDED/OPEN/UNRESOLVED (合理的な回答空間の狭さ)\n"
    "- intent_breadth: NARROW/MULTI_AXIS/UNDERCONSTRAINED/UNRESOLVED (指し得る目的の広さ)\n"
    "- premise_stability: STABLE/UNCERTAIN/SUSPECT/UNRESOLVED (暗黙の前提の確からしさ)\n\n"
    "【戦略(1つ)】\n"
    "- DIRECT: 問い安定・回答空間狭い\n- CONTEXT_RESOLVE: 複数解釈可だが文脈に支配的解釈\n"
    "- CHOICE: 主要解釈が複数で安全に一つ選べない\n- BOUNDED_MULTI_VIEW: 複数の見方を短く比較が合理的\n"
    "- INTENT_PROBE: 意図が不明確・極小の確認質問で解釈改善\n- PREMISE_PROBE: 暗黙の前提が疑わしい・存在確認要\n"
    "- DEFER: 不正形/文脈不足/要明確化\n\n"
    '【出力(JSONのみ)】\n{"context_anchoring":"..","answer_determinacy":"..","intent_breadth":"..",'
    '"premise_stability":"..","strategy":"..","reason":"20字以内"}\n\n')

# loose = 冗長・非構造(発散率比較用の対照)。同じ情報だが tight でない。
_MENU_LOOSE = (
    "依頼の意図について色々考えてみてほしいんだけど、文脈にどれくらい依存してるかとか、答えがどれくらい決まってるかとか、"
    "目的がどれくらい広いかとか、前提がちゃんと成り立ってるかとか、そういうのを踏まえて、どういう対応方針がいいか考えて、"
    "できれば最後に何か構造化された形でまとめてくれると助かる。方針は直接答える/文脈で解決/選択肢出す/複数観点で比較する/"
    "意図を聞き返す/前提を確認する/保留する、みたいな中から。軸は context_anchoring(HIGH/MEDIUM/LOW/UNRESOLVED)、"
    "answer_determinacy(DETERMINATE/BOUNDED/OPEN/UNRESOLVED)、intent_breadth(NARROW/MULTI_AXIS/UNDERCONSTRAINED/UNRESOLVED)、"
    "premise_stability(STABLE/UNCERTAIN/SUSPECT/UNRESOLVED)。戦略は DIRECT/CONTEXT_RESOLVE/CHOICE/BOUNDED_MULTI_VIEW/"
    "INTENT_PROBE/PREMISE_PROBE/DEFER。JSON で出せたら出して。\n\n")

MENUS = {"tight": _MENU_TIGHT, "loose": _MENU_LOOSE}

# ── 決定論 fixture(固定・7戦略を網羅・expected は spec 例に基づく決定論ラベル)──────────
FIXTURES = [
    {"id": "F1_DIRECT", "request": "Windows 10 の一般提供開始日は？", "context": "",
     "expected_axes": {"answer_determinacy": "DETERMINATE"}, "expected_strategy": "DIRECT"},
    {"id": "F2_DIRECT", "request": "1024 は 2 の何乗ですか？", "context": "",
     "expected_axes": {"answer_determinacy": "DETERMINATE"}, "expected_strategy": "DIRECT"},
    {"id": "F3_CONTEXT", "request": "プーチンの今後の動向は？",
     "context": "直前の会話はロシア・ウクライナ戦争の軍事・経済損失の分析が支配的。",
     "expected_axes": {"context_anchoring": "HIGH", "answer_determinacy": "OPEN"}, "expected_strategy": "CONTEXT_RESOLVE"},
    {"id": "F4_CHOICE", "request": "プーチンの今後は？", "context": "",
     "expected_axes": {"context_anchoring": "LOW", "answer_determinacy": "OPEN"}, "expected_strategy": "CHOICE"},
    {"id": "F5_BMV", "request": "白樺の木材としての価値は？", "context": "",
     "expected_axes": {"answer_determinacy": "BOUNDED"}, "expected_strategy": "BOUNDED_MULTI_VIEW"},
    {"id": "F6_INTENT_PROBE", "request": "あれ、どこにあったっけ？", "context": "",
     "expected_axes": {"intent_breadth": "UNDERCONSTRAINED"}, "expected_strategy": "INTENT_PROBE"},
    {"id": "F7_PREMISE_PROBE", "request": "以前作った Watcher 仕様ってどこ？", "context": "",
     "expected_axes": {"premise_stability": "SUSPECT"}, "expected_strategy": "PREMISE_PROBE"},
    {"id": "F8_DEFER", "request": "asdf ;; // @@@", "context": "",
     "expected_axes": {}, "expected_strategy": "DEFER"},
]
PROBE_STRATS = {"INTENT_PROBE", "PREMISE_PROBE"}


def _build_prompt(menu_key, fx):
    p = MENUS[menu_key]
    ctx = ("直前文脈: %s\n" % fx["context"]) if fx["context"] else ""
    return p + "【依頼】\n" + ctx + "依頼: " + fx["request"]


# ── 決定論パーサ(enum/schema 逸脱=発散を REJECT)───────────────────────────────
def parse_output(raw, finish_reason):
    """raw_output → (parsed dict or None, verdict)。verdict∈{OK, DIVERGE_LENGTH, DIVERGE_NO_JSON, DIVERGE_SCHEMA, DIVERGE_ENUM}。"""
    if finish_reason == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, "DIVERGE_NO_JSON"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None, "DIVERGE_NO_JSON"
    keys = set(AXES) | {"strategy"}
    if not keys.issubset(d):
        return None, "DIVERGE_SCHEMA"
    for ax, allowed in AXES.items():
        if d[ax] not in allowed:
            return None, "DIVERGE_ENUM"
    if d["strategy"] not in STRATEGIES:
        return None, "DIVERGE_ENUM"
    return {k: d[k] for k in list(AXES) + ["strategy"]}, "OK"


def _llm(prompt, seed, enable_thinking, max_tokens, timeout=180):
    """:8005 Qwen。返り (content, finish_reason, completion_tokens)。budget 到達(length)は呼び手が DIVERGE 扱い。"""
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": 0.7, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": enable_thinking}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason"), out.get("usage", {}).get("completion_tokens")


def _infra_ok():
    try:
        _llm("ping。JSON {\"ok\":\"YES\"} のみ返答。", 0, False, 32)
        return True
    except Exception:
        return False


def run():
    """config×fixture×seed を実測 → 行 list(record-occurrence・raw_output 記録)。"""
    rows = []
    for cfg_id, menu_key, think, mt in RUN_CONFIGS:
        for fx in FIXTURES:
            prompt = _build_prompt(menu_key, fx)
            for s in SEEDS:
                raw, fr, ctoks = _llm(prompt, s, think, mt)
                parsed, verdict = parse_output(raw, fr)
                rows.append({
                    "config_id": cfg_id, "fixture_id": fx["id"], "menu": menu_key, "seed": s,
                    "model": MODEL, "endpoint": ":8005", "enable_thinking": think,
                    "max_tokens": mt, "completion_tokens": ctoks, "prompt_id": PROMPT_ID, "finish_reason": fr,
                    "raw_output": raw, "parsed": parsed, "parse_verdict": verdict,
                    "expected_strategy": fx["expected_strategy"], "expected_axes": fx["expected_axes"],
                })
    rows.sort(key=lambda r: (r["config_id"], r["fixture_id"], r["seed"]))
    return rows


# ── 決定論集計(measure-first の4指標)────────────────────────────────────────
def aggregate(rows):
    by_menu = {}
    for cfg_id, _menu, _think, _mt in RUN_CONFIGS:
        mrows = [r for r in rows if r["config_id"] == cfg_id]
        n = len(mrows)
        diverge = [r for r in mrows if r["parse_verdict"] != "OK"]
        ok = [r for r in mrows if r["parse_verdict"] == "OK"]
        # (a) 軸評価妥当性: expected_axes に指定された軸が一致した割合
        ax_tot = ax_hit = 0
        for r in ok:
            for ax, exp in r["expected_axes"].items():
                ax_tot += 1
                ax_hit += int(r["parsed"][ax] == exp)
        # (b) 戦略一致 + seed 間一貫性
        strat_hit = sum(1 for r in ok if r["parsed"]["strategy"] == r["expected_strategy"])
        seedcons = {}
        for r in ok:
            seedcons.setdefault(r["fixture_id"], set()).add(r["parsed"]["strategy"])
        consistent_fx = sum(1 for v in seedcons.values() if len(v) == 1)
        # (c) 聞き返し適切さ: PROBE 期待 fixture で PROBE を出した率 / PROBE 非期待で誤って出した率
        probe_exp = [r for r in ok if r["expected_strategy"] in PROBE_STRATS]
        probe_hit = sum(1 for r in probe_exp if r["parsed"]["strategy"] in PROBE_STRATS)
        nonprobe = [r for r in ok if r["expected_strategy"] not in PROBE_STRATS]
        false_probe = sum(1 for r in nonprobe if r["parsed"]["strategy"] in PROBE_STRATS)
        # (d) 発散率
        from collections import Counter
        ctoks = sorted(r["completion_tokens"] for r in mrows if r.get("completion_tokens") is not None)
        median_ctok = ctoks[len(ctoks) // 2] if ctoks else None
        by_menu[cfg_id] = {
            "n": n, "diverge_n": len(diverge), "diverge_rate": round(len(diverge) / n, 4) if n else 0.0,
            "diverge_kinds": dict(Counter(r["parse_verdict"] for r in diverge)),
            "axis_validity": round(ax_hit / ax_tot, 4) if ax_tot else None,
            "strategy_match": round(strat_hit / len(ok), 4) if ok else None,
            "seed_consistent_fixtures": "%d/%d" % (consistent_fx, len(seedcons)),
            "probe_recall": "%d/%d" % (probe_hit, len(probe_exp)),
            "false_probe": "%d/%d" % (false_probe, len(nonprobe)),
            "median_completion_tokens": median_ctok,
        }
    return by_menu


def _ser(rows, agg):
    hdr = {"_meta": "INTENT_PROBE_PROTO(GAP-RRI-5 measure-first)。メニュー/schema/fixture/parser/集計=決定論・判断のみ Qwen。"
                    "thinking OFF+max_tokens 上限、length/enum逸脱=発散。--check=記録 raw_output に決定論再適用。",
           "aggregate": agg, "model": MODEL, "prompt_id": PROMPT_ID, "seeds": list(SEEDS)}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows]) + "\n"


def check():
    if not os.path.isfile(OUT):
        print("INTENT_PROBE_PROTO --check: RED\n  NOT_GENERATED: 先に main を実行(:8005)")
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header, rows = lines[0], lines[1:]
    red = []
    # 決定論パーサ再適用: 記録 raw_output/finish_reason に parse_output を再適用 → parsed/verdict 一致(LLM 不使用)
    for r in rows:
        p, v = parse_output(r["raw_output"], r["finish_reason"])
        if (p, v) != (r["parsed"], r["parse_verdict"]):
            red.append("PARSE_NONDETERMINISTIC[%s/%s/s%d]: 記録=%s,%s 再適用=%s,%s"
                       % (r["menu"], r["fixture_id"], r["seed"], r["parsed"], r["parse_verdict"], p, v))
    # menu/enum/fixture が固定(byte 再現の核)
    if set(r["fixture_id"] for r in rows) != {f["id"] for f in FIXTURES}:
        red.append("FIXTURE_DRIFT: 記録 fixture が固定セットと不一致")
    # 集計再現: 記録 rows から aggregate 再計算 → header と一致
    if aggregate(rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDETERMINISTIC: 記録から集計が再現しない")
    # provenance 完全性
    for r in rows:
        for k in ("model", "endpoint", "enable_thinking", "max_tokens", "seed", "prompt_id", "fixture_id", "raw_output"):
            if k not in r:
                red.append("PROVENANCE_INCOMPLETE[%s]: %s 欠落" % (r["fixture_id"], k))
                break
    if red:
        print("INTENT_PROBE_PROTO --check: RED")
        for m in red[:12]:
            print("  " + m)
        return 1
    agg = header["aggregate"]
    print("INTENT_PROBE_PROTO --check: GREEN (決定論 parser/集計 再現; fixture 固定; provenance 完全; measure-first)")
    for mk in [c[0] for c in RUN_CONFIGS]:
        a = agg[mk]
        print("  [%s] 発散率=%.2f%s 軸妥当=%s 戦略一致=%s seed一貫=%s 聞返recall=%s 誤聞返=%s"
              % (mk, a["diverge_rate"], a["diverge_kinds"] or "", a["axis_validity"], a["strategy_match"],
                 a["seed_consistent_fixtures"], a["probe_recall"], a["false_probe"]))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if not _infra_ok():
        print("INTENT_PROBE_PROTO: NO_INFRA — :8005 で実推論が返らない(捏造の測定をしない)")
        return 2
    rows = run()
    agg = aggregate(rows)
    open(OUT, "w", encoding="utf-8").write(_ser(rows, agg))
    print("実測 %d 行(fixture=%d × menu=2 × seed=%d)。measure-first サマリ:" % (len(rows), len(FIXTURES), len(SEEDS)))
    for mk in [c[0] for c in RUN_CONFIGS]:
        a = agg[mk]
        print("  [%s] 発散率=%.2f %s | 軸妥当=%s 戦略一致=%s seed一貫=%s 聞返recall=%s 誤聞返=%s"
              % (mk, a["diverge_rate"], a["diverge_kinds"] or "", a["axis_validity"], a["strategy_match"],
                 a["seed_consistent_fixtures"], a["probe_recall"], a["false_probe"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
