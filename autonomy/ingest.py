"""SLICE-8: general problem-ingest path (2DER dogfood). Enforces TAKA INPUT -> 2DER -> CLAUDE.

Takes an arbitrary Taka problem/idea, reconstructs current state, retrieves relevant prior history
(self_grounding over the DE/REVIEW ledger), and assembles an investigator HANDOFF that the Claude
senior investigator MUST consume instead of re-deriving from the raw prompt.

HONESTY: fakes NO absent capability. Stages 2DER cannot currently produce for a general problem
(triage / detection / reconstruction) are marked MISSING with the reason + evidence status — never
fabricated. inferred_working_objective is a NON-AUTHORITATIVE worker guess and never becomes the
program objective. Writes only PROBLEMS.jsonl / HANDOFFS.jsonl (append-only); no SoR/DE write.
"""
import sys, os, json, datetime, re, urllib.request, urllib.error, socket
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from autonomy.current_state import build_current_state, REPO
from egl.self_grounding import answer_question, validate_answer

PROBLEMS = REPO / "PROBLEMS.jsonl"
HANDOFFS = REPO / "HANDOFFS.jsonl"
_ENDPOINT = "http://localhost:8005/v1/chat/completions"
_MODEL = "Qwen3.6-35B-A3B"

_CONSTRAINT_KW = ("IMPOSSIBLE", "不可", "MEASURED", "制約", "VRAM", "not viable", "NEGATIVE", "CLOSED")


def _hw(path, prefix, key):
    n = 0
    try:
        for line in path.read_text().splitlines():
            m = re.search(rf'"{key}":\s*"{prefix}-(\d+)"', line)
            if m:
                n = max(n, int(m.group(1)))
    except Exception:
        pass
    return n


def _worker_infer_objective(raw):
    """NON-AUTHORITATIVE worker guess at the working objective. Never promoted to program objective."""
    sys_p = ("Restate the user's problem as a one-sentence working objective (what outcome they want). "
             "Do NOT invent scope beyond the text. Output the sentence only, no preamble.")
    body = json.dumps({"model": _MODEL, "temperature": 0, "max_tokens": 120,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": sys_p},
                                    {"role": "user", "content": raw}]}).encode()
    req = urllib.request.Request(_ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return (json.load(r)["choices"][0]["message"].get("content") or "").strip()


def ingest_problem(raw_input, stated_objective=None, context_refs=None, infer=True):
    """Record a Taka problem. stated_objective is authoritative iff Taka provided it."""
    pid = f"PB-{_hw(PROBLEMS, 'PB', 'problem_id') + 1:05d}"
    inferred = None
    if infer:
        try:
            inferred = _worker_infer_objective(raw_input)
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
            inferred = None
    prob = {
        "problem_id": pid,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "owner": "Taka",
        "raw_input": raw_input,
        "stated_objective": stated_objective,  # authoritative only if Taka set it
        "inferred_working_objective": ({"text": inferred, "authority": "NON_AUTHORITATIVE_WORKER_GUESS"}
                                       if inferred else None),
        "context_refs": context_refs or [],
    }
    with open(PROBLEMS, "a") as f:
        f.write(json.dumps(prob, ensure_ascii=False) + "\n")
    return prob


def assemble_handoff(problem):
    """Build the 2DER->Claude handoff. relevant_history is LIVE (retrieval); reconstruction/detection/
    triage for a general problem are honestly MISSING. Claude must start from THIS, not the raw prompt."""
    state = build_current_state()
    q = problem["raw_input"] + (" " + problem["stated_objective"] if problem.get("stated_objective") else "")
    ans, rids, raw = answer_question(q)
    val = validate_answer(ans, set(rids)) if isinstance(ans, dict) else None
    claims = (ans or {}).get("answer_claims") or [] if isinstance(ans, dict) else []
    gaps = (ans or {}).get("open_gaps") or [] if isinstance(ans, dict) else []

    hid = f"HO-{_hw(HANDOFFS, 'HO', 'handoff_id') + 1:05d}"
    handoff = {
        "handoff_id": hid,
        "produced_by": "2DER general-ingest (autonomy/ingest.py)",
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "problem": problem,
        "current_reality": {
            "repo_state": {"latest_de": state["latest_de"],
                           "candidate_work": len(state["candidate_executable_work"]),
                           "validation_failures": len(state["validation_failures"]),
                           "unowned_constructs": state["unowned_constructs"]},
            "runtime_acquisition": {"status": "NARROW",
                                    "note": "general machine/runtime reality は未取得。investigator が nvidia-smi/docker/serve script 等を現物で読む必要がある。"},
            "origin": "MECHANICAL(repo) + investigator-required(runtime)",
        },
        "relevant_history": {
            "status": "LIVE (self_grounding retrieval over DE/REVIEW ledger)",
            "record_ids": rids,
            "grounded_m1": (val or {}).get("metrics", {}).get("m1_grounding_integrity_pass"),
            "claims": [{"text": c.get("text"), "src": c.get("record_ids")} for c in claims if isinstance(c, dict)],
        },
        "known_constraints": [{"text": c.get("text"), "src": c.get("record_ids")} for c in claims
                              if isinstance(c, dict) and any(k in (c.get("text") or "") for k in _CONSTRAINT_KW)],
        "open_gaps": gaps,
        "triage": {"status": "MISSING", "reason": "RRI triage は DESIGN-ONLY(spec のみ)。general problem の live triage は未実装。"},
        "detection": {"status": "MISSING", "reason": "detection arms は EXHIBIT-ONLY(HBB harness)。general problem に未接続。"},
        "candidate_frames_realization_paths": {
            "status": "MISSING",
            "reason": "reconstruction は EXHIBIT-ONLY かつ scheduler CLOSED NEGATIVE(DE-0130)。general infra input に callable でない。fake しない。"},
        "next_operation": ("route to Claude senior investigator: reversible technical investigation grounded in "
                           "relevant_history + current reality. 既に提供された history/measured 値を再導出しない。"),
        "investigator_task": {
            "objective_stated": problem.get("stated_objective"),
            "objective_inferred_nonauthoritative": (problem.get("inferred_working_objective") or {}).get("text"),
            "must_start_from": "this handoff (relevant_history + known_constraints + open_gaps), NOT the raw prompt alone [ADVISORY contract — not runtime-enforced]",
            "pointers": ["~/models_trtllm/serve_*.sh", "nvidia-smi / docker ps", "DE ledger: " + ", ".join(rids)],
        },
        "authority_required": {"status": "UNKNOWN_UNTIL_INVESTIGATION",
                               "note": "service interruption 等が必要になれば PHASE-7 の構造化 escalation を Taka へ。"},
    }
    with open(HANDOFFS, "a") as f:
        f.write(json.dumps(handoff, ensure_ascii=False) + "\n")
    return handoff


def run(raw_input, stated_objective=None):
    return assemble_handoff(ingest_problem(raw_input, stated_objective))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_input")
    ap.add_argument("--objective", default=None)
    a = ap.parse_args()
    print(json.dumps(run(a.raw_input, a.objective), ensure_ascii=False, indent=2))
