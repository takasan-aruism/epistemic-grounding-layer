#!/usr/bin/env python3
"""Stage 2: file-level extraction via Qwen3.6-35B-A3B (:8005), 30-way parallel.
Spec §3. Qwen outputs ONLY what AST cannot give (§1.1 R1).
calls/called_by/reads/writes are INPUTS here, never outputs.

Call shape copied from the proven 2DER path (dw/adapters.py:_vllm_chat):
temperature 0, seed, chat_template_kwargs.enable_thinking=False.
"""
import json, sys, time, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

STRUCT = Path("/home/takasan/egl/structure")
ENDPOINT = "http://127.0.0.1:8005/v1/chat/completions"
MODEL = "Qwen3.6-35B-A3B"
PARALLEL = 30
MAX_TOKENS = 2600
BUDGET_TOKENS = 2_000_000      # provisional cap (spec §10.4 未裁定 → 暫定値)
BUDGET_SECONDS = 1800

EV = {"type": "object",
      "properties": {"line_start": {"type": "integer"}, "line_end": {"type": "integer"}},
      "required": ["line_start", "line_end"], "additionalProperties": False}
def lst(extra):
    props = {"evidence": EV}; props.update(extra)
    return {"type": "array", "maxItems": 6,
            "items": {"type": "object", "properties": props,
                      "required": sorted(props), "additionalProperties": False}}
SCHEMA = {"type": "object", "properties": {
    "purpose_1line": {"type": "string"},
    "declared_responsibility": {"type": "string"},
    "actual_capabilities": lst({"capability": {"type": "string"}}),
    "claimed_capabilities": lst({"claim": {"type": "string"}}),
    "capability_gap": lst({"claimed": {"type": "string"}, "why_not_actual": {"type": "string"}}),
    "authority_checks": lst({"check": {"type": "string"}}),
    "side_effects": lst({"effect": {"type": "string"}}),
    "failure_modes": lst({"mode": {"type": "string"}}),
    "limitations": lst({"limitation": {"type": "string"}}),
    "uncertainties": {"type": "array", "maxItems": 6, "items": {"type": "string"}},
    "lifecycle_signal": {"type": "string",
                         "enum": ["ACTIVE", "SCAFFOLD", "EXPERIMENT", "DEPRECATED", "UNKNOWN"]},
}, "required": ["purpose_1line", "declared_responsibility", "actual_capabilities",
                "claimed_capabilities", "capability_gap", "authority_checks", "side_effects",
                "failure_modes", "limitations", "uncertainties", "lifecycle_signal"],
   "additionalProperties": False}

SYSTEM = """You analyse ONE source file of the 2DER system and return structured facts as JSON.

HARD PROHIBITIONS (violating any of these invalidates your output):
1. Never assert anything without evidence. Every item carries a line range from THIS file.
   If you are unsure, put it in "uncertainties" instead.
2. Never treat a docstring/comment claim as an implementation fact. A docstring assertion is a
   "claimed_capability". Only code you can point at is an "actual_capability".
3. Never infer a role from the file name. If the body gives no basis, say UNKNOWN.
4. Never treat "DONE" or "implemented" in a comment as meaning the code runs.
5. NEVER judge whether this file is wired into the live path. You have not been given the
   information to decide that, and it is computed elsewhere. Do not speculate about callers.
6. Do not describe other files. Do not invent relationships beyond the given import facts.

"capability_gap" is the important field: where the file's own comments/docstrings claim more
than the code does (e.g. a guard that returns early, a branch gated off by default, a TODO,
a parameter that defaults to disabled)."""

def build_prompt(rec, sym, importers, src):
    d = sym.get("defines", [])[:40]
    facts = {
        "path": rec["key"],
        "loc": sym.get("loc"),
        "imports": [f"{i['module']}.{i['symbol']}" if i.get("symbol") else i["module"]
                    for i in sym.get("imports", [])][:40],
        "defines": [f"{x['kind']} {x['name']}:{x['lineno']}-{x['end_lineno']}" for x in d],
        "file_writes": [w.get("target") for w in sym.get("file_writes", [])][:15],
        "file_reads": [w.get("target") for w in sym.get("file_reads", [])][:15],
        "subprocess_calls": [s.get("call") for s in sym.get("subprocess_calls", [])][:10],
        "network": sym.get("network_libs", []) + sym.get("network_literals", [])[:6],
        "imported_by": importers[:20],
        "imported_by_count": len(importers),
    }
    return (f"AST FACTS (authoritative — do not contradict, do not repeat back):\n"
            f"{json.dumps(facts, ensure_ascii=False)}\n\n"
            f"SOURCE ({rec['key']}), line-numbered:\n"
            + "\n".join(f"{i+1:5d}| {l}" for i, l in enumerate(src.split("\n")[:1400])))

_lock = threading.Lock()
USAGE = {"prompt": 0, "completion": 0, "calls": 0, "errors": 0}

def call(prompt, seed):
    body = json.dumps({"model": MODEL, "temperature": 0, "seed": seed,
                       "max_tokens": MAX_TOKENS,
                       "chat_template_kwargs": {"enable_thinking": False},
                       # NOTE(I2): guided_json is SILENTLY IGNORED by this vLLM build.
                       # Verified with a negative control (schema demanding keys the prompt
                       # never mentions). Only response_format/json_schema actually constrains.
                       "response_format": {"type": "json_schema",
                                           "json_schema": {"name": "file_extraction",
                                                           "schema": SCHEMA, "strict": True}},
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=300)
    d = json.loads(r.read())
    u = d.get("usage") or {}
    with _lock:
        USAGE["prompt"] += u.get("prompt_tokens", 0)
        USAGE["completion"] += u.get("completion_tokens", 0)
        USAGE["calls"] += 1
    return json.loads(d["choices"][0]["message"]["content"])

def main():
    manifest = {}
    for l in open(STRUCT / "FILE_MANIFEST.jsonl"):
        r = json.loads(l); manifest[f"{r['repo']}/{r['relative_path']}"] = r
    syms = {}
    for l in open(STRUCT / "SYMBOL_INDEX.jsonl"):
        r = json.loads(l); syms[r["key"]] = r

    targets = [k for k, r in manifest.items()
               if r["extension"] == ".py" and r["classification"] == "source"
               and r["trust_tier"] == "T1_TRACKED"]
    targets.sort()
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    out_name = sys.argv[2] if len(sys.argv) > 2 else "FILE_EXTRACTION.jsonl"
    if len(sys.argv) > 3:                              # replication subset
        every = int(sys.argv[3]); targets = targets[::every]
    print(f"targets={len(targets)} seed={seed} parallel={PARALLEL} -> {out_name}")

    t0 = time.time(); results = []
    def work(k):
        rec = {"key": k}; rec.update({"repo": manifest[k]["repo"]})
        sym = syms.get(k, {})
        try:
            src = Path(manifest[k]["absolute_path"]).read_text(encoding="utf-8", errors="replace")
            r = call(build_prompt({"key": k}, sym, sym.get("imported_by", []), src), seed)
            rec.update(r); rec["extract_status"] = "OK"
        except Exception as e:
            with _lock: USAGE["errors"] += 1
            rec["extract_status"] = "ERROR"; rec["error"] = repr(e)[:300]
        rec.update({"model": MODEL, "seed": seed, "sha256": manifest[k]["sha256"],
                    "trust_tier": "T3_DERIVED", "regenerable": True,
                    "derived_from": "qwen3.6-35b-a3b@:8005 response_format/json_schema(strict); ast facts from SYMBOL_INDEX"})
        return rec

    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        futs = {ex.submit(work, k): k for k in targets}
        done = 0
        for f in as_completed(futs):
            results.append(f.result()); done += 1
            if done % 25 == 0 or done == len(targets):
                el = time.time() - t0
                print(f"  {done}/{len(targets)}  {el:6.1f}s  "
                      f"{USAGE['completion']/max(el,1e-9):7.1f} out-tok/s  "
                      f"{done/max(el,1e-9):5.2f} req/s  err={USAGE['errors']}")
            if USAGE["completion"] > BUDGET_TOKENS or time.time() - t0 > BUDGET_SECONDS:
                print("!! BUDGET REACHED — stopping"); break

    results.sort(key=lambda r: r["key"])
    (STRUCT / out_name).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n")
    el = time.time() - t0
    print(f"\nwrote {len(results)} -> {out_name}")
    print(f"wall={el:.1f}s  calls={USAGE['calls']}  errors={USAGE['errors']}")
    print(f"prompt_tok={USAGE['prompt']}  completion_tok={USAGE['completion']}")
    print(f"throughput: {USAGE['completion']/el:.1f} out-tok/s, {USAGE['calls']/el:.2f} req/s "
          f"(derived from primitives, not GPU util — PROCESS-01)")

if __name__ == "__main__":
    main()
