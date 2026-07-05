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
            "evidence_relations", "resolves_gap", "polarity"]
POLARITY_VALUES = {"POSITIVE", "NEGATIVE", "ABSENCE"}   # F/JREV-0003: fail-open 封鎖
# R7/DE-0029: 負の理由は mode でなく別軸で表現。NEGATIVE claim は negative_basis を要求。
NEGATIVE_BASIS_VALUES = {"EXPLICITLY_UNSUPPORTED", "SPEC_PROHIBITED",
                         "EMPIRICALLY_FAILED", "REPRODUCTION_FAILURE"}

def gate0_schema(candidate):
    missing = [k for k in REQUIRED if k not in candidate]
    if missing:
        return False, f"missing:{missing}"
    # F/JREV-0003: polarity を enum 検査。未知/typo/None を最特権分岐へ素通りさせない
    # (derive_validation_mode / apply_outcome が非 ABSENCE を positive 扱いするため上流で止める)
    pol = candidate.get("polarity")
    if pol not in POLARITY_VALUES:
        return False, f"invalid polarity {pol!r} (allowed={sorted(POLARITY_VALUES)})"
    # R7/DE-0029: NEGATIVE(明示的不支持)は negative_basis で理由を宣言(mode と直交)。
    if pol == "NEGATIVE":
        nb = candidate.get("negative_basis")
        if nb not in NEGATIVE_BASIS_VALUES:
            return False, f"R7: NEGATIVE requires negative_basis in {sorted(NEGATIVE_BASIS_VALUES)} (got {nb!r})"
    return True, "ok"


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

    R5(Taka 裁定): validation_mode は **positive/negative claim 専用**。
    R6/DE-0025(Phase 1a): source_class(権威次元)だけでは mode を決定できない。authentic な
    PRIMARY でも observation_kind(declaration/specification/measurement/reproduction)が別なら別 mode。
    ゆえに DECLARED/SPECIFIED は **PRIMARY かつ明示宣言/規定の観測** に限定し、それ以外は UNRESOLVED
    へ倒す(『無理に賢く導出しない』= measurement/reproduction からの MEASURED/REPRODUCED 導出は
    Activity/run type を要する Phase 1b/F3a 送り)。PRIMARY と declaration は **同一観測** で成立を要求
    (別 source の PRIMARY と別観測の DECLARATION を継ぎ合わせる gaming を封じる)。
    R7/DE-0029(Taka 裁定: R5『SPECIFIED=NEGATIVE 専用』を supersede): mode ⊥ polarity。
    - DECLARATION 観測(PRIMARY)→ DECLARED(polarity 不問。POSITIVE も NEGATIVE〈公式が非対応と宣言〉も)
    - SPECIFICATION 観測(PRIMARY)→ SPECIFIED(polarity 不問。仕様が許可も禁止も)
    - 負の理由(なぜ不支持か)は mode でなく candidate.negative_basis で表現(Gate0 が enum 検査)。
    - ABSENCE(調査完遂したが見つからない不在)は **この体系を使わない** → derive_absence_validation。
      SPECIFIED を ABSENCE に与えるのは NOT_FOUND と『公式仕様に規定された不在』の再混同(この系の
      第一日の禁忌)。polarity 層が既にこの区別を持つので mode 層で再融合させない。"""
    polarity = candidate.get("polarity")
    if polarity == "ABSENCE":
        raise ValueError("R5: ABSENCE は validation_mode を持たない。derive_absence_validation を使う")
    # F/JREV-0003: 未知/欠落/typo の polarity は POSITIVE→DECLARED 分岐へ倒さず fail-closed。
    # 『既定値の存在自体が誤り』の原則を polarity 層にも適用(Gate0 が上流で弾くが二重防御)。
    if polarity not in ("POSITIVE", "NEGATIVE"):
        return "UNRESOLVED"
    # R8/DE-0030: evidence を *袋* でなく *関係付き support path* として見る。各 SUPPORTS relation を
    # 独立の support path とし、その (source_class, observation_kind) を集める。GENERATED path は
    # 独立に mode を確立できない=eligible から除くが、**別の適格 primary path を大域無効化しない**
    # (旧 all(c!=GENERATED) の大域 veto は非単調——無関係な生成物1件で valid PRIMARY path が壊れた)。
    eligible = []   # non-GENERATED な SUPPORTS path の (source_class, observation_kind)
    for rid in candidate.get("evidence_relations", []):
        rel = core.get(con, rid)
        if not rel or rel.get("relation_type") != "SUPPORTS":
            continue
        frag = core.get(con, rel.get("from_id"))
        nobs = core.get(con, frag.get("norm_obs_id")) if frag else None
        src = core.get(con, nobs.get("source_id")) if nobs else None
        if not (src and nobs):
            continue
        if src.get("source_class") == "GENERATED":   # 独立資格なし。ただし他 path を veto しない
            continue
        eligible.append((src.get("source_class"), nobs.get("observation_kind", "UNSPECIFIED")))
    if not any(c == "PRIMARY" for c, _ in eligible):
        return "UNRESOLVED"
    # R6+R7/DE-0029(Taka 裁定 supersede R5): mode は evidence の epistemic kind(observation_kind)に
    #   従い polarity と *直交* する。DECLARATION(公式が宣言)→ DECLARED / SPECIFICATION(公式仕様に
    #   規定)→ SPECIFIED。正負(支持/不支持)は mode を変えない——『公式が非対応と宣言』は DECLARED+
    #   NEGATIVE、『仕様が禁止』は SPECIFIED+NEGATIVE。負の理由は candidate.negative_basis が別軸で担う。
    if any(c == "PRIMARY" and k == "DECLARATION" for c, k in eligible):
        return "DECLARED"
    if any(c == "PRIMARY" and k == "SPECIFICATION" for c, k in eligible):
        return "SPECIFIED"
    return "UNRESOLVED"


def eligible_support_paths(con, candidate):
    """DE-0040: policy-eligible な qualifying SUPPORTS path の relation id 群を返す。
    first slice: source_class==PRIMARY な非 GENERATED SUPPORTS path(観測種別の policy 照合は
    取得境界 evaluate_leg_requirement 側。curation では source_class を保守 proxy にする)。
    factual admission(VERIFIED)はこれが空でないことを要する = judge entailment ≠ claim admission。"""
    out = []
    for rid in candidate.get("evidence_relations", []):
        rel = core.get(con, rid)
        if not rel or rel.get("relation_type") != "SUPPORTS":
            continue
        frag = core.get(con, rel.get("from_id"))
        nobs = core.get(con, frag.get("norm_obs_id")) if frag else None
        src = core.get(con, nobs.get("source_id")) if nobs else None
        if src and src.get("source_class") == "PRIMARY":
            out.append(rid)
    return out


def candidate_has_taint(con, candidate):
    """DE-0039: 候補の evidence fragment に taint があるか(bootstrap 除外用の defense-in-depth。
    tainted は通常 gate1 GC-8 で先に block されるが、bootstrap 適格判定でも明示的に排除する)。"""
    for rid in candidate.get("evidence_relations", []):
        rel = core.get(con, rid)
        frag = core.get(con, rel.get("from_id")) if rel else None
        if frag and frag.get("taint_flags"):
            return True
    return False


def derive_absence_validation(con, candidate):
    """ABSENCE claim の validation は別軸(R5)。通常の validation_mode を使わない。
    根拠は『どの coverage profile の調査を完遂したか』= SC-2 の provenance。
    NOT_FOUND(調査完遂したが無い)を『公式規定の不在』と読み違えさせない。"""
    scon = core.get(con, candidate.get("search_conclusion"))
    plan_id = scon.get("search_plan_id") if scon else None
    return {"mode": "SEARCH_COVERAGE_COMPLETED", "search_plan_id": plan_id}


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
