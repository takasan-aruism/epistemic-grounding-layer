"""Walking skeleton orchestration: Gap → SearchPlan → SearchRun → Observation →
Fragment → CandidateClaim → Gate0-3(code) → Gate4(Claude) → Gate5 apply。

差別化機構を必ず通す: EVIDENCE_INSUFFICIENT / gap 残存 / required-gap による SOLVED 封鎖(DF-4)。
"""
from . import core, gates, judge


# ---------- constructors (すべて OM-2: run_id を刻む) ----------
def mk_source(run, name, source_class, locator):
    # DE-0006: id は append 内で採番。SELF 番兵で自己 alias(source_id)も同一 event に。
    return core.append_event(run, "CREATE", "Source", None,
                             {"id": core.SELF, "source_id": core.SELF, "name": name,
                              "source_class": source_class, "locator": locator},
                             new_prefix="SRC")

def mk_observation(run, source_id, section_heading, blocks):
    oid = core.append_event(run, "CREATE", "RawObservation", None,
                            {"id": core.SELF, "source_id": source_id,
                             "acquired_by_run": run, "taint_flags": []}, new_prefix="OBS")
    return core.append_event(run, "CREATE", "NormalizedObservation", None,
                             {"id": core.SELF, "norm_obs_id": core.SELF, "raw_observation_id": oid,
                              "source_id": source_id, "section_heading": section_heading,
                              "blocks": blocks, "normalized_by_run": run}, new_prefix="NOBS")

def mk_fragment(run, norm_obs_id, block_index, excerpt, mentions=None, taint=None):
    return core.append_event(run, "CREATE", "EvidenceFragment", None,
                             {"id": core.SELF, "fragment_id": core.SELF, "norm_obs_id": norm_obs_id,
                              "block_index": block_index, "excerpt": excerpt,
                              "extracted_by_run": run, "extraction_method": "llm",
                              "mentions_entities": mentions or [], "taint_flags": taint or []},
                             new_prefix="EFRAG")

def mk_relation(run, from_frag, to_candidate, rel_type, context):
    # to_id は back-ref(candidate)。gate1/build_packet は candidate 起点で辿るため未読=vestigial。
    # id-in-append の相互参照 cycle を断つため、candidate 生成前に to_candidate=None で先行生成できる。
    return core.append_event(run, "CREATE", "Relation", None,
                             {"id": core.SELF, "from_id": from_frag, "to_id": to_candidate,
                              "relation_type": rel_type, "context": context, "created_by_run": run},
                             new_prefix="REL")

def mk_candidate(run, payload):
    """CandidateClaim を作り、その evidence_relations の to_id を完結 event で結線する(AB-0007)。
    relation は id-in-append の cycle 回避で to_id=None 先行生成される → candidate 確定後にここで
    COMPLETION により結線し、恒久 null link を残さない(OM-3)。seam-6(write surface 統一)の芽。"""
    payload = dict(payload)
    payload["id"] = core.SELF
    cid = core.append_event(run, "CREATE", "CandidateClaim", None, payload, new_prefix="CC")
    for rid in payload.get("evidence_relations", []):
        core.complete_object(run, "Relation", rid, {"to_id": cid},
                             reason="candidate 確定に伴う link 結線 (AB-0007)")
    return cid


def mk_gap(run, question, required_for, profile):
    return core.append_event(run, "CREATE", "KnowledgeGap", None,
                             {"id": core.SELF, "gap_id": core.SELF, "question": question,
                              "required_for": required_for, "status": "OPEN",
                              "epistemic_profile_id": profile, "created_by_run": run},
                             new_prefix="KGAP")

def mk_search_plan(run, gap_id, coverage_profile):
    return core.append_event(run, "CREATE", "SearchPlan", None,
                             {"id": core.SELF, "gap_id": gap_id,
                              "coverage_profile_id": coverage_profile}, new_prefix="SPLAN")

def mk_search_leg(task_id, plan_id, source_kind, simulate_fail=False):
    """必須 source kind ごとの SearchRun。timeout 模擬で FAILED に落とせる(SC-2 負性試験用)。

    H1(SC-2 enforce): leg の (plan_id, source_kind) を **event payload に記録** する。
    これが無いと gate3 は coverage を leg event から再導出できず、driver が渡す
    SearchConclusion.status を信用するしかない(= DE-0005 の wrong-source 欠陥)。
    """
    rid = core.run_start("rd", "SEARCH", task_id=task_id, inputs=[plan_id])
    status = "FAILED" if simulate_fail else "COMPLETED"   # FAILED=RATE_LIMITED/timeout 相当
    # M4: leg 情報 + lifecycle を1つの完全 revision で書く(gate3 が再導出の一次資料に使う)
    st = core.get_state(rid)
    st.update({"leg_plan_id": plan_id, "source_kind": source_kind,
               "outputs": [], "status": status, "ended_at": core.now_iso()})
    core.append_event(rid, "UPDATE", "Run", rid, st)
    return rid, source_kind, status == "COMPLETED"


def mk_search_conclusion(run, plan_id, status, outcome, coverage_result=None):
    return core.append_event(run, "CREATE", "SearchConclusion", None,
                             {"id": core.SELF, "search_plan_id": plan_id, "status": status,
                              "outcome": outcome, "coverage_result": coverage_result,
                              "concluded_at": core.now_iso()}, new_prefix="SCON")


# ---------- Gate 5: apply outcome (CU-1: code のみが write) ----------
def apply_outcome(run, candidate, outcome, reason, finding, gate2):
    dec_id = core.append_event(run, "DECISION", "CuratorDecision", None,
                               {"id": core.SELF, "about": candidate["id"], "outcome": outcome,
                                "reason": reason, "finding": finding.as_dict() if finding else None,
                                "claim_key": gate2["claim_key"], "decided_by_run": run,
                                "decision_table_version": "DT-1a.0"}, new_prefix="CDEC")  # DT-1
    result = {"decision_id": dec_id, "outcome": outcome, "reason": reason}

    if outcome == "ACCEPT":
        st = dict(candidate)
        # AB-0003: bootstrap を一律 True にしない。bootstrap = 「teacher signal(Gate4 Claude,
        # CB-5)由来で受理された」= 導出値。ABSENCE は adjudicator を持たず coverage 由来なので
        # bootstrap ではない → benchmark B(自律化原料)への混入を防ぐ(data-integrity)。
        bootstrap = bool(finding and getattr(finding, "teacher_signal", False))
        con_v = core.build_view()
        if candidate.get("polarity") == "ABSENCE":       # NOT_FOUND + AB-3 短TTL
            # R5: ABSENCE は通常の validation_mode を持たず、別軸 absence_validation を持つ
            #     (SPECIFIED=公式規定の不在 との再混同を避ける)。
            st.update({"id": core.SELF, "claim_id": core.SELF, "object_kind": "Claim", "claim_type": "ABSENCE",
                       "status": "NOT_FOUND",
                       "absence_validation": gates.derive_absence_validation(con_v, candidate), "revision": 1,
                       "origin_candidate": candidate["id"], "bootstrap": bootstrap,
                       "volatility_class": "ABSENCE_VOLATILE",
                       "temporal": {"observation_time": core.now_iso(),
                                    "knowledge_time": core.now_iso(),
                                    "valid_until": core.plus_days(14),   # AB-3: 短TTL
                                    "last_verified": core.now_iso()},
                       "promoted_by_run": run})
        else:
            # L4: validation_mode は provenance 導出(既定値を捏造しない)。導出不能=UNRESOLVED。
            st.update({"id": core.SELF, "claim_id": core.SELF, "object_kind": "Claim",
                       "status": "VERIFIED" if finding.f1_entailment == "SUPPORTED" else "REPORTED",
                       "validation_mode": gates.derive_validation_mode(con_v, candidate),
                       "revision": 1, "origin_candidate": candidate["id"],
                       "bootstrap": bootstrap, "promoted_by_run": run})
        cid = core.append_event(run, "CREATE", "Claim", None, st, new_prefix="C")
        result["global_claim"] = cid

    elif outcome in ("EVIDENCE_INSUFFICIENT", "SCOPE_REDUCTION_REQUIRED",
                     "REJECT_CONTRADICTED"):
        # G4-7 / DF-3: required gap を OPEN へ戻し、追加調査の SearchPlan を添付
        gid = candidate.get("resolves_gap")
        if gid:
            g = core.get_state(gid)                        # M4: 完全 revision で再 OPEN
            g.update({"status": "OPEN", "last_insufficient_reason": reason})
            core.append_event(run, "UPDATE", "KnowledgeGap", gid, g)
            newplan = mk_search_plan(run, gid, "COV-TECH-STANDARD")
            p = core.get_state(newplan)                    # M4: 完全 revision で note 追記
            p["note"] = "stress/stability test required (evidence insufficient)"
            core.append_event(run, "UPDATE", "SearchPlan", newplan, p)
            result["reopened_gap"] = gid
            result["new_search_plan"] = newplan
    return result
