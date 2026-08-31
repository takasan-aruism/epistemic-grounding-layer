#!/usr/bin/env python3
"""★同一母集団で 回帰試験する(★ITEM-2DER-EVO-0037 受入⑨)。

★測る物(★Taka 指示 2026-08-31『文字が一致することは 必ずしも正しいとは限らない』)=
  ★被覆率は 主指標に しない。★見るのは ★機械が 決められる 3つだけ=
    ①JSON が 取れた率  ②原文と一致した率(★追跡可能性)  ③候補数
  ★どれも ★正解を 要らない ∴ ★gold に 依存しない。

★★差の 読み方(★自分の COMPARE_RULES)= ★ノイズ帯を 先に 出し ★帯を 超えた 時だけ 差と 呼ぶ。
★★★帯は ★指標ごとに 違う(★2026-09-01 に 踏んだ 誤り)=
  ・被覆率の 帯= 5.8pt(2026-08-30 実測)
  ・★追跡可能率の 帯= ★27.8pt(★同じ版を 4周= 72.2 / 80.0 / 86.7 / 100.0)
  ★私は ★被覆率の 帯を ★追跡可能率に 当てて ★『変更なしなのに 差が 出た』と 読みかけた。
  ∴ ★帯は ★その指標で 測る。★他の指標の 帯を 流用しない。
"""
import json, os, statistics, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_r1 import _call, _parse_json, mechanical_check, POP

D = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(D, "regress_baseline.json")
BAND = {"追跡可能率": 27.8}          # ★実測(★同じ版を 4周した 幅)。★測った指標の 帯だけ 持つ


def measure(ver, tids):
    """★1版を 母集団で 1周 引く。★正解を 要らない 3つだけ 返す。"""
    P = __import__("prompts_%s" % ver)
    pop = json.load(open(POP))
    js = ok = cand = matched = 0
    for tid in tids:
        goal = pop[tid]["goal"]
        obj = _parse_json(_call(P.R1_GENERATOR % goal).get("content") or "")
        js += obj is not None
        cs = (obj or {}).get("candidates") or []
        m = mechanical_check(goal, cs)
        cand += m["候補"]; matched += m["原文と一致"]
    n = len(tids)
    return {"版": ver, "分母(TASK)": n, "JSONが取れた": "%d/%d" % (js, n),
            "候補": cand, "原文と一致": "%d/%d" % (matched, cand),
            "追跡可能率": round(100.0 * matched / cand, 1) if cand else 0.0}


def main(argv):
    vers = [a for a in argv if a.startswith("v")] or ["v1"]
    n = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 6
    tids = sorted(json.load(open(POP)))[:n]
    print("★回帰試験(★同一母集団 %d TASK・★正解を要らない3指標)" % len(tids))
    now = {}
    for v in vers:
        t0 = time.perf_counter()
        r = measure(v, tids)
        r["秒"] = round(time.perf_counter() - t0, 1)
        now[v] = r
        print("  %-4s JSON %-6s 候補%4d 原文と一致 %-8s = %5.1f%%  %.0f秒" % (
            v, r["JSONが取れた"], r["候補"], r["原文と一致"], r["追跡可能率"], r["秒"]))
    if "--save" in argv:
        json.dump(now, open(BASE, "w"), ensure_ascii=False)
        print("\n★基準として 保存した: %s" % BASE)
        return
    if not os.path.exists(BASE):
        print("\n★基準が 無い= ★--save で 先に 作る(★『前と同じ』が 言えない)")
        return
    old = json.load(open(BASE))
    b = BAND["追跡可能率"]
    print("\n★前回との 差(★帯 %.1fpt を 超えた 時だけ 差と 呼ぶ= ★追跡可能率の 帯)" % b)
    for v in vers:
        if v not in old:
            print("  %-4s ★基準に 無い= 比べられない" % v); continue
        d = now[v]["追跡可能率"] - old[v]["追跡可能率"]
        verdict = "★差(帯の外)" if abs(d) > b else "★帯の内側= 差と 呼ばない"
        print("  %-4s 追跡可能率 %.1f%% → %.1f%% (%+.1fpt) %s" % (
            v, old[v]["追跡可能率"], now[v]["追跡可能率"], d, verdict))


if __name__ == "__main__":
    main(sys.argv[1:])
