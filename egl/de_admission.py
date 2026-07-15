"""EGL Design-Evidence admission (DE-0178). The ONLY sanctioned writer of DESIGN_EVIDENCE_LEDGER.jsonl.

Until now the DE ledger had NO code writer — every entry was a manual Claude append (a bypass Taka flagged).
This function is the admission gate a development-evidence registration must pass through, mirroring the
result_packet / VALIDATION_TARGET discipline (DE-0047/0059):

- schema check (required fields + non-empty evidence_refs) — no evidence => REJECTED.
- duplicate design_evidence_id => REJECTED (id is auto-assigned if omitted).
- claim ceiling: HARD_REJECT tokens (self-improvement / bottleneck-solved / co-serve / proven-correct /
  guaranteed / fully-verified …) => REJECTED. A BEHAVIORAL_PROPERTY assertion beyond tested scope without
  an EGL independent reverify => DOWNGRADED from ADMITTED to REPORTED (record exists ≠ behaviour proven).
- record_class classification: OBSERVED / IMPLEMENTED / LIVE / MANUAL_BYPASS.
- the ledger line is appended ONLY here, with EGL-assigned admission metadata.

Callers propose; EGL decides id + status + append. Claude no longer appends the ledger directly.
"""
import json, re
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "DESIGN_EVIDENCE_LEDGER.jsonl"

REQUIRED = ("observation", "decision", "decision_owner")

# over-claims that must never enter the ledger (retention>detection discipline; measured-facts-only)
HARD_REJECT = ["self-improving", "self-improvement", "bottleneck solved", "bottleneck-solved",
               "co-serve confirmed", "co-serve proven", "proven correct", "guaranteed to work",
               "100% correct", "always works", "fully verified", "zero bugs", "cannot fail"]
# behavioural assertions that need EGL independent reverify; without it, downgrade ADMITTED -> REPORTED
BEHAVIORAL_MARKERS = ["behaves correctly", "works in production", "production-proven", "verified live behaviour",
                      "verified live behavior", "in all cases", "proven to behave"]


def _load(ledger):
    ids, maxn = set(), 0
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            did = e.get("design_evidence_id") or ""
            ids.add(did)
            m = re.search(r"DE-(\d{4,})", did)
            if m:
                maxn = max(maxn, int(m.group(1)))
    return ids, maxn


def _record_class(cand):
    if cand.get("manual_bypass"):
        return "MANUAL_BYPASS"
    refs = " ".join(str(r) for r in (cand.get("evidence_refs") or [])).lower()
    claimed = (cand.get("claimed_status") or "").upper()
    if claimed in ("OBSERVED", "IMPLEMENTED", "LIVE", "MANUAL_BYPASS"):
        return claimed
    if "obs-" in refs or "measured" in refs:
        return "OBSERVED"
    if "live" in refs or "trace" in refs:
        return "LIVE"
    return "IMPLEMENTED"


def admit_design_evidence(candidate, ts, ledger_path=None, reverify=None):
    """candidate=proposed DE dict. reverify:()->(ok,detail) for BEHAVIORAL claims. Returns admission result.
    Appends to the ledger ONLY on admit/downgrade (never on reject)."""
    ledger = Path(ledger_path) if ledger_path else LEDGER
    reasons, downgrades = [], []

    # (1) schema
    missing = [k for k in REQUIRED if not candidate.get(k)]
    if not (candidate.get("evidence_refs") or []):
        missing.append("evidence_refs (non-empty)")
    if missing:
        return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": candidate.get("design_evidence_id"),
                "reasons": [f"schema: missing {', '.join(missing)}"]}

    # anti-amnesia (DE-0181): an implementation/LIVE claim must cite the 2DER artifact ids it changed
    if (candidate.get("claimed_status") or "").upper() in ("IMPLEMENTED", "LIVE") and not candidate.get("affected_artifact_ids"):
        return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": candidate.get("design_evidence_id"),
                "reasons": ["implementation/LIVE claim requires affected_artifact_ids (2DER ARTIFACT ids), not file paths/prose"]}

    # (FI-MIN-4) claim–principal binding — ENFORCED only when generated_by_principal is disclosed (backward-compatible:
    # legacy DEs without it are admitted as bootstrap legacy with UNKNOWN_PRINCIPAL recorded). Canonical vocab lives in
    # twoder.principal_attribution; the rule is inlined here to avoid an egl->twoder import. A 2DER self-operation claim
    # backed by a CLAUDE_CODE (or UNKNOWN) artifact without disclosed MANUAL_SUBSTITUTION+lowered ceiling -> REJECT.
    _PRINCIPALS = ("QWEN", "DW", "DETERMINISTIC_COMPONENT", "CLAUDE_CODE", "TAKA", "MANUAL_RELAY", "UNKNOWN_PRINCIPAL")
    _2DER_SELF = {"QWEN", "DW", "DETERMINISTIC_COMPONENT"}
    gp = candidate.get("generated_by_principal")
    if gp is not None:
        gm = candidate.get("generation_mode", "DIRECT")
        claiming = candidate.get("claiming_principal") or gp
        lowered = bool(candidate.get("claim_ceiling_lowered"))
        if gp not in _PRINCIPALS or claiming not in _PRINCIPALS:
            return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": candidate.get("design_evidence_id"),
                    "reasons": ["FI-MIN-4: principal not in controlled vocabulary %s" % (_PRINCIPALS,)]}
        _bind_ok = (claiming == gp) or (gm == "MANUAL_SUBSTITUTION" and lowered)
        if gp == "UNKNOWN_PRINCIPAL":
            _bind_ok = False
        if candidate.get("self_operation_claim") and claiming in _2DER_SELF and gp not in _2DER_SELF \
                and not (gm == "MANUAL_SUBSTITUTION" and lowered):
            _bind_ok = False
        if not _bind_ok:
            return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": candidate.get("design_evidence_id"),
                    "reasons": ["FI-MIN-4 claim-principal binding failed: claiming=%s artifact=%s mode=%s lowered=%s "
                                "(fail-closed)" % (claiming, gp, gm, lowered)]}

    ids, maxn = _load(ledger)

    # (2) duplicate id
    did = candidate.get("design_evidence_id")
    if did and did in ids:
        return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": did,
                "reasons": [f"duplicate design_evidence_id {did} already in ledger"]}
    if not did:
        did = f"DE-{maxn + 1:04d}"

    text = " ".join(str(candidate.get(k, "")) for k in ("observation", "decision", "replication_status", "evidence_class")).lower()

    # (3) claim ceiling — hard reject
    hard = [tok for tok in HARD_REJECT if tok in text]
    if hard:
        return {"admitted": False, "admission_status": "REJECTED", "design_evidence_id": did,
                "reasons": [f"over-claim (ceiling): forbidden token(s) {hard}"]}

    # (3b) behavioural over-claim -> downgrade unless EGL independently reverifies
    validation_target = "RECORD_OCCURRENCE"
    admission_status = "ADMITTED"
    beh = [tok for tok in BEHAVIORAL_MARKERS if tok in text]
    if beh:
        validation_target = "BEHAVIORAL_PROPERTY"
        rv = reverify() if reverify else None
        if rv and rv[0]:
            admission_status = "VERIFIED"
            reasons.append(f"BEHAVIORAL reverified by EGL: {rv[1]}")
        else:
            admission_status = "REPORTED"
            downgrades.append(f"BEHAVIORAL assertion {beh} not independently reverified -> REPORTED "
                              "(record exists != behaviour established)")

    record_class = _record_class(candidate)
    admission_id = "ADM-" + did.split("-", 1)[1]     # one admission per DE; resolvable via resolve_admission

    # (4) build + append (ONLY writer)
    entry = dict(candidate)
    entry["design_evidence_id"] = did
    # (FI-MIN-1) record the content-generating principal on the DE artifact. Legacy candidates (no principal disclosed)
    # are kept as bootstrap legacy: recorded UNKNOWN_PRINCIPAL + a non-blocking finding, NEVER retro-rewritten.
    if candidate.get("generated_by_principal") is None:
        entry["generated_by_principal"] = "UNKNOWN_PRINCIPAL"
        entry["generation_mode"] = "TRANSPORT_ONLY"
        entry["fi_min_finding"] = "PRINCIPAL_NOT_RECORDED_LEGACY"
    else:
        entry["generated_by_principal"] = candidate["generated_by_principal"]
        entry["generation_mode"] = candidate.get("generation_mode", "DIRECT")
    entry["egl_admission"] = {
        "admission_id": admission_id,
        "admission_status": admission_status, "validation_target": validation_target,
        "record_class": record_class, "admitted_at": ts, "admitted_by": "egl.de_admission",
        "evidence_refs": candidate.get("evidence_refs"), "cited_2der_ids": candidate.get("cited_2der_ids") or [],
        "affected_artifact_ids": candidate.get("affected_artifact_ids") or [], "change_id": candidate.get("change_id"),
        "downgrades": downgrades,
        "basis": "record-occurrence of a development event; content/behaviour not auto-established",
    }
    with ledger.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"admitted": True, "admission_status": admission_status, "design_evidence_id": did,
            "admission_id": admission_id, "validation_target": validation_target, "record_class": record_class,
            "reasons": reasons or ["record-occurrence admitted"], "downgrades": downgrades,
            "ledger": str(ledger)}


def resolve_admission(admission_id, ledger_path=None):
    """Resolve an ADM- id to its ledger entry (the admission record)."""
    ledger = Path(ledger_path) if ledger_path else LEDGER
    if not ledger.exists():
        return None
    for line in ledger.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("egl_admission", {}).get("admission_id") == admission_id:
            return e
    return None
