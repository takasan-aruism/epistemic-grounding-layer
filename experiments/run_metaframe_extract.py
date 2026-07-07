#!/usr/bin/env python3
"""Phase A incident extraction(§13)。extractor=Qwen3.6。gold 封緘後に prompt 凍結。
corpus の phase-narrative chunk(## 教訓 セクションは除外=lesson-copy 抑制, §6/§13)を読み、
INCIDENT_FRAME 候補を出す。cluster/lesson/meta-frame は作らない(blindness)。gold は入力に含めない。"""
import json, re, sys, urllib.request, hashlib
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe as MF
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
CORPUS = "/home/takasan/esde/ESDE-Research/docs/概念理解.md"

def chat(sysp, u, seed=0, max_tokens=2000):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": max_tokens,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

def jarr(t):
    i, j = t.find("["), t.rfind("]")
    try:
        return json.loads(t[i:j + 1]) if 0 <= i < j else []
    except Exception:
        return []

# ── frozen extraction prompt (gold 封緘後に固定) ──
EXTRACT_SYS = (
    "You extract INCIDENT_FRAME candidates from a research-history document. An INCIDENT is a place where the "
    "represented PROBLEM FRAME changed after a tension, failure, contradiction, audit, or intervention. "
    "Reconstruct the causal chain from the prose. Do NOT summarize lessons, do NOT form reusable principles, do "
    "NOT cluster. For EACH incident return an object with: incident_id, topic_surface, observation, "
    "initial_interpretation, tension_or_failure, intervention (object with actor in "
    "{TAKA,AI,AUDIT,TEST,EXTERNAL_EVIDENCE,UNKNOWN} and statement_or_action), added_dimensions (list), "
    "added_distinctions (list of {left,relation,right}), added_operations (list), post_intervention_test_or_action, "
    "outcome, claim_before, claim_after, decision_changed (bool), field_support (each of observation / "
    "initial_interpretation / tension_or_failure / intervention / outcome = EXPLICIT | INFERRED | UNRESOLVED), "
    "source_span_hint (the heading or line range you used). Only include a candidate if you can point to actual "
    "text for observation, an initial interpretation/direction, a later tension, AND a changed "
    "dimension/distinction/operation. If a section is only a lesson list, an observation, or a status note with no "
    "frame change, DO NOT emit it. Return ONLY a JSON array.")
PROMPT_HASH = hashlib.sha256(EXTRACT_SYS.encode()).hexdigest()


def phase_chunks():
    lines = Path(CORPUS).read_text().splitlines()
    # v9.11..v9.18 region (rich narratives). split by '## ' ; drop 教訓 sections.
    chunks, cur, head, ln0 = [], [], None, 0
    for i, l in enumerate(lines):
        if l.startswith("## "):
            if cur and head and "教訓" not in head:
                chunks.append((head, ln0 + 1, "\n".join(cur)))
            head, cur, ln0 = l, [l], i
        else:
            cur.append(l)
        if i > 2680:
            break
    if cur and head and "教訓" not in head:
        chunks.append((head, ln0 + 1, "\n".join(cur)))
    return [c for c in chunks if c[1] >= 1312 and len(c[2]) > 400]


def main():
    chunks = phase_chunks()
    print(f"### Phase A extraction — {len(chunks)} phase-narrative chunks (教訓 excluded), prompt {PROMPT_HASH[:12]} ###\n")
    cands, k = [], 0
    for head, ln, body in chunks:
        raw = chat(EXTRACT_SYS, f"SOURCE (starting line ~{ln}):\n{body[:14000]}\n\nReturn the JSON array of INCIDENT_FRAME candidates.", seed=0)
        arr = jarr(raw)
        for a in arr:
            if not isinstance(a, dict):
                continue
            k += 1
            a["incident_id"] = f"INC-{k:02d}"
            a["source_document"] = CORPUS
            a["source_span_refs"] = [a.get("source_span_hint") or head.strip("# ")]
            a["origin"] = "CORPUS_EXTRACTION"
            a["corpus_tier"] = "TIER_1_RETROSPECTIVE_CORPUS"
            a["pre_frame_fidelity"] = "RETROSPECTIVE_RECONSTRUCTION"
            a["extraction_status"] = "CANDIDATE"
            g = MF.validate_incident(a)
            a["_gate"] = {"valid": g["valid"], "eligible": g["eligible"], "problems": g["problems"][:3]}
            cands.append(a)
        print(f"  [{head.strip('# ')[:48]}] +{len(arr)} candidates", flush=True)
    gate_ok = [c for c in cands if c["_gate"]["valid"] and c["_gate"]["eligible"]]
    out = {"prompt_hash": PROMPT_HASH, "n_chunks": len(chunks), "candidates": cands,
           "n_candidates": len(cands), "n_gate_pass": len(gate_ok)}
    Path("/home/takasan/egl/experiments/metaframe_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n  total candidates: {len(cands)}  gate(valid+eligible) pass: {len(gate_ok)}")
    print("  -> metaframe_candidates.json 保存。次: 外部weight監査(Claude)で VERIFIED 化。")


if __name__ == "__main__":
    main()
