#!/usr/bin/env python3
"""Audit 1 を 走らせ ★Auditor の 検出率を Generator と 別に 測る(★Taka 指示 §19)。

★正解は ★人が 決めない= ★機械が 決める。
  ★『source_text が 原文に 無い』は ★決定論で 判る ∴ ★これを 正解に する。
  ★Auditor が それを needs_check に 入れられたか= ★AUDIT CATCH RATE。
★使い方: run_a1.py <prompt_version>
"""
import json, os, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_r1 import _call, _parse_json          # ★同じ口を 使う(★写さない)

POP = "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad/detail_pop.json"
D = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    ver = argv[0] if argv else "v1"
    P = __import__("prompts_%s" % ver)
    pop = json.load(open(POP))
    # ★generator の 版と auditor の 版は 別(★v2 は auditor だけ 変えた)。
    #   ★generator の 出力が 無ければ ★同じ generator の 版へ 落とす(★勝手に 作らない)。
    _gen = ver if os.path.exists(os.path.join(D, "r1_%s.json" % ver)) else getattr(
        __import__("prompts_%s" % ver), "GENERATOR_FROM", "v1")
    print("★generator の 出力: r1_%s.json ／ auditor: %s" % (_gen, ver))
    r1 = json.load(open(os.path.join(D, "r1_%s.json" % _gen)))
    out, tot = {}, {"bad": 0, "caught": 0, "good": 0, "false_alarm": 0}
    for tid in sorted(r1):
        v = r1[tid]
        if "候補" not in v or not v["候補"]:
            continue
        goal = pop[tid]["goal"]
        # ★機械が 決める 正解= ★原文に 無い 候補(★人の意見を 使わない)
        bad = {c.get("candidate_id") for c in v["候補"]
               if (c.get("source_text") or "") not in goal}
        cand_txt = json.dumps([{k: c.get(k) for k in ("candidate_id", "source_text",
                                                      "target", "requested_action")}
                               for c in v["候補"]], ensure_ascii=False)
        # ★★v2 から= ★機械が 先に 落とす。★LLM には ★機械が できないことだけ 聞く。
        t0 = time.perf_counter()
        if P.R1_AUDITOR.count("%s") == 1:
            keep = [c for c in v["候補"] if (c.get("source_text") or "") in goal]
            cand_txt = json.dumps([{k: c.get(k) for k in ("candidate_id", "source_text",
                                                          "target", "requested_action")}
                                   for c in keep], ensure_ascii=False)
            r = _call(P.R1_AUDITOR % cand_txt)
        else:
            r = _call(P.R1_AUDITOR % (goal, cand_txt))
        obj = _parse_json(r.get("content") or "")
        need = {x.get("candidate_id") for x in ((obj or {}).get("needs_check") or [])
                if isinstance(x, dict)}
        est = set((obj or {}).get("established") or [])
        allids = {c.get("candidate_id") for c in v["候補"]}
        good = allids - bad
        # ★機械が 落とした分は ★機械の 検出として 数える(★LLM の 手柄に しない)
        machine_caught = bad if P.R1_AUDITOR.count("%s") == 1 else set()
        caught = (bad & need) | machine_caught
        false_alarm = good & need
        tot["bad"] += len(bad); tot["caught"] += len(caught)
        tot["good"] += len(good); tot["false_alarm"] += len(false_alarm)
        out[tid] = {"候補": len(allids), "機械が悪いと判った": sorted(bad),
                    "監査が要確認にした": sorted(need), "監査が成立とした": sorted(est),
                    "検出": sorted(caught), "誤警報": sorted(false_alarm),
                    "json取れた": obj is not None, "秒": round(time.perf_counter() - t0, 1)}
        if bad or false_alarm:
            print("  %-24s 悪い%d 検出%d 誤警報%d %s" % (
                tid, len(bad), len(caught), len(false_alarm),
                "" if obj is not None else "★JSON 取れず"))
    json.dump(out, open(os.path.join(D, "a1_%s.json" % ver), "w"), ensure_ascii=False)
    print("\n★AUDIT 1 %s (分母 %d TASK)" % (ver, len(out)))
    print("   ★どこが 見たか: %s" % ("機械=文字照合 / LLM=意味の3点" if P.R1_AUDITOR.count("%s") == 1 else "LLM=4点 まとめて"))
    print("   ★AUDIT CATCH RATE : %d/%d = %s" % (
        tot["caught"], tot["bad"],
        ("%.0f%%" % (100.0 * tot["caught"] / tot["bad"])) if tot["bad"] else "★分母0(悪い候補が無い)"))
    print("   ★誤警報(良いのに要確認): %d/%d = %.0f%%" % (
        tot["false_alarm"], tot["good"], 100.0 * tot["false_alarm"] / tot["good"] if tot["good"] else 0))
    print("   JSON 取れた: %d/%d" % (sum(1 for v in out.values() if v["json取れた"]), len(out)))


if __name__ == "__main__":
    main(sys.argv[1:])
