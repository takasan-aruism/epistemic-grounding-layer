"""PHASE-3 full-path dogfood trace: run ONE real problem through the ACTUAL existing 2DER
mechanisms (not the minimal handoff). Saves every stage IN/OUT/survived/dropped so we can judge
whether 2DER was actually used. NO capability claim; CLOSED-NEGATIVE mechanisms are run as-is
(they exist + run) but never relabeled positive. Read-only to SoR/DE. Requires vLLM :8005.
"""
import sys, os, json, datetime
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "experiments"))

FRAME = ("INCIDENT: 本番 LLM serving で、2 つの大型モデル(Qwen3.6-35B と Qwen3-Coder-Next-80B)が"
         "それぞれ両方の GPU を占有するため、両者を切り替えるたびにコンテナ再起動のコールドロードで"
         "実測 約174.5秒/回(rework 時は複数回で数分〜十数分)かかる。現状の枠組みは「動いているモデルを"
         "より速くスワップする」。目的は切替を実用速度にすること。この状況の詰まりの本質を特定し、"
         "必要なら別の実現の枠組みを再構成せよ。")


def stage(trace, name, inp, out, survived=None, dropped=None, why_next=None):
    trace["stages"].append({"stage": name, "input": inp, "output": out,
                            "survived": survived, "dropped": dropped, "why_next": why_next})


def main():
    trace = {"object": "DOGFOOD_FULLPATH_TRACE", "problem": FRAME,
             "as_of": datetime.datetime.now().isoformat(timespec="seconds"), "stages": []}

    # STAGE 1 — HISTORY (self_grounding retrieval over DE/REVIEW) — LIVE
    from egl.self_grounding import answer_question, validate_answer
    ans, rids, raw = answer_question(FRAME)
    claims = (ans or {}).get("answer_claims") or [] if isinstance(ans, dict) else []
    gaps = (ans or {}).get("open_gaps") or [] if isinstance(ans, dict) else []
    stage(trace, "HISTORY(self_grounding)", "problem frame",
          {"record_ids": rids, "claims": [c.get("text") for c in claims][:6], "open_gaps": gaps[:4]},
          survived=rids, why_next="feed grounded reality into detection")

    # STAGE 2 — DETECTION (AFE operator ensemble + skepticism) — EXHIBIT-ONLY, WEAK/NEGATIVE evidence, but RUNS
    import run_afe_walking as afe
    signals = [afe.run_operator(o, FRAME) for o in afe.ADMITTED]
    cands = afe.aggregate(signals)                       # dedup + support_count = what survived
    fec = afe.orchestrate(FRAME, cands)                  # <=3 missing dimensions/distinctions
    skeptic = afe.arm_ABE("B", FRAME)                    # strongest HBB detector
    n_sig = sum(1 for s in signals if s.get("verdict") == "SIGNAL")
    stage(trace, "DETECTION(AFE+skepticism)", f"{len(afe.ADMITTED)} operators on frame",
          {"detected_missing_dimensions": fec, "skeptic_checks": skeptic,
           "n_candidates": len(cands)},
          survived=[c.get("structure") for c in cands][:8],
          dropped=f"{len(signals)-n_sig} operators returned NO_SIGNAL",
          why_next="hand detected defects/missing axes to reconstruction")

    # STAGE 3 — RECONSTRUCTION (scheduler view->signature->compare->rebuild) — EXHIBIT-ONLY + CLOSED-NEGATIVE at HBB bar, but RUNS
    import run_scheduler_exhibit as sch
    rebuild, rtrace = sch.rs_run(FRAME, seed=0, V=3)
    stage(trace, "RECONSTRUCTION(scheduler rebuild)", "problem frame + detected differences",
          {"rebuild_alternative_frame": rebuild, "attempts": rtrace.get("attempts"),
           "resolved": rtrace.get("resolved")},
          survived="1 rebuild frame", why_next="compare against reality / propose next operation")

    out = os.path.join(REPO, "experiments", "dogfood_qwen_fullpath_trace.json")
    json.dump(trace, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"-> {out}\n")
    for s in trace["stages"]:
        print("=" * 70); print("STAGE:", s["stage"])
        o = s["output"]
        if s["stage"].startswith("HISTORY"):
            print("  retrieved:", o["record_ids"])
            for c in o["claims"][:3]: print("   • hist:", (c or "")[:150])
        elif s["stage"].startswith("DETECTION"):
            print("  detected missing dimensions (AFE orchestrate):")
            for d in (o["detected_missing_dimensions"] or [])[:3]:
                print("   •", json.dumps(d, ensure_ascii=False)[:200])
            print("  skeptic checks:", [str(x)[:80] for x in (o["skeptic_checks"] or [])][:3])
        elif s["stage"].startswith("RECONSTRUCTION"):
            print("  ALTERNATIVE FRAME (rebuild):")
            print("  ", (o["rebuild_alternative_frame"] or "")[:600])
            print("  resolved(changed subject/level/distinction?):", o["resolved"])


if __name__ == "__main__":
    main()
