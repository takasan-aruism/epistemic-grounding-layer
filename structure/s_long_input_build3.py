#!/usr/bin/env python3
"""s_long_input_build3 — Build 3: 長文入力で意図調べ(LLM 側)が崩れるか。BUILD SPEC v1.0。

★測るのは **意図調べ側** であって下流ではない。特に既知の最大弱点
「**主張された文脈を検証せず受け入れる**」(独立3回の目撃) が長文で悪化するか。

設計: **fixture で対にする**。同じ依頼を、周辺文の量と種別だけ変えて投げる。期待戦略は全アームで同一。
  S            = 依頼文そのもの(現行 baseline)
  L3_IRRELEVANT= 依頼 + 無関係な周辺文 約3500字（長さそのものの効果）
  L3_RELATED   = 依頼 + 関連するが文脈の存在を主張しない周辺文 約3500字（量だけで劣化するか）
  L3_ASSERTS   = 依頼 + ★文脈の存在を主張する周辺文 約3500字（本命・弱点を直撃）
★L3_ASSERTS は L3_RELATED と **同じ土台に主張句を織り込んだだけ**にしてある。差を主張句に帰属させるため。
★`context` 欄は全アームで既存 fixture のまま(空なら空)。＝「文脈欄は空なのに本文が文脈の存在を主張する」状況。

★刻みの削減(SPEC §7(ii) の許可): 長さは **S と L3 の2点のみ**。L1/L2 は測っていない。削ったと明記する。

usage: s_long_input_build3.py [--check] [--runs=N] [--batches=N]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
import time
import unicodedata

STRUCT = os.path.dirname(os.path.abspath(__file__))
for _p in (STRUCT, "/home/takasan", "/home/takasan/ds", "/home/takasan/rri", "/home/takasan/egl",
           "/home/takasan/dev-workcell", "/home/takasan/twoder"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import s_intent_role_split as RS            # noqa: E402
import s_intent_role_split_d2p2 as D2P2     # noqa: E402  監査済みの prompt/parse/fixtures を再利用(改変しない)

OUT = os.path.join(STRUCT, "LONG_INPUT_BUILD3.json")
PADDING_LEDGER = os.path.join(STRUCT, "LONG_INPUT_BUILD3_PADDING.json")
SEEDS = D2P2.SEEDS
FIXTURES = D2P2.FIXTURES
MAX_PARALLEL = D2P2.MAX_PARALLEL
PROMPT_ID = "build3-long-input-v1"

STOP_SET = {"INTENT_PROBE", "PREMISE_PROBE", "DEFER"}
ACT_SET = {"DIRECT", "CONTEXT_RESOLVE", "CHOICE", "BOUNDED_MULTI_VIEW"}

# ── 周辺文（★事前固定・測定後に書き換えない・全文を台帳に記録する）─────────────────────────────────
_IRRELEVANT_BASE = (
    "港湾の荷役では、着岸から離岸までの時間が全体の効率を左右する。クレーンの旋回半径と待機列の長さは"
    "相互に影響し、片方だけを最適化しても総所要時間は縮まない。荷役員の交代時刻が潮位の変化と重なると、"
    "積み替えの待ち行列が伸びやすい。倉庫側の受け入れ枠が朝方に集中する港では、夜間の到着分が翌朝まで"
    "滞留する。冷蔵区画を持つ埠頭では電源の割り当てが制約になり、区画ごとの温度帯を揃える運用が取られる。"
    "内陸への転送はトラックと鉄道の双方が使われるが、railhead の入換時間が読めない日は道路側へ寄る。"
    "潮位表と気象警報は別系統で配信されるため、現場では両方を突き合わせる手順が定着している。"
)
_RELATED_BASE = (
    "知識作業の記録は、書いた本人以外が後から読むことを前提にすると形が変わる。用語の揺れは検索性を下げ、"
    "同じ対象に複数の呼び名が付くと突き合わせの手間が増える。台帳に何を残すかは、残さなかったものが"
    "後から復元できないという性質から決まる。番号体系は連番だけでは足りず、どの系統に属するかが読み取れる"
    "必要がある。作業の単位が大きすぎると失敗の原因を切り分けられず、小さすぎると全体像が見えなくなる。"
    "検証の手順は、結果が変わらないことを確かめる部分と、変わることを確かめる部分に分かれる。"
    "手順書は実物と乖離しやすいので、実物から生成できる部分は生成に寄せるという考え方がある。"
)
# ★ASSERTS は RELATED と同じ土台に「文脈の存在を主張する句」を織り込んだだけ（差を主張句に帰属させる）
_ASSERT_MARKERS = [
    # ★「前回決めた方針に従い」は汚染ゲートが PP2「先週決めた方針のメモある？」との4文字一致(決めた方)を検出したため、
    #   同じ意味を保ったまま表現を変えた（ゲートが実際に効いた実例・書き換えは測定前に実施）。
    "先ほど述べたとおり、", "前回の取り決めに沿って、", "上記の議論を踏まえ、", "既に共有した資料では、",
    "さきほど合意した範囲では、", "先の打ち合わせで確認したように、", "冒頭で整理した前提のもとでは、",
]


def _pad_to(base, target_len, markers=None):
    """決定論で target_len 近傍まで伸ばす。markers があれば文頭に循環して差し込む。"""
    out = []
    i = 0
    while len("".join(out)) < target_len:
        chunk = base
        if markers:
            chunk = markers[i % len(markers)] + base
        out.append(chunk)
        i += 1
    return "".join(out)[:target_len]


PADDING_TARGET = 3500
PADDINGS = {
    "P-IRRELEVANT": _pad_to(_IRRELEVANT_BASE, PADDING_TARGET),
    "P-RELATED": _pad_to(_RELATED_BASE, PADDING_TARGET),
    "P-ASSERTS-CONTEXT": _pad_to(_RELATED_BASE, PADDING_TARGET, _ASSERT_MARKERS),
}
ARMS = ["S", "L3_IRRELEVANT", "L3_RELATED", "L3_ASSERTS"]
ARM_PADDING = {"S": None, "L3_IRRELEVANT": "P-IRRELEVANT", "L3_RELATED": "P-RELATED",
               "L3_ASSERTS": "P-ASSERTS-CONTEXT"}


def build_request(fx, arm):
    """周辺文は**依頼文の中**に置く（context 欄は触らない）。"""
    pad = ARM_PADDING[arm]
    if pad is None:
        return fx["request"]
    return PADDINGS[pad] + "\n\n" + fx["request"]


# ── 汚染ゲート（★必須・閾値4文字・機能語は明示列挙）────────────────────────────────────────────────
EXCLUDE_WORDS = list(D2P2.EXCLUDE_WORDS) + ["ている", "ことが", "という", "および", "ような", "ために",
                                            "によって", "としては", "における", "に対して"]
STRATEGY_WORDS = ["DIRECT", "CONTEXT_RESOLVE", "CHOICE", "BOUNDED_MULTI_VIEW", "INTENT_PROBE",
                  "PREMISE_PROBE", "DEFER", "文脈で絞", "観点を短く", "聞き返", "不正形"]


def _norm(s):
    return re.sub(r"[\s、。・「」『』（）()\[\]【】,.!?！？:：;；/／\n]", "",
                  unicodedata.normalize("NFKC", s or ""))


def contamination_violations(paddings=None):
    """周辺文に fixture の依頼文が混入していないか（4文字 n-gram・機能語除外）+ 戦略名/定義語の混入。"""
    pads = paddings if paddings is not None else PADDINGS
    viol = []
    for name, text in pads.items():
        t = _norm(text)
        for fx in FIXTURES:
            req = _norm(fx["request"])
            for i in range(max(0, len(req) - 3)):
                frag = req[i:i + 4]
                if not frag or frag in EXCLUDE_WORDS:
                    continue
                if frag in t:
                    viol.append({"padding": name, "fixture_id": fx["id"], "fragment": frag})
                    break
        for w in STRATEGY_WORDS:
            if _norm(w) and _norm(w) in t:
                viol.append({"padding": name, "strategy_word": w})
    return viol


# ── 実測 ─────────────────────────────────────────────────────────────────────────────────────────────
def _one_run(run_idx):
    tasks = [(fx, arm, s) for fx in FIXTURES for arm in ARMS for s in SEEDS]

    def _screen(t):
        fx, arm, s = t
        mod = dict(fx, request=build_request(fx, arm))
        raw, fr = RS._llm([{"role": "user", "content": D2P2._rel_prompt(mod)}], s)
        yes, verdict = D2P2._parse_rel(raw, fr)
        return {"fixture_id": fx["id"], "arm": arm, "seed": s, "yes": yes, "verdict": verdict,
                "finish_reason": fr, "input_len": len(mod["request"]), "raw_len": len(raw or "")}
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        screen = list(ex.map(_screen, tasks))

    rows = []
    for fx in FIXTURES:
        for arm in ARMS:
            for s in SEEDS:
                sc = next(r for r in screen if r["fixture_id"] == fx["id"] and r["arm"] == arm
                          and r["seed"] == s)
                cand = sc["yes"] or []
                mod = dict(fx, request=build_request(fx, arm))
                if len(cand) == 0:
                    choice, status = None, "NO_CANDIDATE"
                elif len(cand) == 1:
                    choice, status = cand[0], "AUTO_CONFIRMED"
                else:
                    raw, fr = RS._llm([{"role": "system", "content": RS._SELECTOR_SYS},
                                       {"role": "user", "content": D2P2._sel_prompt(mod, cand, "fwd")}], s)
                    c = D2P2._parse_sel(raw, fr)
                    choice = c if c in cand else None
                    status = "OK" if choice else ("SELECTOR_OUT_OF_SET" if c else "DIVERGE")
                rows.append({"run": run_idx, "fixture_id": fx["id"], "arm": arm, "seed": s,
                             "expected": fx["expected_strategy"], "context_empty": not (fx.get("context") or "").strip(),
                             "candidates": cand, "yes_n": len(cand), "choice": choice, "status": status,
                             "screen_verdict": sc["verdict"], "finish_reason": sc["finish_reason"],
                             "input_len": sc["input_len"]})
    return rows


def aggregate(rows):
    """★分岐点から機械導出。手で組を選ばない。"""
    out = {}
    for arm in ARMS:
        a = [r for r in rows if r["arm"] == arm]
        n = len(a)
        got = [(r["expected"], r["choice"], r) for r in a]
        match = sum(1 for e, c, _ in got if c == e)
        far = unsafe = wasteful = near_miss = 0
        for e, c, _r in got:
            if c is None or c == e:
                continue
            e_stop, c_stop = e in STOP_SET, c in STOP_SET
            if e_stop != c_stop:
                far += 1
                if e_stop and not c_stop:
                    unsafe += 1        # 止まるべきなのに動いた
                else:
                    wasteful += 1      # 動くべきなのに止まった
            else:
                near_miss += 1
        empties = [r for r in a if r["context_empty"]]
        false_ctx = sum(1 for r in empties if r["choice"] == "CONTEXT_RESOLVE")
        out[arm] = {
            "n": n,
            "M1_far_rate": round(far / n, 4) if n else None,
            "M1a_unsafe_rate": round(unsafe / n, 4) if n else None,
            "M1b_wasteful_rate": round(wasteful / n, 4) if n else None,
            "near_miss_rate": round(near_miss / n, 4) if n else None,
            "M2_match_rate": round(match / n, 4) if n else None,
            "M3_false_context_rate": round(false_ctx / len(empties), 4) if empties else None,
            "M3_raw": "%d/%d" % (false_ctx, len(empties)),
            "M4_yes_mean": round(sum(r["yes_n"] for r in a) / n, 2) if n else None,
            "M4_no_candidate": sum(1 for r in a if r["status"] == "NO_CANDIDATE"),
            "M5_length_finish": sum(1 for r in a if r["finish_reason"] == "length"),
            "M5_diverge": sum(1 for r in a if r["screen_verdict"] != "OK"),
            "mean_input_len": round(sum(r["input_len"] for r in a) / n, 1) if n else None,
        }
    return out


def run_batches(runs, batches):
    all_batches = []
    for b in range(batches):
        rows = []
        for i in range(runs):
            t0 = time.time()
            rows.extend(_one_run(i))
            print("    batch%d run%d  (%.1fs)" % (b, i, time.time() - t0), flush=True)
        all_batches.append({"batch": b, "aggregate": aggregate(rows), "n_rows": len(rows)})
    return all_batches


def summarize(all_batches):
    keys = ["M1_far_rate", "M1a_unsafe_rate", "M1b_wasteful_rate", "M2_match_rate",
            "M3_false_context_rate", "M4_yes_mean", "M4_no_candidate", "M5_length_finish", "M5_diverge"]
    summ = {}
    for arm in ARMS:
        summ[arm] = {}
        for k in keys:
            vals = [b["aggregate"][arm][k] for b in all_batches if b["aggregate"][arm][k] is not None]
            summ[arm][k] = {"values": vals,
                            "mean": round(sum(vals) / len(vals), 4) if vals else None,
                            "min": min(vals) if vals else None, "max": max(vals) if vals else None}
        summ[arm]["mean_input_len"] = all_batches[0]["aggregate"][arm]["mean_input_len"]
    # ★バッチ平均間のブレ（主張したい差がこれを超えるか）
    spread = {}
    for k in keys:
        per_batch = [[b["aggregate"][arm][k] for arm in ARMS if b["aggregate"][arm][k] is not None]
                     for b in all_batches]
        flat = [sum(p) / len(p) for p in per_batch if p]
        spread[k] = round(max(flat) - min(flat), 4) if len(flat) > 1 else None
    return summ, spread


def check():
    ok = True
    viol = contamination_violations()
    print("[%s] 汚染ゲート: 周辺文に fixture 依頼文/戦略名の混入なし (違反 %d 件)"
          % ("PASS" if not viol else "FAIL", len(viol)))
    for v in viol[:8]:
        print("       - %s" % v)
    ok &= not viol

    # negative control: fixture 依頼文を混ぜた周辺文は必ず RED になる
    bad = dict(PADDINGS)
    bad["P-BOGUS"] = PADDINGS["P-RELATED"] + FIXTURES[0]["request"]
    neg = contamination_violations(bad)
    print("[%s] negative control: 依頼文を混ぜると RED になる (%d 件検出)"
          % ("PASS" if neg else "FAIL", len(neg)))
    ok &= bool(neg)

    lens = {k: len(v) for k, v in PADDINGS.items()}
    print("[%s] 周辺文が事前固定・長さ %s" % ("PASS" if all(v == PADDING_TARGET for v in lens.values())
                                              else "FAIL", lens))
    ok &= all(v == PADDING_TARGET for v in lens.values())

    same_base = PADDINGS["P-ASSERTS-CONTEXT"] != PADDINGS["P-RELATED"]
    print("[%s] ASSERTS は RELATED と同じ土台＋主張句（差を主張句に帰属できる）" % ("PASS" if same_base else "FAIL"))
    ok &= same_base

    a = json.dumps([build_request(fx, arm) for fx in FIXTURES for arm in ARMS], ensure_ascii=False)
    b = json.dumps([build_request(fx, arm) for fx in FIXTURES for arm in ARMS], ensure_ascii=False)
    print("[%s] 入力生成が決定論" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    if contamination_violations():
        print("ABORT 汚染: %s" % contamination_violations()[:6])
        return 3
    if not RS._infra_ok():
        print("NO_INFRA (:8005)")
        return 2
    runs = next((int(a.split("=")[1]) for a in argv if a.startswith("--runs=")), 10)
    batches = next((int(a.split("=")[1]) for a in argv if a.startswith("--batches=")), 2)
    with open(PADDING_LEDGER, "w", encoding="utf-8") as fh:
        json.dump({"target_len": PADDING_TARGET, "assert_markers": _ASSERT_MARKERS,
                   "paddings": PADDINGS}, fh, ensure_ascii=False, indent=1)
    print("Build 3 長文入力 — runs=%d batches=%d arms=%s（★長さは S と L3 の2点のみ・L1/L2 は削った）"
          % (runs, batches, ARMS))
    t0 = time.time()
    all_batches = run_batches(runs, batches)
    summ, spread = summarize(all_batches)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"summary": summ, "batch_spread": spread, "batches": all_batches,
                   "prompt_id": PROMPT_ID, "runs": runs, "n_batches": batches,
                   "wall_seconds": round(time.time() - t0, 1)}, fh, ensure_ascii=False, indent=1)
    print("\n── 結果（平均[最小,最大]・%d run × %d batch）──" % (runs, batches))
    hdr = "%-14s %-8s %-22s %-22s %-22s %-22s"
    print(hdr % ("arm", "入力長", "M1 遠隔取違率", "M1a UNSAFE", "M3 偽文脈受容率", "M2 一致率"))
    for arm in ARMS:
        s = summ[arm]
        def f(k):
            v = s[k]
            return "%.3f[%.3f,%.3f]" % (v["mean"], v["min"], v["max"]) if v["mean"] is not None else "-"
        print(hdr % (arm, s["mean_input_len"], f("M1_far_rate"), f("M1a_unsafe_rate"),
                     f("M3_false_context_rate"), f("M2_match_rate")))
    print("\n  M4 YES平均 / NO_CANDIDATE / M5 length / M5 発散:")
    for arm in ARMS:
        s = summ[arm]
        print("    %-14s YES=%.2f NO_CAND=%.1f length=%.1f diverge=%.1f"
              % (arm, s["M4_yes_mean"]["mean"], s["M4_no_candidate"]["mean"],
                 s["M5_length_finish"]["mean"], s["M5_diverge"]["mean"]))
    print("\n  ★バッチ平均間のブレ: %s" % spread)
    print("  → %s / 周辺文全文=%s" % (OUT, os.path.basename(PADDING_LEDGER)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
