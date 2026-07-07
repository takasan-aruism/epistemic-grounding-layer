"""2DER Meta-Frame Factory — schemas + deterministic gates (spec v0.3 §7/§10/§17/§29).

DD-ARCH-6: META_FRAME owner + currentness authority = EGL。RRI が applies、DW が experiments、
DS が reactivates、Director が routes。Meta-Frame Factory は pipeline role であって第5責任系ではない。
これは derived pipeline の構造 gate 群であって、admission(=EGL)や application(=RRI)を代行しない。
deterministic gate は source-span / eligibility / lineage / origin を強制する。semantic structural
similarity は保証しない(§29: overclaim しない)。
"""
import re

# §5 origin classes(human-origin laundering を防ぐ mandatory separation)
ORIGINS = {"HUMAN_LESSON", "CORPUS_EXTRACTION", "DERIVED_FROM_INCIDENT",
           "INDUCED_FROM_INCIDENT_CLUSTER", "HUMAN_REVISED", "SYSTEM_REVISION_CANDIDATE"}
# §20.1 lifecycle statuses
STATUSES = {"CANDIDATE", "PROVISIONAL", "CURRENT", "REVIEW_REQUIRED", "SUPERSEDED", "REJECTED", "DEPRECATED"}
FIELD_SUPPORT = {"EXPLICIT", "INFERRED", "UNRESOLVED"}
EXTRACTION_STATUS = {"CANDIDATE", "VERIFIED", "PARTIAL", "REJECTED"}
INELIGIBLE = {"LESSON_ONLY", "OBSERVATION_ONLY", "STATUS_ONLY", "SPECIFICATION_ONLY", "INSUFFICIENT_CAUSAL_TRACE"}
DECISION_EFFECT = {"REVERSED", "NARROWED", "EXPANDED", "REDIRECTED", "NO_CHANGE"}
CORPUS_TIERS = {"TIER_1_RETROSPECTIVE_CORPUS", "TIER_2_PRIMITIVE_INCIDENT_CORPUS"}
PRE_FRAME_FIDELITY = {"RETROSPECTIVE_RECONSTRUCTION", "PRIMITIVE_CROSS_GROUNDED"}
# §8 causal-shape load-bearing fields that require source support (§9)
LOAD_BEARING = ["observation", "initial_interpretation", "tension_or_failure", "intervention",
                "post_intervention_test_or_action", "outcome"]
# §18 generic-virtue rejection cues(applicability structure が無ければ meta-frame でない)
_GENERIC = re.compile(r"(be skeptical|懐疑|check assumptions|仮定を確認|look for other|別の可能性|"
                      r"think from another angle|別の角度|do more research|もっと調査|avoid bias|バイアス)", re.I)


# ── §7/§8/§9 INCIDENT_FRAME ────────────────────────────────────────────────────
def validate_incident(inc):
    """source-span 完全性 + eligibility + field_support enum。extraction が verified 化する前の構造 gate。
    返り {valid, eligible, problems}。causal-trace 不足は eligible=False(INELIGIBLE 分類が要る)。"""
    if not isinstance(inc, dict):
        return {"valid": False, "eligible": False, "problems": ["incident is not a dict (fail-closed)"]}
    p = []
    if inc.get("origin") != "CORPUS_EXTRACTION":
        p.append(f"INCIDENT_FRAME origin must be CORPUS_EXTRACTION (got {inc.get('origin')!r})")
    if not inc.get("incident_id") or not inc.get("source_document"):
        p.append("incident_id + source_document required")
    if not inc.get("source_span_refs"):
        p.append("source_span_refs required (§9: no unsupported chronology)")
    fs = inc.get("field_support") or {}
    for f in ("observation", "initial_interpretation", "tension_or_failure", "intervention", "outcome"):
        if fs.get(f) not in FIELD_SUPPORT:
            p.append(f"field_support.{f} must be EXPLICIT|INFERRED|UNRESOLVED")
    # §8 eligibility: needs A observation + B interpretation + C tension + D added-frame + E outcome/claim-change
    has_added = bool(inc.get("added_dimensions") or inc.get("added_distinctions") or inc.get("added_operations"))
    eligible = bool(inc.get("observation") and inc.get("initial_interpretation") and inc.get("tension_or_failure")
                    and has_added and (inc.get("outcome") or inc.get("claim_after")))
    if inc.get("extraction_status") not in EXTRACTION_STATUS:
        p.append("extraction_status must be CANDIDATE|VERIFIED|PARTIAL|REJECTED")
    # INFERRED load-bearing fields require an inference basis (§9)
    for f in LOAD_BEARING:
        if fs.get(f) == "INFERRED" and not (inc.get("inference_basis") or {}).get(f):
            p.append(f"{f}=INFERRED requires inference_basis.{f} (span refs + inference statement)")
    if inc.get("corpus_tier") not in CORPUS_TIERS:
        p.append("corpus_tier required (TIER_1/TIER_2)")
    if inc.get("corpus_tier") == "TIER_1_RETROSPECTIVE_CORPUS" and inc.get("pre_frame_fidelity") not in PRE_FRAME_FIDELITY:
        p.append("TIER_1 incident requires pre_frame_fidelity (§9.1: retrospective limitation)")
    return {"valid": not p, "eligible": eligible, "problems": p}


# ── §10 FRAME_DELTA(verified incident のみ)──────────────────────────────────
def validate_frame_delta(fd, verified_incident_ids):
    if not isinstance(fd, dict):
        return {"valid": False, "problems": ["frame_delta not a dict (fail-closed)"]}
    p = []
    if fd.get("origin") != "DERIVED_FROM_INCIDENT":
        p.append("FRAME_DELTA origin must be DERIVED_FROM_INCIDENT")
    inc = fd.get("incident_id")
    if inc not in set(verified_incident_ids):
        p.append(f"FRAME_DELTA incident_id {inc!r} must reference a VERIFIED incident (§10)")
    if fd.get("decision_effect") not in DECISION_EFFECT:
        p.append("decision_effect must be REVERSED|NARROWED|EXPANDED|REDIRECTED|NO_CHANGE")
    pre, post = fd.get("pre_frame") or {}, fd.get("post_frame") or {}
    if not (post.get("added_variables") or post.get("added_distinctions") or post.get("added_operations")):
        p.append("post_frame must add at least one variable/distinction/operation")
    return {"valid": not p, "problems": p}


# ── §17/§18 META_FRAME_CANDIDATE ──────────────────────────────────────────────
def validate_meta_frame(mf, verified_incident_ids, frame_delta_ids, existing_human_heuristics=None):
    """§18: >=3 verified incidents / materially different surfaces / applicability predicate with a
    disqualifying condition / not a generic virtue / not a duplicate heuristic. §17 origin/status。"""
    if not isinstance(mf, dict):
        return {"valid": False, "problems": ["meta_frame not a dict (fail-closed)"]}
    p = []
    if mf.get("origin") != "INDUCED_FROM_INCIDENT_CLUSTER":
        p.append("META_FRAME origin must be INDUCED_FROM_INCIDENT_CLUSTER (no human-origin laundering §5)")
    if mf.get("status", "CANDIDATE") not in STATUSES:
        p.append("status must be a lifecycle status")
    inc = mf.get("derived_from_incidents") or []
    if len([i for i in inc if i in set(verified_incident_ids)]) < 3:
        p.append("meta-frame requires >= 3 VERIFIED incidents (§18)")
    fds = mf.get("source_frame_delta_refs") or []
    if not fds or any(f not in set(frame_delta_ids) for f in fds):
        p.append("source_frame_delta_refs must all reference existing FRAME_DELTA (§18/§29)")
    ap = mf.get("applicability_predicate") or {}
    if not ap.get("required_conditions"):
        p.append("applicability_predicate.required_conditions required")
    if not ap.get("disqualifying_conditions") and not mf.get("non_applicable_cases"):
        p.append("at least one disqualifying/non-applicable condition required (§18)")
    # §18/§28 MF-R4: reject generic virtues unless structural specifics present
    blob = " ".join(str(mf.get(k, "")) for k in ("name", "shared_frame_delta", "shared_missing_dimension_shape"))
    specifics = bool(ap.get("required_conditions") and mf.get("suggested_axes") and
                     (ap.get("disqualifying_conditions") or mf.get("non_applicable_cases")))
    if _GENERIC.search(blob) and not specifics:
        p.append("MF-R4: generic intellectual virtue without structural precondition/axis/disqualifier")
    # MF-R9 duplicate heuristic
    for h in (existing_human_heuristics or []):
        if h and h.lower() in blob.lower():
            p.append(f"MF-R9: duplicates existing human heuristic {h!r}")
    return {"valid": not p, "problems": p}


# ── PHASE 0: verification trust root(手書き VERIFIED list 禁止)──────────────
# incident candidate → deterministic gate PASS → external audit VERIFIED → VERIFICATION_RECORD。
# inducer / validate_meta_frame は VERIFICATION_RECORD だけを信頼根にする(self-report id-list を根にしない)。
AUDIT_DISPOSITIONS = {"VERIFIED", "PARTIAL", "REJECTED"}


def validate_verification_record(rec):
    """VERIFICATION_RECORD の妥当性。gate_pass=True かつ external audit=VERIFIED かつ auditor 明示。"""
    if not isinstance(rec, dict):
        return {"valid": False, "problems": ["record not a dict"]}
    p = []
    if not rec.get("incident_id"):
        p.append("incident_id required")
    if rec.get("gate_pass") is not True:
        p.append("gate_pass must be True (deterministic gate PASS 必須)")
    if rec.get("audit_disposition") not in AUDIT_DISPOSITIONS:
        p.append("audit_disposition must be VERIFIED|PARTIAL|REJECTED")
    if rec.get("audit_disposition") == "VERIFIED" and not rec.get("auditor"):
        p.append("VERIFIED requires an explicit auditor (external weight)")
    return {"valid": not p, "problems": p}


def load_valid_verified_ids(records):
    """current valid VERIFICATION_RECORD を持ち audit_disposition=VERIFIED な incident id 集合。
    これが induction / validate_meta_frame の唯一の verified 根。手書き list は使わない。"""
    ok = set()
    for r in records:
        v = validate_verification_record(r)
        if v["valid"] and r.get("status", "VALID") == "VALID" and r.get("audit_disposition") == "VERIFIED":
            ok.add(r["incident_id"])
    return ok


def meta_frame_verification_ok(mf, records):
    """§ trust-root: meta-frame の全 source incident が current valid verification record を持つこと。"""
    vids = load_valid_verified_ids(records)
    missing = [i for i in (mf.get("derived_from_incidents") or []) if i not in vids]
    return {"ok": not missing, "unverified_source_incidents": missing}


# ── §20.2/§29 version lineage + currentness uniqueness ────────────────────────
def validate_version_lineage(versions):
    """meta_frame_id ごとに CURRENT は高々1、append-only、supersedes/superseded_by 整合。§29。"""
    p, by_id = [], {}
    for v in versions:
        by_id.setdefault(v.get("meta_frame_id"), []).append(v)
    for mid, vs in by_id.items():
        cur = [v for v in vs if v.get("status") == "CURRENT"]
        if len(cur) > 1:
            p.append(f"{mid}: more than one CURRENT version (§29 uniqueness)")
        vnums = [v.get("version") for v in vs]
        if len(vnums) != len(set(vnums)):
            p.append(f"{mid}: duplicate version numbers (append-only violated)")
        for v in vs:
            sb = v.get("superseded_by_version")
            if v.get("status") == "SUPERSEDED" and sb is None:
                p.append(f"{mid} v{v.get('version')}: SUPERSEDED requires superseded_by_version")
    return {"valid": not p, "problems": p}
