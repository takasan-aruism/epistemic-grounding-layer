"""Curator Gates 0-3 [code] + Decision Table + Gate 5 apply。
Gate 4 は judge.py(Claude-in-loop)。CU-1: LLM は DB write 権限を持たない
→ 本モジュール(コード)のみが受理を書く。
"""
from . import core

# ---------- Coverage Profile registry(CP-1: RD の ad hoc 定義を禁止) ----------
COVERAGE_PROFILES = {
    "COV-TECH-STANDARD": {
        "required_source_kinds": ["official_documentation", "release_notes", "official_repository"],
        "required_languages": ["en"],
        "min_query_variants": 3,
    }
}


def evaluate_coverage(profile_id, checked_kinds, incomplete_reason=None):
    """SearchConclusion の COMPLETED 可否を coverage で決める。
    checked_kinds = *成功裏に* 確認できた source kind。失敗 leg の kind は含めない
    → unchecked に落ち SEARCH_INCOMPLETE(SC-1)。「検索失敗」と「coverage 欠落」を同機構で扱う。"""
    prof = COVERAGE_PROFILES[profile_id]
    req = set(prof["required_source_kinds"])
    unchecked = sorted(req - set(checked_kinds))
    ok = not unchecked
    result = {"required_domains_checked": ok, "unchecked": unchecked,
              "languages_covered": prof["required_languages"], "languages_uncovered": []}
    status = "COMPLETED" if ok else "SEARCH_INCOMPLETE"
    if not ok and incomplete_reason:
        result["incomplete_reason"] = incomplete_reason
    return status, result

# ---------- Gate 0: schema ----------
REQUIRED = ["id", "object_kind", "claim_type", "statement", "scope",
            "evidence_relations", "resolves_gap"]

def gate0_schema(candidate):
    missing = [k for k in REQUIRED if k not in candidate]
    return (not missing, f"missing:{missing}" if missing else "ok")


# ---------- Gate 1: evidence integrity + taint (GC-1/GC-4/GC-8) ----------
def gate1_evidence(con, candidate):
    rels = candidate.get("evidence_relations", [])
    if candidate.get("polarity") != "ABSENCE" and not rels:
        return False, "GC-1: FACT-class claim has empty grounds"
    kinds, tainted = [], False
    for rid in rels:
        rel = core.get(con, rid)
        if not rel:
            return False, f"GC-4: dangling relation {rid}"
        frag = core.get(con, rel["from_id"])
        if not frag:
            return False, f"GC-4: dangling fragment {rel['from_id']}"
        src = core.get(con, core.get(con, frag["norm_obs_id"])["source_id"])
        kinds.append(src["source_class"])
        if frag.get("taint_flags"):
            tainted = True
    if rels and all(k == "GENERATED" for k in kinds):
        return False, "source: GENERATED-only grounds forbidden"
    if tainted:
        return False, "GC-8: taint-only grounds need explicit Curator clearance"
    return True, "ok"


# ---------- Gate 2: dedup / conflict candidates (full scan CS-1, no vector) ----------
def gate2_candidates(con, candidate):
    ck = core.claim_key(candidate)
    same = [c for c in core.by_type(con, "Claim") if core.claim_key(c) == ck]
    return {"claim_key": ck, "dup_conflict_candidate_ids": [c["id"] for c in same]}


# ---------- Gate 3: authority + coverage (ABSENCE→SC-2) ----------
def gate3_authority(con, candidate):
    if candidate.get("polarity") == "ABSENCE":
        scon = core.get(con, candidate.get("search_conclusion"))
        if not scon or scon.get("status") != "COMPLETED" or scon.get("outcome") != "NO_POSITIVE_EVIDENCE":
            return False, "SC-2: ABSENCE requires COMPLETED conclusion w/ NO_POSITIVE_EVIDENCE"
    return True, "ok"


# ---------- Decision Table (Gate 5 判定) ----------
# FI-6: finding の個数でなく必要 family の充足で判定。AM-11: 不能→EVIDENCE_INSUFFICIENT。
def decide(finding, gate2, importance):
    if not finding.fragment_sufficient:                       # EI-6
        return "EVIDENCE_INSUFFICIENT", "judge: fragment insufficient"
    if finding.f1_entailment in ("UNJUDGEABLE",) or finding.f2_scope in ("UNRESOLVED",):
        return "EVIDENCE_INSUFFICIENT", "judge: unjudgeable/unresolved (AM-11)"
    if finding.f1_entailment == "CONTRADICTS":
        return "REJECT_CONTRADICTED", "evidence contradicts statement"
    if finding.f2_scope == "EXCEEDS":                         # SN-4: 自動縮小せず差し戻し
        return "SCOPE_REDUCTION_REQUIRED", "scope exceeds evidence; RD must re-scope (SN-4)"
    if finding.f1_entailment in ("SUPPORTED", "PARTIAL") and finding.f2_scope in ("WITHIN", "NARROWER"):
        return "ACCEPT", f"supported within scope (f1={finding.f1_entailment})"
    return "EVIDENCE_INSUFFICIENT", f"not supported (f1={finding.f1_entailment})"


# ---------- GC-7: representation residual protection (assertion lint) ----------
def gc7_lint(con, assertion, ground_claim):
    """FACT assertion が grounds claim の known_omissions 次元へ新事実を足していないか。
    scope_echo の次元キー ∩ known_omissions ≠ ∅ かつ その次元を支持する別 grounds が無ければ error。"""
    omit = set(ground_claim.get("representation_residual", {}).get("known_omissions", []))
    echo = set(assertion.get("scope_echo", {}).keys()) | set(assertion.get("residual_ack", []))
    hit = omit & echo
    if hit:
        return False, f"GC-7: asserts on omitted dimension(s) {sorted(hit)} with no supporting ground"
    return True, "ok"
