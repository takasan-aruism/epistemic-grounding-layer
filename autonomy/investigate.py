"""SLICE-4 (v0): investigator runner (2DER autonomous loop). Given a work item selected by the
router, gather the real evidence, run a FIRST-PASS investigation via the local Qwen worker, and
record a structured finding append-only in INVESTIGATIONS.jsonl.

HONEST framing: this is a LOCAL-WORKER first pass (Qwen), NOT senior-verified (Claude Code) and NOT
Taka-approved. It produces a finding + proposed SMALLEST reversible next action + an A–G classification,
surfaced for Taka to steer (approve / redirect / hold). It changes NO evidence status and writes NO SoR.
"""
import sys, os, json, urllib.request, urllib.error, socket, datetime, re
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from autonomy.current_state import REPO

INVESTIGATIONS = REPO / "INVESTIGATIONS.jsonl"
_ENDPOINT = "http://localhost:8005/v1/chat/completions"
_MODEL = "Qwen3.6-35B-A3B"

CLASSES = ["A_REAL_STRUCTURAL", "B_GENERATION_ECHO", "C_WORK_BATCHING", "D_INSTRUMENT_DEFECT",
           "E_MISSING_EVIDENCE", "F_REPRESENTATION_LOSS", "G_UNKNOWN"]

_SYS = (
    "You are a FIRST-PASS investigator in an autonomous research loop. You do NOT decide program "
    "direction and you do NOT change any evidence status. Given a WORK ITEM and its EVIDENCE, open "
    "the evidence, compare expected vs actual, and produce a grounded finding. Classify the issue as "
    "exactly one of: A_REAL_STRUCTURAL, B_GENERATION_ECHO, C_WORK_BATCHING, D_INSTRUMENT_DEFECT, "
    "E_MISSING_EVIDENCE, F_REPRESENTATION_LOSS, G_UNKNOWN. Propose the SMALLEST REVERSIBLE next action. "
    "Do NOT invent mechanisms not supported by the evidence; if unsure, say G_UNKNOWN and confidence LOW. "
    "Return ONLY a JSON object: {\"findings\": str, \"expected\": str, \"actual\": str, "
    "\"classification\": one of the labels, \"proposed_next_action\": str, \"reversible\": true|false, "
    "\"confidence\": \"LOW\"|\"MED\"|\"HIGH\"}."
)


def _vllm_chat(prompt, max_tokens=900):
    body = json.dumps({"model": _MODEL, "temperature": 0, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": _SYS},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(_ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


def _extract_json(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(text[i:j + 1])
    except Exception:
        return None


def gather_evidence(work):
    """Load the real artifact behind a work item (read-only). Returns a compact evidence dict."""
    ref = work.get("ref")
    ev = {"work": work}
    art = ref.get("artifact") if isinstance(ref, dict) else None
    if art:
        try:
            d = json.loads((REPO / art).read_text())
            if work.get("kind") == "validation_failure":
                # pull the failing batches' M1 problems + metrics (the concrete evidence)
                fails = []
                for b in (d.get("batches") or []):
                    v = b.get("validate") or {}
                    if (v.get("metrics") or {}).get("m1_grounding_integrity_pass") is False:
                        fails.append({"batch": b.get("tag"),
                                      "m1_problems": (v.get("axes") or {}).get("M1_grounding_integrity"),
                                      "src_trace_completeness": (v.get("metrics") or {}).get("source_trace_completeness")})
                ev["artifact"] = art
                ev["failing_batches"] = fails
                ev["object"] = d.get("object")
            else:
                ev["artifact"] = art
                ev["excerpt"] = json.dumps(d)[:1500]
        except Exception as e:
            ev["evidence_error"] = f"{type(e).__name__}: {e}"
    return ev


def run_investigation(work):
    ev = gather_evidence(work)
    prompt = f"WORK ITEM:\n{json.dumps(work, ensure_ascii=False)}\n\nEVIDENCE:\n{json.dumps(ev, ensure_ascii=False)[:6000]}\n\nReturn the JSON finding now."
    try:
        raw = _vllm_chat(prompt)
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        return {"error": f"worker_unreachable:{e}"}
    obj = _extract_json(raw)
    if not isinstance(obj, dict):
        return {"error": "worker_returned_no_json", "raw": raw[:400]}
    if obj.get("classification") not in CLASSES:
        obj["classification"] = "G_UNKNOWN"
    obj["evidence_ref"] = ev.get("artifact")
    return obj


def _high_water():
    n = 0
    try:
        for line in INVESTIGATIONS.read_text().splitlines():
            m = re.search(r'"inv_id":\s*"INV-(\d+)"', line)
            if m:
                n = max(n, int(m.group(1)))
    except Exception:
        pass
    return n


def record_investigation(work, finding):
    inv = {"inv_id": f"INV-{_high_water() + 1:05d}",
           "ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "investigator": "qwen-first-pass",
           "senior_verified": False, "taka_status": "PROPOSED",
           "work_ref": {"kind": work.get("kind"), "ref": work.get("ref"), "priority": work.get("priority")},
           "finding": finding}
    with open(INVESTIGATIONS, "a") as f:
        f.write(json.dumps(inv, ensure_ascii=False) + "\n")
    return inv


def load_investigations():
    out = []
    try:
        for line in INVESTIGATIONS.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    o = json.loads(line)
                    if isinstance(o, dict):
                        out.append(o)
                except Exception:
                    pass
    except Exception:
        pass
    return out


def run_one_cycle(state):
    """Router selects next work -> investigate -> record. Returns (inv | None, rationale)."""
    from autonomy.router import select_next_work
    work, rationale = select_next_work(state)
    if work is None:
        return None, rationale
    # dedup: don't re-investigate a work item that already has an un-steered PROPOSED finding
    # (prevents duplicate INV rows masquerading as progress; investigate again only after Taka steers)
    for iv in state.get("investigations", []):
        wr = iv.get("work_ref", {})
        if wr.get("kind") == work.get("kind") and wr.get("ref") == work.get("ref") and not iv.get("taka_steer"):
            return None, f"top work already investigated as {iv['inv_id']} (PROPOSED, awaiting your steer)"
    finding = run_investigation(work)
    if finding.get("error"):
        return None, f"investigation failed: {finding['error']}"
    inv = record_investigation(work, finding)
    return inv, rationale


if __name__ == "__main__":
    from autonomy.current_state import build_current_state
    inv, rationale = run_one_cycle(build_current_state())
    print("rationale:", rationale)
    print(json.dumps(inv, ensure_ascii=False, indent=2) if inv else "(no investigation)")
