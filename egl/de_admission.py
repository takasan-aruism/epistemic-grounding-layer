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

    # (4) build + append (ONLY writer)
    entry = dict(candidate)
    entry["design_evidence_id"] = did
    entry["egl_admission"] = {
        "admission_status": admission_status, "validation_target": validation_target,
        "record_class": record_class, "admitted_at": ts, "admitted_by": "egl.de_admission",
        "evidence_refs": candidate.get("evidence_refs"), "downgrades": downgrades,
        "basis": "record-occurrence of a development event; content/behaviour not auto-established",
    }
    with ledger.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"admitted": True, "admission_status": admission_status, "design_evidence_id": did,
            "validation_target": validation_target, "record_class": record_class,
            "reasons": reasons or ["record-occurrence admitted"], "downgrades": downgrades,
            "ledger": str(ledger)}
