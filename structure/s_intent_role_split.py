#!/usr/bin/env python3
"""s_intent_role_split — 意図調べ arm-D「役割分割」: 選別役(YES/NO) と 選択役 を分ける。

Taka 指示: 木を捨て役割を分ける。7 戦略を**独立に**「この依頼に一致するか YES/NO」(選別役=観測者・勝者を選ばない)、
別役割で「YES の中から最善を選べ」(選択役)。arm-C3 の短絡ツリー(上流1誤りが下流正答を殺す・DE-0544)を構造的に消す。

ESDE Language A1 の先行実績を移植(DESIGN 調査済):
- 役割言語「You are an OBSERVER, not a classifier. Do NOT pick a winner.」
- ★YES 膨張が実際に起きる(QwQ 48中39に非ゼロ)。対策=既定NO / 員数明示(通常1-2) / 理由なきYES禁止 / 弱いYES禁止。
- 監査役は検出のみ(同一モデルに直させると失敗)→ flag→選別役が制約付きで再観測。
- binary か連続値(0-10)かは両方測る(ESDE は binary を捨て 0-10 にした経緯・粒度が違うので両測)。

metric=seed平均(arm-C 0.5833 / C3 0.5397 と同一物差し)。**arm-C2 0.83 は汚染値ゆえ並べない。**
measure-first: 役割分割が効かなければ正直に。YES 膨張していたら「していた」と書く。

usage:  s_intent_role_split.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
import unicodedata
from collections import Counter

import s_intent_probe_armc3 as A3   # FIXTURES(21・held-out)を import

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_ROLE_SPLIT.jsonl")
MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
MAX_TOKENS = 200
PROMPT_ID = "role-split-v1"
MAX_PARALLEL = 16

# §9 7戦略 + 定義1文(名前だけだと語感で決まるので毎回同梱)
STRATEGIES = [
    ("DIRECT", "問いが安定し回答空間が狭く、そのまま単一の答えを返せる"),
    ("CONTEXT_RESOLVE", "単体では複数解釈できるが、直前の文脈に支配的な解釈があり文脈で絞れる"),
    ("CHOICE", "主要な解釈が有限個あり、ユーザに選択肢を提示して一つ選ばせるのが妥当"),
    ("BOUNDED_MULTI_VIEW", "複数の観点を短く比較して見せること自体が答えとして妥当"),
    ("INTENT_PROBE", "対象が何を指すか意図が不明で、調査前に極小の確認質問が要る"),
    ("PREMISE_PROBE", "依頼が前提する事実/存在が怪しく、確認せずに答えてはいけない"),
    ("DEFER", "不正形・文脈不足・要明確化で、今は保留すべき"),
]
STRAT_DEF = dict(STRATEGIES)
STRAT_NAMES = [s for s, _ in STRATEGIES]
# 排他ペア(CONTRADICTORY_YES 用)。DIRECT/DEFER は他と両立しにくい。
MUTEX = [("DEFER", "DIRECT"), ("DIRECT", "BOUNDED_MULTI_VIEW"), ("DIRECT", "INTENT_PROBE"),
         ("DIRECT", "PREMISE_PROBE"), ("DIRECT", "CHOICE"), ("DEFER", "BOUNDED_MULTI_VIEW")]

_ANTI_INFLATION = ("あなたは観測者であり分類器ではない。勝者を選ばない。既定は NO。迷ったら NO。"
                   "7戦略のうち通常 YES は1〜2個。この戦略が本当に一致する時だけ YES。"
                   "具体的な理由を1文で言えないなら NO。")


def _llm(messages, seed, mt=MAX_TOKENS):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": messages, "seed": seed, "temperature": 0.7,
                       "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason")


def _infra_ok():
    try:
        _llm([{"role": "user", "content": "ping"}], 0, 16)
        return True
    except Exception:
        return False


# ── ロール1 選別役(独立・並列)。mode=D1(YES/NO) or D2(0-10)──────────────────────
def _screen_prompt(fx, strat, mode):
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    head = "依頼:「%s」%s\nこの依頼に戦略「%s = %s」は一致するか。%s" % (
        fx["request"], ctx, strat, STRAT_DEF[strat], _ANTI_INFLATION)
    if mode == "D1":
        return head + '\n出力は JSON のみ: {"match":"YES" または "NO","reason":"40字以内"}'
    return head + '\n当てはまり度を 0〜10 の整数で。JSON のみ: {"score":0-10,"reason":"40字以内"}'


def _parse_screen(mode, raw, fr):
    if fr == "length":
        return None, None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, None, "DIVERGE_SCHEMA"
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None, None, "DIVERGE_SCHEMA"
    reason = (d.get("reason") or "").strip()
    if mode == "D1":
        mt = d.get("match")
        if mt not in ("YES", "NO"):
            return None, None, "DIVERGE_SCHEMA"
        return (mt == "YES"), reason, ("OK" if reason else "DIVERGE_NO_REASON")
    sc = d.get("score")
    if not isinstance(sc, int) or not (0 <= sc <= 10):
        return None, None, "DIVERGE_SCHEMA"
    return sc, reason, ("OK" if reason else "DIVERGE_NO_REASON")


# ── ロール3 監査役(決定論 pre-screen・LLM 使わない)────────────────────────────
def audit(yes_set, reasons):
    flags = []
    if len(yes_set) >= 3:
        flags.append("YES_INFLATION")
    if len(yes_set) == 0:
        flags.append("NO_CANDIDATE")
    for a, b in MUTEX:
        if a in yes_set and b in yes_set:
            flags.append("CONTRADICTORY_YES:%s+%s" % (a, b))
    if any((s in yes_set) and (not reasons.get(s)) for s in yes_set):
        flags.append("REASONLESS_YES")
    return flags


# ── ロール2 選択役(別 system prompt・YES 候補のみ・順序 fwd/rev)──────────────────
_SELECTOR_SYS = "あなたは、与えられた候補の中から最も当てはまるものを1つ選ぶ役割。候補集合の外は選べない。"


def _select_prompt(fx, cands, order):
    c = list(cands) if order == "fwd" else list(reversed(cands))
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s" % (s, STRAT_DEF[s]) for s in c)
    return ("依頼:「%s」%s\n次の候補のうち最も当てはまるもの1つを選び、理由を1文で。\n%s"
            "\n出力は JSON のみ: {\"choice\":\"戦略名\",\"reason\":\"40字以内\"}" % (fx["request"], ctx, lst))


def _parse_select(raw, fr):
    if fr == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, "DIVERGE_SCHEMA"
    try:
        c = json.loads(m.group(0)).get("choice")
    except Exception:
        return None, "DIVERGE_SCHEMA"
    for s in STRAT_NAMES:
        if c and s in c:
            return s, "OK"
    return None, "DIVERGE_SCHEMA"


# ── 汚染ゲート(閾値4・EXCLUDE_WORDS 機能語・DE-0544 の「〜の是非は」抜けを塞ぐ)────────
EXCLUDE_WORDS = ["として", "ですか", "ますか", "でしょう", "について", "における", "のような", "すべき", "どちら"]


def _norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"[\s、。・「」『』（）()\[\]【】,.!?！？:：;；/／]", "", s)


def contamination_violations():
    tmpl = _norm(_ANTI_INFLATION + _SELECTOR_SYS + " ".join(s + d for s, d in STRATEGIES))
    viol = []
    for fx in A3.FIXTURES:
        req = _norm(fx["request"])
        for i in range(len(req) - 3):
            frag = req[i:i + 4]     # 閾値4(5だと「〜の是非は」が抜けた・DE-0544)
            if frag in EXCLUDE_WORDS:
                continue
            if frag and frag in tmpl:
                viol.append({"fixture_id": fx["id"], "fragment": frag})
                break
    return viol


# ── 再観測(監査 flag 時・選別役に制約付きで観測し直させる・監査は直さない=ESDE)──────────
def reobserve(fx, yes, reasons, seed):
    """flag が立った YES 集合を、選別役に「弱い YES を NO に落とせ」で再観測。返り (kept list, raw)。"""
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s（前回理由: %s）" % (s, STRAT_DEF[s], reasons.get(s, "")) for s in yes)
    p = ("依頼:「%s」%s\n前回この依頼に次の戦略へ YES を付けた:\n%s\n"
         "7戦略のうち通常一致するのは1〜2個。根拠が弱い/具体的でない YES を NO に落とし、本当に残すべき戦略だけ挙げよ。"
         '\n出力は JSON のみ: {"keep":["戦略名", ...],"reason":"40字以内"}' % (fx["request"], ctx, lst))
    raw, fr = _llm([{"role": "user", "content": p}], seed)
    kept = []
    m = re.search(r"\{.*\}", raw or "", re.S)
    if m:
        try:
            k = json.loads(m.group(0)).get("keep") or []
            kept = [s for s in yes if any(s in str(x) for x in k)]
        except Exception:
            pass
    return kept, raw


# ── 実測 ─────────────────────────────────────────────────────────────────────
def run():
    import time as _t
    # ロール1: fixture×strat×mode×seed 独立
    s_tasks = [(fx, strat, mode, s) for fx in A3.FIXTURES for strat in STRAT_NAMES
               for mode in ("D1", "D2") for s in SEEDS]

    def _screen(t):
        fx, strat, mode, s = t
        raw, fr = _llm([{"role": "user", "content": _screen_prompt(fx, strat, mode)}], s)
        val, reason, verdict = _parse_screen(mode, raw, fr)
        return {"role": "role1_screen", "fixture_id": fx["id"], "strategy": strat, "mode": mode,
                "seed": s, "value": val, "reason": reason, "parse_verdict": verdict, "raw_output": raw}
    t0 = _t.time()
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        screen = list(ex.map(_screen, s_tasks))

    # 監査(決定論) + 選択役(D1 の YES 候補・順序両方)
    sel_rows, audit_rows = [], []
    for fx in A3.FIXTURES:
        for s in SEEDS:
            d1 = {r["strategy"]: r for r in screen if r["fixture_id"] == fx["id"] and r["mode"] == "D1" and r["seed"] == s}
            yes = [st for st in STRAT_NAMES if d1.get(st, {}).get("value") is True]
            reasons = {st: d1[st]["reason"] for st in yes if st in d1}
            flags = audit(set(yes), reasons)
            # 監査 flag(YES膨張/矛盾)→ 再観測1回。初回と再観測の両方を記録・yes_final を以降で使う(隠さない)。
            reobs_flag = any(f == "YES_INFLATION" or f.startswith("CONTRADICTORY_YES") for f in flags)
            reobs_raw, yes_final = "", yes
            if reobs_flag and len(yes) >= 2:
                kept, reobs_raw = reobserve(fx, yes, reasons, s)
                yes_final = kept if kept else yes   # 空なら初回を使う(捏造で減らさない)
            audit_rows.append({"role": "audit", "fixture_id": fx["id"], "seed": s,
                               "yes_set": yes, "n_yes": len(yes), "flags": flags,
                               "reobserved": bool(reobs_raw), "yes_final": yes_final,
                               "n_yes_final": len(yes_final), "reobs_raw": reobs_raw})
            for order in ("fwd", "rev"):
                if len(yes_final) == 0:
                    sel_rows.append({"role": "role2_select", "fixture_id": fx["id"], "seed": s, "order": order,
                                     "candidates": yes_final, "choice": None, "status": "NO_CANDIDATE", "raw_output": ""})
                    continue
                if len(yes_final) == 1:
                    sel_rows.append({"role": "role2_select", "fixture_id": fx["id"], "seed": s, "order": order,
                                     "candidates": yes_final, "choice": yes_final[0], "status": "SINGLE_CANDIDATE", "raw_output": ""})
                    continue
                raw, fr = _llm([{"role": "system", "content": _SELECTOR_SYS},
                                {"role": "user", "content": _select_prompt(fx, yes_final, order)}], s)
                choice, v = _parse_select(raw, fr)
                status = "OK" if (choice in yes_final) else ("SELECTOR_OUT_OF_SET" if choice else v)
                sel_rows.append({"role": "role2_select", "fixture_id": fx["id"], "seed": s, "order": order,
                                 "candidates": yes_final, "choice": choice if choice in yes_final else None,
                                 "raw_choice": choice, "status": status, "raw_output": raw})
    wall = round(_t.time() - t0, 2)
    return screen, sel_rows, audit_rows, wall


def _expected(fid):
    return next(fx["expected_strategy"] for fx in A3.FIXTURES if fx["id"] == fid)


def _d2_choice(screen, fid, seed):
    """arm-D2: 0-10 の最高スコア戦略(同点は STRAT_NAMES 順で決定論)。"""
    best, bestsc = None, -1
    for st in STRAT_NAMES:
        r = next((r for r in screen if r["fixture_id"] == fid and r["mode"] == "D2" and r["seed"] == seed and r["strategy"] == st), None)
        sc = r["value"] if r and isinstance(r["value"], int) else -1
        if sc > bestsc:
            best, bestsc = st, sc
    return best if bestsc >= 0 else None


def aggregate(screen, sel_rows, audit_rows):
    # arm-D1: selector(fwd) の choice が期待戦略か(seed 平均)
    d1_hit = d1_tot = 0
    for fx in A3.FIXTURES:
        for s in SEEDS:
            sel = next((r for r in sel_rows if r["fixture_id"] == fx["id"] and r["seed"] == s and r["order"] == "fwd"), None)
            got = sel["choice"] if sel else None
            d1_tot += 1
            d1_hit += int(got == fx["expected_strategy"] or got in fx.get("acceptable_strategies", []))
    # arm-D2: 最高スコア戦略が期待か
    d2_hit = d2_tot = 0
    for fx in A3.FIXTURES:
        for s in SEEDS:
            got = _d2_choice(screen, fx["id"], s)
            d2_tot += 1
            d2_hit += int(got == fx["expected_strategy"] or got in fx.get("acceptable_strategies", []))
    # YES 膨張(D1): fixture×seed あたりの YES 数分布
    yes_counts = [a["n_yes"] for a in audit_rows]
    # 選択役 順序一致(position bias)
    pb_tot = pb_agree = 0
    for fx in A3.FIXTURES:
        for s in SEEDS:
            f = next((r for r in sel_rows if r["fixture_id"] == fx["id"] and r["seed"] == s and r["order"] == "fwd"), None)
            r = next((r for r in sel_rows if r["fixture_id"] == fx["id"] and r["seed"] == s and r["order"] == "rev"), None)
            if f and r and f["choice"] and r["choice"]:
                pb_tot += 1
                pb_agree += int(f["choice"] == r["choice"])
    fl = Counter(f for a in audit_rows for f in a["flags"])
    reobs = [a for a in audit_rows if a.get("reobserved")]
    reobs_reduced = sum(1 for a in reobs if a.get("n_yes_final", a["n_yes"]) < a["n_yes"])
    yes_final_counts = [a.get("n_yes_final", a["n_yes"]) for a in audit_rows]
    return {
        "reobserved_n": len(reobs),
        "reobs_reduced_yes_n": reobs_reduced,
        "yes_final_mean": round(sum(yes_final_counts) / len(yes_final_counts), 2) if yes_final_counts else None,
        "armD1_seedavg": round(d1_hit / d1_tot, 4) if d1_tot else None, "armD1_raw": "%d/%d" % (d1_hit, d1_tot),
        "armD2_seedavg": round(d2_hit / d2_tot, 4) if d2_tot else None, "armD2_raw": "%d/%d" % (d2_hit, d2_tot),
        "yes_count_mean": round(sum(yes_counts) / len(yes_counts), 2) if yes_counts else None,
        "yes_count_dist": {str(k): v for k, v in sorted(Counter(yes_counts).items())},
        "yes_inflation_ge3": sum(1 for c in yes_counts if c >= 3),
        "no_candidate_n": sum(1 for c in yes_counts if c == 0),
        "selector_out_of_set_n": sum(1 for r in sel_rows if r["status"] == "SELECTOR_OUT_OF_SET"),
        "selector_order_agreement": round(pb_agree / pb_tot, 4) if pb_tot else None,
        "audit_flags": dict(fl),
        "screen_diverge_rate": round(sum(1 for r in screen if r["parse_verdict"] != "OK") / len(screen), 4) if screen else 0.0,
        "note": "seed平均で arm-C(0.5833)/C3(0.5397)と同一物差し。arm-C2 0.83 は汚染ゆえ並べない。数字は能力主張でない。",
    }


def _ser(screen, sel_rows, audit_rows, agg, wall):
    hdr = {"_meta": "INTENT_ROLE_SPLIT(arm-D 役割分割: 選別役YES/NO・選択役・監査検出のみ)。木を捨て役割を分ける。",
           "arm": "D", "aggregate": agg, "wall_seconds": wall, "model": MODEL, "prompt_id": PROMPT_ID,
           "strategies": STRAT_NAMES, "seeds": list(SEEDS), "exclude_words": EXCLUDE_WORDS,
           "note": "arm-D1=YES/NO・arm-D2=0-10。YES膨張は ESDE 先行実績どおり実測(していたら正直に)。"}
    lines = [json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in screen + sel_rows + audit_rows]
    return "\n".join(lines) + "\n"


def _report(agg):
    a = agg
    print("  arm-D1(YES/NO→選択)=%s [%s] | arm-D2(0-10最高)=%s [%s] | 選択役順序一致=%s"
          % (a["armD1_seedavg"], a["armD1_raw"], a["armD2_seedavg"], a["armD2_raw"], a["selector_order_agreement"]))
    print("  ★YES膨張: 平均%.2f個/問 分布%s (≥3=%d) | NO_CANDIDATE=%d | SELECTOR_OUT_OF_SET=%d"
          % (a["yes_count_mean"], a["yes_count_dist"], a["yes_inflation_ge3"], a["no_candidate_n"], a["selector_out_of_set_n"]))
    print("  再観測=%d件(YES削減%d件・再観測後YES平均%.2f) 監査flags=%s 選別発散=%.2f"
          % (a["reobserved_n"], a["reobs_reduced_yes_n"], a["yes_final_mean"], a["audit_flags"], a["screen_diverge_rate"]))


def check():
    red = []
    viol = contamination_violations()
    if viol:
        red.append("CONTAMINATION: fixture 文が定義/例に混入 %s" % viol[:8])
    _saved = STRATEGIES[0]
    try:
        STRATEGIES[0] = (STRATEGIES[0][0], STRATEGIES[0][1] + A3.FIXTURES[0]["request"])
        STRAT_DEF[STRATEGIES[0][0]] = STRATEGIES[0][1]
        if not contamination_violations():
            red.append("CONTAMINATION_GATE_DEAD: 注入 fixture 文を検出できない(negative control 失敗)")
    finally:
        STRATEGIES[0] = _saved
        STRAT_DEF[_saved[0]] = _saved[1]
    if not os.path.isfile(OUT):
        red.append("NOT_GENERATED: 先に main(:8005)")
        print("INTENT_ROLE_SPLIT --check: RED")
        for m in red:
            print("  " + m)
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    screen = [l for l in lines[1:] if l.get("role") == "role1_screen"]
    sel_rows = [l for l in lines[1:] if l.get("role") == "role2_select"]
    audit_rows = [l for l in lines[1:] if l.get("role") == "audit"]
    # 選別 parser 再適用
    for r in screen:
        v, reason, verdict = _parse_screen(r["mode"], r["raw_output"], "stop" if r["raw_output"] else r.get("finish_reason", "stop"))
        if verdict != r["parse_verdict"]:
            red.append("SCREEN_PARSE_NONDET[%s/%s/%s/s%d]" % (r["fixture_id"], r["strategy"], r["mode"], r["seed"]))
            break
    # 監査(決定論)再計算: yes_set→flags
    for a in audit_rows:
        reasons = {s: next((r["reason"] for r in screen if r["fixture_id"] == a["fixture_id"] and r["mode"] == "D1"
                            and r["seed"] == a["seed"] and r["strategy"] == s), None) for s in a["yes_set"]}
        if sorted(audit(set(a["yes_set"]), reasons)) != sorted(a["flags"]):
            red.append("AUDIT_NONDET[%s/s%d]" % (a["fixture_id"], a["seed"]))
            break
    if aggregate(screen, sel_rows, audit_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET")
    if red:
        print("INTENT_ROLE_SPLIT --check: RED")
        for m in red[:10]:
            print("  " + m)
        return 1
    print("INTENT_ROLE_SPLIT --check: GREEN (汚染ゲート[negative control実証]; 選別/監査/集計 決定論再現; ロール分離証跡)")
    _report(header["aggregate"])
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    v = contamination_violations()
    if v:
        print("INTENT_ROLE_SPLIT: ABORT — 定義/例に fixture 文が混入(汚染) %s" % v[:8])
        return 3
    if not _infra_ok():
        print("INTENT_ROLE_SPLIT: NO_INFRA — :8005 で実推論が返らない")
        return 2
    screen, sel_rows, audit_rows, wall = run()
    agg = aggregate(screen, sel_rows, audit_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(screen, sel_rows, audit_rows, agg, wall))
    print("arm-D 実測: 選別 %d(21×7×2mode×3seed) + 選択 %d + 監査 %d  wall=%.1fs think=OFF"
          % (len(screen), len(sel_rows), len(audit_rows), wall))
    _report(agg)
    print("  ※seed平均で arm-C3(0.5397)と比較可・arm-C2(0.83汚染)とは並べない・能力主張でない。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
