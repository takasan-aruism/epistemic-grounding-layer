#!/usr/bin/env python3
"""Phase A 再抽出(coverage gap 補填)。0抽出だった phase を ### 単位 sub-chunk で再処理。
同一 frozen prompt。教訓除外。既存 INC-01..09 に追番で merge。"""
import json, sys, urllib.request, hashlib
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe as MF
from run_metaframe_extract import EXTRACT_SYS, chat, jarr, PROMPT_HASH
CORPUS = "/home/takasan/esde/ESDE-Research/docs/概念理解.md"
# 未被覆 phase の行範囲(0抽出 or gold欠落)
TARGETS = [("v9.15", 1694, 1931), ("v9.17", 2206, 2446), ("v9.18", 2469, 2677), ("v9.14b", 1560, 1694)]


def subchunks(lines, a, b, maxchars=8000):
    """[a,b) を ### 単位でまとめ、maxchars を超えない sub-chunk に。"""
    seg, chunks, size = [], [], 0
    for i in range(a - 1, min(b, len(lines))):
        l = lines[i]
        if l.startswith("### ") and size > maxchars and seg:
            chunks.append("\n".join(seg)); seg, size = [], 0
        seg.append(l); size += len(l) + 1
    if seg:
        chunks.append("\n".join(seg))
    return chunks


def main():
    lines = Path(CORPUS).read_text().splitlines()
    existing = json.load(open("/home/takasan/egl/experiments/metaframe_candidates.json"))
    k = len(existing["candidates"])
    new = []
    for name, a, b in TARGETS:
        for ci, body in enumerate(subchunks(lines, a, b)):
            if len(body) < 500:
                continue
            raw = chat(EXTRACT_SYS, f"SOURCE ({name} part {ci}, ~line {a}):\n{body[:12000]}\n\nReturn the JSON array of INCIDENT_FRAME candidates.", seed=0)
            for x in jarr(raw):
                if not isinstance(x, dict):
                    continue
                k += 1
                x.update({"incident_id": f"INC-{k:02d}", "source_document": CORPUS,
                          "source_span_refs": [x.get("source_span_hint") or f"{name} ~{a}"],
                          "origin": "CORPUS_EXTRACTION", "corpus_tier": "TIER_1_RETROSPECTIVE_CORPUS",
                          "pre_frame_fidelity": "RETROSPECTIVE_RECONSTRUCTION", "extraction_status": "CANDIDATE"})
                g = MF.validate_incident(x)
                x["_gate"] = {"valid": g["valid"], "eligible": g["eligible"], "problems": g["problems"][:3]}
                new.append(x)
            print(f"  [{name} part {ci}] +{len(jarr(raw))}", flush=True)
    print(f"\n新規候補 {len(new)} 件")
    Path("/home/takasan/egl/experiments/metaframe_candidates2.json").write_text(json.dumps({"new_candidates": new, "prompt_hash": PROMPT_HASH}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
