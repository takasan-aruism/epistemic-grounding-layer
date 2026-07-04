"""Walking skeleton orchestration: Gap → SearchPlan → SearchRun → Observation →
Fragment → CandidateClaim → Gate0-3(code) → Gate4(Claude) → Gate5 apply。

差別化機構を必ず通す: EVIDENCE_INSUFFICIENT / gap 残存 / required-gap による SOLVED 封鎖(DF-4)。
"""
from . import core, gates, judge


# ---------- constructors (すべて OM-2: run_id を刻む) ----------
def mk_source(run, name, source_class, locator):
    sid = core.new_id("SRC")
    core.append_event(run, "CREATE", "Source", sid,
                      {"id": sid, "source_id": sid, "name": name,
                       "source_class": source_class, "locator": locator})
    return sid

def mk_observation(run, source_id, section_heading, blocks):
    oid = core.new_id("OBS"); nid = core.new_id("NOBS")
    core.append_event(run, "CREATE", "RawObservation", oid,
                      {"id": oid, "source_id": source_id, "acquired_by_run": run, "taint_flags": []})
    core.append_event(run, "CREATE", "NormalizedObservation", nid,
                      {"id": nid, "norm_obs_id": nid, "raw_observation_id": oid,
                       "source_id": source_id, "section_heading": section_heading,
                       "blocks": blocks, "normalized_by_run": run})
    return nid

def mk_fragment(run, norm_obs_id, block_index, excerpt, mentions=None, taint=None):
    fid = core.new_id("EFRAG")
    core.append_event(run, "CREATE", "EvidenceFragment", fid,
                      {"id": fid, "fragment_id": fid, "norm_obs_id": norm_obs_id,
                       "block_index": block_index, "excerpt": excerpt,
                       "extracted_by_run": run, "extraction_method": "llm",
                       "mentions_entities": mentions or [], "taint_flags": taint or []})
    return fid

def mk_relation(run, from_frag, to_candidate, rel_type, context):
    rid = core.new_id("REL")
    core.append_event(run, "CREATE", "Relation", rid,
                      {"id": rid, "from_id": from_frag, "to_id": to_candidate,
                       "relation_type": rel_type, "context": context, "created_by_run": run})
    return rid

def mk_gap(run, question, required_for, profile):
    gid = core.new_id("KGAP")
    core.append_event(run, "CREATE", "KnowledgeGap", gid,
                      {"id": gid, "gap_id": gid, "question": question,
                       "required_for": required_for, "status": "OPEN",
                       "epistemic_profile_id": profile, "created_by_run": run})
    return gid

def mk_search_plan(run, gap_id, coverage_profile):
    pid = core.new_id("SPLAN")
    core.append_event(run, "CREATE", "SearchPlan", pid,
                      {"id": pid, "gap_id": gap_id, "coverage_profile_id": coverage_profile})
    return pid

def mk_search_leg(task_id, plan_id, source_kind, simulate_fail=False):
    """必須 source kind ごとの SearchRun。timeout 模擬で FAILED に落とせる(SC-2 負性試験用)。

    H1(SC-2 enforce): leg の (plan_id, source_kind) を **event payload に記録** する。
    これが無いと gate3 は coverage を leg event から再導出できず、driver が渡す
    SearchConclusion.status を信用するしかない(= DE-0005 の wrong-source 欠陥)。
    """
    rid = core.run_start("rd", "SEARCH", task_id=task_id, inputs=[plan_id])
    # SoR に leg の意味的結果を刻む(gate3 が再導出の一次資料に使う)
    core.append_event(rid, "UPDATE", "Run", rid,
                      {"leg_plan_id": plan_id, "source_kind": source_kind})
    status = "FAILED" if simulate_fail else "COMPLETED"   # FAILED=RATE_LIMITED/timeout 相当
    core.run_end(rid, [], status=status)
    return rid, source_kind, status == "COMPLETED"


def mk_search_conclusion(run, plan_id, status, outcome, coverage_result=None):
    cid = core.new_id("SCON")
    core.append_event(run, "CREATE", "SearchConclusion", cid,
                      {"id": cid, "search_plan_id": plan_id, "status": status,
                       "outcome": outcome, "coverage_result": coverage_result,
                       "concluded_at": core.now_iso()})
    return cid


# ---------- Gate 5: apply outcome (CU-1: code のみが write) ----------
def apply_outcome(run, candidate, outcome, reason, finding, gate2):
    dec_id = core.new_id("CDEC")
    core.append_event(run, "DECISION", "CuratorDecision", dec_id,
                      {"id": dec_id, "about": candidate["id"], "outcome": outcome,
                       "reason": reason, "finding": finding.as_dict() if finding else None,
                       "claim_key": gate2["claim_key"], "decided_by_run": run,
                       "decision_table_version": "DT-1a.0"})  # DT-1
    result = {"decision_id": dec_id, "outcome": outcome, "reason": reason}

    if outcome == "ACCEPT":
        cid = core.new_id("C")
        st = dict(candidate)
        # AB-0003: bootstrap を一律 True にしない。bootstrap = 「teacher signal(Gate4 Claude,
        # CB-5)由来で受理された」= 導出値。ABSENCE は adjudicator を持たず coverage 由来なので
        # bootstrap ではない → benchmark B(自律化原料)への混入を防ぐ(data-integrity)。
        bootstrap = bool(finding and getattr(finding, "teacher_signal", False))
        if candidate.get("polarity") == "ABSENCE":       # NOT_FOUND + AB-3 短TTL
            st.update({"id": cid, "claim_id": cid, "object_kind": "Claim", "claim_type": "ABSENCE",
                       "status": "NOT_FOUND", "validation_mode": "SPECIFIED", "revision": 1,
                       "origin_candidate": candidate["id"], "bootstrap": bootstrap,
                       "volatility_class": "ABSENCE_VOLATILE",
                       "temporal": {"observation_time": core.now_iso(),
                                    "knowledge_time": core.now_iso(),
                                    "valid_until": core.plus_days(14),   # AB-3: 短TTL
                                    "last_verified": core.now_iso()},
                       "promoted_by_run": run})
        else:
            st.update({"id": cid, "claim_id": cid, "object_kind": "Claim",
                       "status": "VERIFIED" if finding.f1_entailment == "SUPPORTED" else "REPORTED",
                       "validation_mode": candidate.get("validation_mode", "DECLARED"),
                       "revision": 1, "origin_candidate": candidate["id"],
                       "bootstrap": bootstrap, "promoted_by_run": run})
        core.append_event(run, "CREATE", "Claim", cid, st)
        result["global_claim"] = cid

    elif outcome in ("EVIDENCE_INSUFFICIENT", "SCOPE_REDUCTION_REQUIRED",
                     "REJECT_CONTRADICTED"):
        # G4-7 / DF-3: required gap を OPEN へ戻し、追加調査の SearchPlan を添付
        gid = candidate.get("resolves_gap")
        if gid:
            core.append_event(run, "UPDATE", "KnowledgeGap", gid,
                              {"status": "OPEN", "last_insufficient_reason": reason})
            newplan = mk_search_plan(run, gid, "COV-TECH-STANDARD")
            core.append_event(run, "UPDATE", "SearchPlan", newplan,
                              {"note": "stress/stability test required (evidence insufficient)"})
            result["reopened_gap"] = gid
            result["new_search_plan"] = newplan
    return result
