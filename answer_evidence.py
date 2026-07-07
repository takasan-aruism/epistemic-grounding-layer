"""2DER Answer Evidence Contract (AEC) + Surface (AES) — answer-layer contracts over EGL evidence.

DD-ARCH: AEC/AES は 2DER の answer-layer role であって独立責任系ではない。EGL が epistemic 責任系、
RRI が research-need/design 責任系。answer layer は EITHER を吸収しない(knowledge admission も research もしない)。
ANSWER_CLAIM_PACKET は EGL の Claim/Observation/Source/EvidenceLink refs を参照する **derived rendering artifact**
であり、第二の knowledge SoR ではない。scalar confidence score は scope 外(source fitness は claim-relative)。
"""
import re

CLAIM_CLASSES = {"FACT", "INFERENCE", "HYPOTHESIS", "DESIGN_CHOICE"}
VALIDATION_MODES = {"DECLARED", "SPECIFIED", "OBSERVED", "MEASURED", "REPRODUCED", "UNRESOLVED"}
BASIS_KINDS = {"AI_INFERENCE", "EXTERNAL_RESEARCH", "EXTERNAL_SPECIFICATION", "LOCAL_CODE_OBSERVATION",
               "LOCAL_MEASUREMENT", "LOCAL_REPRODUCTION", "HUMAN_DECLARATION", "MIXED_BASIS", "UNRESOLVED"}
# §8 compact surface labels(JP)
LABELS = {"AI_INFERENCE": "AI推論", "EXTERNAL_RESEARCH": "外部調査", "EXTERNAL_SPECIFICATION": "公式仕様",
          "LOCAL_CODE_OBSERVATION": "コード確認", "LOCAL_MEASUREMENT": "実測", "LOCAL_REPRODUCTION": "再現",
          "HUMAN_DECLARATION": "人間申告", "MIXED_BASIS": "混合根拠", "UNRESOLVED": "未解決"}
# basis_kind が evidence ref を要するもの(§7)
_NEEDS_REF = {"EXTERNAL_RESEARCH", "EXTERNAL_SPECIFICATION", "LOCAL_CODE_OBSERVATION",
              "LOCAL_MEASUREMENT", "LOCAL_REPRODUCTION"}

# lexical cues(fail-conservative。完全な意味含意は主張しない — §14)
_HEDGE = re.compile(r"(可能性|かもしれ|恐らく|おそらく|見込み|推論|推定|未実測|未測定|未確認|未確立|確立していま|確立していな|確認できて|できていま|できていな|分かりません|分からない|まだ|likely|may |might|possibly|could|estimate|appears|suggests|probably|not measured|unverified|counterfactual|not established|not yet|unknown|unclear|to be determined)", re.I)
_LOCAL = re.compile(r"(現在|ローカル|実機|うちの|この環境|現構成|現在の構成|our |local |this environment|current config|in production|現行)", re.I)
_ABSENCE = re.compile(r"(存在しない|存在しません|できない|できません|不可能|不可|無い|ない\b|no native|does not|doesn't|cannot|can't|impossible|no legal|not exist|none)", re.I)
_PERF_LOCAL = re.compile(r"(速く|速い|下がる|減る|改善|高速|効率|reduce|fast|faster|speeds? up|improve|lower|works? in|stable|efficient|performant|動く|使える)", re.I)
_SCOPE_QUAL = re.compile(r"(現在|current|config|構成|環境|environment|2×|RTX|TP=2|NVFP4|version|バージョン|2026)", re.I)


def _has(pat, s):
    return bool(pat.search(s or ""))


# ── §5/§7 packet validation ───────────────────────────────────────────────────
def validate_packet(p):
    """§7: 必須 field + basis_kind ごとの ref 要件。fail-closed。返り {valid, problems}。"""
    if not isinstance(p, dict):
        return {"valid": False, "problems": ["packet is not a dict (fail-closed)"]}
    probs = []
    for f in ("answer_claim_id", "statement", "claim_class", "basis_kind", "validation_mode"):
        if not p.get(f):
            probs.append(f"missing required field: {f}")
    if p.get("claim_class") not in CLAIM_CLASSES:
        probs.append(f"claim_class 不正: {p.get('claim_class')!r}")
    if p.get("validation_mode") not in VALIDATION_MODES:
        probs.append(f"validation_mode 不正: {p.get('validation_mode')!r}")
    bk = p.get("basis_kind")
    if bk not in BASIS_KINDS:
        probs.append(f"basis_kind 不正: {bk!r}")
    refs = p.get("evidence_refs") or []
    if bk in _NEEDS_REF and not refs:
        probs.append(f"{bk} は evidence_refs を要する(§7)")
    if bk == "AI_INFERENCE" and not refs and not p.get("ungrounded_reasoning"):
        probs.append("AI_INFERENCE は evidence_refs か ungrounded_reasoning=true を要する")
    if bk == "HUMAN_DECLARATION" and not (p.get("declaration_source") or p.get("subject")):
        probs.append("HUMAN_DECLARATION は declaration_source / subject を要する")
    if bk == "MIXED_BASIS" and not (p.get("component_bases") and len(p["component_bases"]) >= 2):
        probs.append("MIXED_BASIS は component_bases(>=2)を要する")
    if bk == "UNRESOLVED" and not (p.get("residuals")):
        probs.append("UNRESOLVED は residuals(missing-evidence)を要する")
    return {"valid": not probs, "problems": probs}


# ── §14 answer-composition strength guard(anti-inflation, fail-conservative)────
def strength_guard(p):
    """statement wording を claim_class / validation_mode / basis / scope と照合し、
    evidence-strength inflation を flag。lexical+schema。完全な意味含意は主張しない(fail-conservative)。"""
    v = []
    s = p.get("statement", "")
    bk, cc, vm = p.get("basis_kind"), p.get("claim_class"), p.get("validation_mode")
    refs = p.get("evidence_refs") or []
    scope = (p.get("scope") or "")
    hedged = _has(_HEDGE, s)

    # INFERENCE/HYPOTHESIS を FACT wording で(AE-4)
    if cc in ("INFERENCE", "HYPOTHESIS") and not hedged:
        v.append({"type": "INFERENCE_AS_FACT", "detail": "INFERENCE/HYPOTHESIS だが断定的表現(hedge 無し)→ likely/推定 に narrow 要"})
    # SPECIFIED-only で local applicability を主張(AE-1, AE-5)
    if (vm == "SPECIFIED" or bk == "EXTERNAL_SPECIFICATION") and _has(_LOCAL, s) and _has(_PERF_LOCAL, s) \
            and p.get("local_applicability") not in ("MEASURED", "REPRODUCED"):
        v.append({"type": "SPECIFIED_IMPLIES_LOCAL", "detail": "SPECIFIED は local 適用/性能を確立しない → local_applicability 要 measure"})
    # 狭い local scope を general に(AE-3)
    if _has(_LOCAL, scope) or _has(_SCOPE_QUAL, scope):
        if not _has(_SCOPE_QUAL, s):
            v.append({"type": "NARROW_TO_GENERAL", "detail": f"scope は狭い({scope[:40]})が statement に scope 限定が無い → 一般化 inflation"})
    # 不在主張に basis/coverage が無い(AE-2)
    if _has(_ABSENCE, s):
        has_absence_basis = bool(p.get("negative_basis") or p.get("coverage")) or \
            (bk in ("LOCAL_MEASUREMENT", "LOCAL_REPRODUCTION") and refs)
        if not has_absence_basis:
            v.append({"type": "ABSENCE_WITHOUT_BASIS", "detail": "不在/不可主張だが negative_basis / coverage / 実測 root が無い"})
    # MEASURED wording/basis で ref 無し(AE-6)
    if (vm == "MEASURED" or bk == "LOCAL_MEASUREMENT") and not refs:
        v.append({"type": "MEASURED_WITHOUT_REF", "detail": "MEASURED だが evidence_refs が空 → 無効 packet"})
    # MIXED を単一 badge に flatten(AE-7)
    comp = p.get("component_bases") or []
    if bk != "MIXED_BASIS" and len({c.get("basis_kind") if isinstance(c, dict) else c for c in comp}) >= 2:
        v.append({"type": "MIXED_FLATTENED", "detail": "複数 basis を含むが単一 basis_kind で表現 → split か MIXED_BASIS 要"})
    return {"ok": not v, "violations": v}


def compose_ok(p):
    """packet が render 可能か(validate + strength 両方)。fail-conservative。"""
    vp = validate_packet(p)
    sg = strength_guard(p)
    return {"renderable": vp["valid"] and sg["ok"], "validate": vp, "strength": sg}


# ── §8/§9 rendering ────────────────────────────────────────────────────────────
def render_compact(p):
    """§9 L1 compact JP surface(raw ledger ID は出さない)。"""
    bk = p.get("basis_kind")
    label = LABELS.get(bk, bk)
    lines = [p.get("statement", ""), "", f"[{label}]"]
    desc = p.get("evidence_summary") or p.get("source_role") or ""
    if desc:
        lines.append(f"根拠: {desc}")
    la = p.get("local_applicability")
    if bk == "EXTERNAL_SPECIFICATION" and la in (None, "NOT_MEASURED"):
        lines.append("実機確認: 未")
    if bk in ("LOCAL_MEASUREMENT", "LOCAL_REPRODUCTION") and p.get("scope"):
        lines.append(f"範囲: {p['scope']}")
    if bk == "UNRESOLVED" and p.get("residuals"):
        lines.append(f"不足: {p['residuals'][0]}")
    if bk in ("AI_INFERENCE", "MIXED_BASIS") and p.get("validation_mode") == "UNRESOLVED":
        lines.append("実測: 未")
    return "\n".join(lines)


def render_expanded(p):
    """§9 L2 expanded evidence trace(明示要求時)。"""
    return {
        "statement": p.get("statement"), "claim_class": p.get("claim_class"),
        "basis_kind": p.get("basis_kind"), "validation_mode": p.get("validation_mode"),
        "source_policy": p.get("source_policy"), "source_role": p.get("source_role"),
        "supports_dimension": p.get("supports_dimension"), "unsupported_dimension": p.get("unsupported_dimension"),
        "scope": p.get("scope"), "currentness": p.get("currentness"),
        "evidence_refs": p.get("evidence_refs"), "egl_claim_ref": p.get("egl_claim_ref"),
        "discovered_by": p.get("discovered_by"), "evidence_source": p.get("evidence_source"),
        "claim_registration_status": p.get("claim_registration_status"),
        "local_applicability": p.get("local_applicability"), "residuals": p.get("residuals"),
        "component_bases": p.get("component_bases"),
    }
