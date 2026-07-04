"""共通 curate 境界(2本の slice が使う。(a) component 分解の芽)。
Gate 0-3[code] → Gate 4[Claude, positive のみ] → Decision Table → Gate 5 apply。
ABSENCE は Gate4 を持たない(entailment 対象の fragment が無い)。
SC-2(COMPLETED からのみ ABSENCE)を Gate3 が担い、失敗すれば『偽の不在』を構造ブロック。
"""
from . import core, gates, judge, pipeline as P


def _importance(con, cand):
    g = cand.get("resolves_gap")
    if g and core.get(con, g) and core.get(con, g).get("required_for"):
        return "REQUIRED_FOR_RESOLUTION"
    return "SUPPORTING"


def _block(run, cand, gate2, outcome, reason):
    dec = core.new_id("CDEC")
    core.append_event(run, "DECISION", "CuratorDecision", dec,
                      {"id": dec, "about": cand["id"], "outcome": outcome, "reason": reason,
                       "finding": None, "claim_key": gate2.get("claim_key"),
                       "decided_by_run": run, "decision_table_version": "DT-1a.0"})
    core.run_end(run, [dec], "COMPLETED")
    return {"outcome": outcome, "reason": reason, "decision_id": dec}


def curate(candidate_id, adjudicator=None, log=lambda *_: None):
    con = core.build_view()
    cand = core.get(con, candidate_id)
    run = core.run_start("curator", "CURATION", task_id=cand.get("task_id"))
    is_absence = cand.get("polarity") == "ABSENCE"

    ok, msg = gates.gate0_schema(cand)
    if not ok:
        log(f"        Gate0 FAIL {msg}"); return _block(run, cand, {}, "DEFER", msg)
    ok, msg = gates.gate1_evidence(con, cand)
    if not ok:
        log(f"        Gate1 FAIL {msg}"); return _block(run, cand, {}, "DEFER", msg)
    g2 = gates.gate2_candidates(con, cand)
    ok, msg = gates.gate3_authority(con, cand)
    if not ok:
        # ABSENCE なら SC-2 による『偽の不在』ブロック(通らない試験の本体)
        oc = "ABSENCE_BLOCKED_SC2" if is_absence else "GATE3_FAIL"
        log(f"        Gate3 FAIL → {oc}: {msg}")
        return _block(run, cand, g2, oc, msg)

    if is_absence:
        finding, outcome, reason = None, "ACCEPT", "ABSENCE via COMPLETED conclusion (SC-2 satisfied)"
        log(f"        Gate4: (ABSENCE — entailment 対象なし、SC-2 で成立)")
    else:
        packet = judge.build_packet(con, cand)                  # EI-3 bounded context
        finding = adjudicator.adjudicate(packet, common_run_id=run)  # Gate 4 (Claude)
        outcome, reason = gates.decide(finding, g2, _importance(con, cand))
        log(f"        Gate4(Claude): f1={finding.f1_entailment} f2={finding.f2_scope} "
            f"frag_sufficient={finding.fragment_sufficient}")

    res = P.apply_outcome(run, cand, outcome, reason, finding, g2)
    core.run_end(run, [res.get("global_claim") or res["decision_id"]])
    log(f"        → OUTCOME: {outcome}  ({reason})")
    if res.get("global_claim"):
        c = core.get(core.build_view(), res["global_claim"])
        extra = f"status={c['status']}"
        if is_absence:
            extra += f", valid_until={c['temporal']['valid_until'][:10]} (AB-3短TTL)"
        else:
            extra += f", residual={cand.get('representation_residual', {}).get('known_omissions')}"
        log(f"        → Global受理 {res['global_claim']} ({extra})")
    if res.get("reopened_gap"):
        log(f"        → gap {res['reopened_gap']} 差し戻し / 追加 {res['new_search_plan']}")
    return res
