"""SLICE-1: mechanical CURRENT_STATE builder (2DER autonomous loop v0).

Prereg: docs/autonomy_slice1_prereg_v0.1.md
Produces a machine-derived state projection with HONEST origin tags. Side-effect-free:
build_current_state() reads repo files and returns a dict; it writes NOTHING. The CLI
(build_state.py) writes CURRENT_STATE.json (a regenerable/deletable projection).

Invariants (see prereg): read-only to SoR/ledger · origin honesty (heuristics tagged
CLAUDE-DERIVED, never MECHANICAL) · no fabrication (unverifiable seals => UNVERIFIABLE) ·
totality (malformed/missing inputs never crash). NOT evidence promotion. C≠H.
"""
import json, hashlib, datetime, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "DESIGN_EVIDENCE_LEDGER.jsonl"
SPEC = REPO / "docs" / "2DER_TECHNICAL_SPECIFICATION.md"
AUTONOMY_LEDGER = REPO / "AUTONOMY_LEDGER.jsonl"

# closed/negative-branch heuristic keywords (CLAUDE-DERIVED, interpretive — NOT a clean enum in the ledger)
_CLOSURE_KW = ("CLOSE", "NEGATIVE", "DEMOTE", "NOT_CONFIRMED", "REJECT", "ODF_CLOSED",
               "PHASE3_CLOSED", "NOT_VIABLE", "DOWNGRAD")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except Exception:
        return None


def load_de_ledger():
    out = []
    try:
        for line in LEDGER.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):   # totality: ignore non-dict JSON lines (no downstream crash)
                        out.append(obj)
                except Exception:
                    pass
    except Exception:
        pass
    return out


def load_taka_events():
    """Read append-only AUTONOMY_LEDGER.jsonl (Taka correction events). dict-only, guarded."""
    out = []
    try:
        for line in AUTONOMY_LEDGER.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        out.append(obj)
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _apply_taka_overlay(state, events):
    """Apply Taka correction events to the mechanical state, with VISIBLE downstream effects.
    Append-only supersession: the LAST event per target_object wins (reversible). v0 realizes
    HOLD/REJECT/PRIORITY_OVERRIDE on candidate_work; REDIRECT/RECLASSIFICATION are surfaced in
    authority_pending only (not auto-applied); CORRECTION/CONTEXT_ADDITION are recorded only."""
    effects = []
    # active = latest event per target_object (append order = ts order)
    active = {}
    for ev in events:
        active[ev.get("target_object")] = ev
    pending = []
    for tgt, ev in active.items():
        act = ev.get("action")
        eid = ev.get("event_id")
        if act in ("TAKA_HOLD", "TAKA_REJECT", "TAKA_REDIRECT", "TAKA_AUTHORITY_RECLASSIFICATION"):
            pending.append({"event_id": eid, "action": act, "target_object": tgt,
                            "content": ev.get("content"), "reason": ev.get("reason")})
        for w in state["candidate_executable_work"]:
            if tgt and (tgt == w.get("kind") or tgt == str(w.get("ref"))):   # exact match only (no loose substring)
                if act == "TAKA_HOLD":
                    w["held_by"] = eid; effects.append(f"{eid}: HOLD {tgt} -> work item held (router skips)")
                elif act == "TAKA_REJECT":
                    w["rejected_by"] = eid; effects.append(f"{eid}: REJECT {tgt} -> work item dropped")
                elif act == "TAKA_PRIORITY_OVERRIDE":
                    try:
                        w["priority"] = int(ev.get("content"))
                        effects.append(f"{eid}: PRIORITY_OVERRIDE {tgt} -> priority={w['priority']}")
                    except Exception:
                        pass
    # drop rejected, keep held (flagged), resort
    state["candidate_executable_work"] = sorted(
        [w for w in state["candidate_executable_work"] if "rejected_by" not in w],
        key=lambda w: (w.get("held_by") is not None, w.get("priority", 99)))
    state["authority_pending"] = pending
    state["taka_events"] = events
    state["taka_overlay_effects"] = effects
    state["field_origins"]["taka_events"] = "TAKA-OWNED"
    state["field_origins"]["taka_overlay_effects"] = "TAKA-OWNED"
    return state


def _walk_seal_refs(obj):
    """Yield (path, expected_sha256) pairs found anywhere in a seal JSON.
    Two shapes: {"path":..,"sha256":..} dicts, and {"<file/path>": "<64hex>"} maps
    (e.g. companion_hashes). Hash-only pins (no file path) are skipped => UNVERIFIABLE."""
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str) and _HEX64.match(str(obj.get("sha256", ""))):
            yield obj["path"], obj["sha256"]
        for k, v in obj.items():
            if isinstance(v, str) and _HEX64.match(v) and "/" in k:   # only true paths; bare-filename pins => UNVERIFIABLE
                yield k, v
            else:
                yield from _walk_seal_refs(v)
    elif isinstance(obj, list):
        for it in obj:
            yield from _walk_seal_refs(it)


def verify_seals():
    """MECHANICAL: recompute sha256 of each referenced file vs the recorded value."""
    seals = []
    for sf in sorted((REPO / "experiments").glob("*seal*.json")):
        rec = {"file": f"experiments/{sf.name}", "verified": [], "mismatched": [], "unverifiable": 0}
        try:
            obj = json.loads(sf.read_text())
        except Exception:
            rec["status"] = "PARSE_ERROR"
            seals.append(rec)
            continue
        refs = list(_walk_seal_refs(obj))
        for path, expected in refs:
            actual = _sha256_file(REPO / path)
            if actual is None:
                rec["unverifiable"] += 1
            elif actual == expected:
                rec["verified"].append(path)
            else:
                rec["mismatched"].append({"path": path, "expected": expected, "actual": actual})
        rec["n_refs"] = len(refs)
        rec["status"] = ("MISMATCH" if rec["mismatched"]
                         else "OK" if rec["verified"]
                         else "UNVERIFIABLE")
        seals.append(rec)
    return seals


def component_files():
    def rel(g):
        return sorted(str(p.relative_to(REPO)) for p in g)
    return {
        "egl_core": rel((REPO / "egl").glob("*.py")),
        "experiments_runners": rel((REPO / "experiments").glob("run_*.py")),
        "tests": rel(REPO.glob("test_*.py")),
        "autonomy": rel((REPO / "autonomy").glob("*.py")),
    }


def _max_de_in_text(text):
    ids = [int(m) for m in re.findall(r"DE-(\d{4})", text or "")]
    return max(ids) if ids else None


def spec_staleness(ledger):
    ledger_latest = None
    if ledger:
        m = re.search(r"DE-(\d{4})", ledger[-1].get("design_evidence_id", ""))
        ledger_latest = int(m.group(1)) if m else None
    spec_latest = None
    try:
        spec_latest = _max_de_in_text(SPEC.read_text())
    except Exception:
        pass
    stale = (ledger_latest is not None and spec_latest is not None and spec_latest < ledger_latest)
    return {"spec_latest_de": f"DE-{spec_latest:04d}" if spec_latest else None,
            "ledger_latest_de": f"DE-{ledger_latest:04d}" if ledger_latest else None,
            "stale": bool(stale)}


def validation_failures():
    """MECHANICAL: scan known result artifacts for explicit failure flags."""
    fails = []
    for rf in sorted((REPO / "experiments").glob("*result*.json")):
        try:
            d = json.loads(rf.read_text())
        except Exception:
            continue
        name = f"experiments/{rf.name}"
        if d.get("coverage_all_ok") is False or d.get("coverage_ok") is False:
            fails.append({"artifact": name, "kind": "coverage_not_ok"})
        for b in (d.get("batches") or []):
            v = (b.get("validate") or {}).get("metrics") or {}
            if v.get("m1_grounding_integrity_pass") is False:
                fails.append({"artifact": name, "kind": "m1_grounding_fail",
                              "detail": f"batch={b.get('tag')} src_trace={v.get('source_trace_completeness')}"})
    return fails


def closed_branches(ledger):
    """CLAUDE-DERIVED (heuristic): free-text decision/replication_status keyword match."""
    out = []
    for e in ledger:
        blob = (str(e.get("decision", "")) + " " + str(e.get("replication_status", ""))).upper()
        if any(kw in blob for kw in _CLOSURE_KW):
            out.append({"de": e.get("design_evidence_id"), "decision": e.get("decision", "")[:60]})
    return out


# UNOWNED constructs — CLAUDE-DERIVED, mirrors living spec §2.8 (authoritative source = the spec)
_UNOWNED = ["Attention Center", "same-object tension binding", "structural re-centering",
            "local Aruism operational regime", "end-to-end self-operation"]


def build_current_state():
    """Side-effect-free. Returns the state dict. Writes nothing."""
    ledger = load_de_ledger()
    seals = verify_seals()
    stale = spec_staleness(ledger)
    vfails = validation_failures()
    latest_de = ledger[-1].get("design_evidence_id") if ledger else None

    # candidate_executable_work: MECHANICAL subset only (no LLM free-writing)
    work = []
    for s in seals:
        if s["status"] == "MISMATCH":
            work.append({"priority": 1, "kind": "seal_mismatch", "ref": s["file"]})
    for f in vfails:
        work.append({"priority": 3, "kind": "validation_failure", "ref": f})
    if stale["stale"]:
        work.append({"priority": 5, "kind": "spec_stale",
                     "ref": f"spec@{stale['spec_latest_de']} < ledger@{stale['ledger_latest_de']}"})
    work.sort(key=lambda w: w["priority"])

    state = {
        "object": "CURRENT_STATE",
        "schema_version": "v0.1",
        "as_of": datetime.datetime.now().isoformat(timespec="seconds"),
        "latest_de": latest_de,
        "n_de_entries": len(ledger),
        "de_index": [{"id": e.get("design_evidence_id"), "evidence_class": e.get("evidence_class"),
                      "replication_status": e.get("replication_status"), "decision": e.get("decision"),
                      "decision_owner": e.get("decision_owner")} for e in ledger],
        "seals": seals,
        "component_files": component_files(),
        "component_class_heuristic": {"egl_core": "LIVE-CORE(authoritative tags=spec §2)",
                                      "experiments_runners": "EXHIBIT-OR-TOOL",
                                      "tests": "TEST", "autonomy": "AUTONOMY-LOOP-v0"},
        "closed_branches": closed_branches(ledger),
        "unowned_constructs": _UNOWNED,
        "validation_failures": vfails,
        "spec_staleness": stale,
        "authority_pending": [],   # TAKA-OWNED: populated by the Taka overlay below
        "candidate_executable_work": work,
    }
    state["field_origins"] = {
        "latest_de": "MECHANICAL", "n_de_entries": "MECHANICAL", "de_index": "MECHANICAL",
        "seals": "MECHANICAL", "component_files": "MECHANICAL",
        "component_class_heuristic": "CLAUDE-DERIVED", "closed_branches": "CLAUDE-DERIVED",
        "unowned_constructs": "CLAUDE-DERIVED", "validation_failures": "MECHANICAL",
        "spec_staleness": "MECHANICAL", "authority_pending": "TAKA-OWNED",
        "candidate_executable_work": "MECHANICAL",
    }
    return _apply_taka_overlay(state, load_taka_events())
