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
        # M3: nobs/source が dangling でも None 添字で crash せず clean-fail する
        nobs = core.get(con, frag.get("norm_obs_id"))
        if not nobs:
            return False, f"GC-4: dangling normalized observation {frag.get('norm_obs_id')}"
        src = core.get(con, nobs.get("source_id"))
        if not src:
            return False, f"GC-4: dangling source {nobs.get('source_id')}"
        kinds.append(src["source_class"])
        if frag.get("taint_flags"):
            tainted = True
    if rels and all(k == "GENERATED" for k in kinds):
        return False, "source: GENERATED-only grounds forbidden"
    if tainted:
        return False, "GC-8: taint-only grounds need explicit Curator clearance"
    return True, "ok"


# ---------- validation_mode derivation (L4 / DE-0008, AM-15 F3a) ----------
def derive_validation_mode(con, candidate):
    """validation_mode を provenance からコード導出。導出不能なら UNRESOLVED。
    候補の *自己申告* validation_mode は用いない(L4: 『公式主体が宣言したと一次確認した』の
    無根拠メタデータ捏造=本系が殺す無根拠 claim のメタデータ版。既定値の存在自体が誤り)。
    - ABSENCE: SC-2 で coverage 完全性を leg event から再導出済 → 宣言済み profile 準拠が
      provenance-backed = SPECIFIED
    - POSITIVE: grounds を辿り一次資料(PRIMARY)の宣言に到達できれば DECLARED、
      さもなくば UNRESOLVED(再現/測定 mode は再現 run の provenance が要るが未モデル→導出不能)"""
    if candidate.get("polarity") == "ABSENCE":
        return "SPECIFIED"
    kinds = []
    for rid in candidate.get("evidence_relations", []):
        rel = core.get(con, rid)
        if not rel:
            continue
        frag = core.get(con, rel.get("from_id"))
        nobs = core.get(con, frag.get("norm_obs_id")) if frag else None
        src = core.get(con, nobs.get("source_id")) if nobs else None
        if src:
            kinds.append(src.get("source_class"))
    if kinds and any(k == "PRIMARY" for k in kinds) and all(k != "GENERATED" for k in kinds):
        return "DECLARED"
    return "UNRESOLVED"


# ---------- Gate 2: dedup / conflict candidates (full scan CS-1, no vector) ----------
def gate2_candidates(con, candidate):
    ck = core.claim_key(candidate)
    same = [c for c in core.by_type(con, "Claim") if core.claim_key(c) == ck]
    return {"claim_key": ck, "dup_conflict_candidate_ids": [c["id"] for c in same]}


# ---------- Gate 3: authority + coverage (ABSENCE→SC-2) ----------
def _derive_checked_kinds(con, plan_id):
    """H1: SearchConclusion.status を信用せず、leg event(SearchRun)から
    *COMPLETED* leg の source_kind を再収集する。これが SC-2 の一次資料。
    driver が渡した status/coverage_result は一切参照しない(wrong-source 防止)。"""
    checked = []
    for r in core.by_type(con, "Run"):
        if r.get("leg_plan_id") == plan_id and r.get("status") == "COMPLETED":
            checked.append(r["source_kind"])
    return checked


def gate3_authority(con, candidate):
    if candidate.get("polarity") == "ABSENCE":
        scon = core.get(con, candidate.get("search_conclusion"))
        if not scon:
            return False, "SC-2: ABSENCE requires a SearchConclusion"
        plan = core.get(con, scon.get("search_plan_id"))
        if not plan:
            return False, "SC-2: SearchConclusion references dangling SearchPlan"
        # coverage を leg event から再導出(scon.status は信用しない = H1 enforce)
        checked = _derive_checked_kinds(con, plan["id"])
        status, cov = evaluate_coverage(plan["coverage_profile_id"], checked)
        if status != "COMPLETED":
            return False, (f"SC-2: re-derived coverage={status} from legs "
                           f"(unchecked={cov['unchecked']}); ABSENCE forbidden")
        if scon.get("outcome") != "NO_POSITIVE_EVIDENCE":
            return False, "SC-2: ABSENCE requires NO_POSITIVE_EVIDENCE outcome"
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
    supported = (finding.f1_entailment in ("SUPPORTED", "PARTIAL")
                 and finding.f2_scope in ("WITHIN", "NARROWER"))
    if not supported:
        return "EVIDENCE_INSUFFICIENT", f"not supported (f1={finding.f1_entailment})"
    # H3: gate2(dedup 全走査 CS-1)を判定に効かせる。同 claim_key の既存 Claim があれば
    #     無条件 ACCEPT せず衝突解決へ回す(2つの矛盾 claim が両方 ACCEPT される穴を塞ぐ)。
    if gate2 and gate2.get("dup_conflict_candidate_ids"):
        return "CONFLICT_REVIEW_REQUIRED", (
            f"claim_key conflicts with existing {gate2['dup_conflict_candidate_ids']} "
            "(CS-1); resolve before accept")
    # H3/M5: importance=REQUIRED_FOR_RESOLUTION は審査バーを上げる(PARTIAL では必須 gap を埋めない)。
    if importance == "REQUIRED_FOR_RESOLUTION" and finding.f1_entailment != "SUPPORTED":
        return "EVIDENCE_INSUFFICIENT", (
            f"required-for-resolution needs SUPPORTED, got {finding.f1_entailment} (M5)")
    return "ACCEPT", f"supported within scope (f1={finding.f1_entailment})"


# ---------- GC-7: representation residual protection (assertion lint) ----------
def gc7_lint(con, assertion, ground_claim):
    """FACT assertion が grounds claim の known_omissions 次元へ新事実を足していないか。
    次元キー ∩ known_omissions ≠ ∅ かつ その次元を支持する別 grounds が無ければ error。

    H4: 「省略で素通り」を塞ぐため、self-report の scope_echo/residual_ack だけでなく
    assertion の *構造 scope キー* も asserted dimension として算入する。scope_echo を
    省いても、構造上その次元に踏み込んでいれば検出される(自己申告非依存)。"""
    omit = set(ground_claim.get("representation_residual", {}).get("known_omissions", []))
    echo = (set(assertion.get("scope_echo", {}).keys())
            | set(assertion.get("residual_ack", []))
            | set(assertion.get("scope", {}).keys()))
    hit = omit & echo
    if hit:
        return False, f"GC-7: asserts on omitted dimension(s) {sorted(hit)} with no supporting ground"
    return True, "ok"
