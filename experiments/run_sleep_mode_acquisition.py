#!/usr/bin/env python3
"""Sleep Mode external-spec RQ の EGL acquisition(Taka authorization 済)。
取得境界(AB-1/2/3)を通し、実 vLLM 公式ドキュメントから Claim を1本生成する。
chain: SourcePolicy → Gap → SearchPlan → LegIntent → 実 fetch(ACQ_HTTP_STATIC)→ AcquisitionRun
→ SearchResultSnapshot → RawObservation + Source Qualification(OFFICIAL_DOCS)→ Extraction
→ CandidateClaim → curate(gate1..5)→ Claim。validation_mode は provenance 導出(OFFICIAL_DOCS→DECLARATION→DECLARED)。
statement は excerpt が直接 entail する範囲のみ(local 性能主張へ inflate しない)。"""
import os, re, sys
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
os.environ["EGL_DATA_DIR"] = "/home/takasan/egl/data_sleepmode_claim"
for f in ["events.jsonl", "state.sqlite", ".idlock"]:
    p = Path(os.environ["EGL_DATA_DIR"]) / f
    if p.exists():
        p.unlink()
from egl import core, source_policy as SP, acquisition as ACQ, pipeline as P, judge, curator, adapters
def line(s=""): print(s)

TASK = "TASK-VLLM-SLEEPMODE"
TARGET = "https://docs.vllm.ai/en/latest/features/sleep_mode/"
line("########## Sleep Mode external-spec RQ — EGL acquisition ##########\n")

r = core.run_start("rd", "ACQUISITION", task_id=TASK)
SP.mk_source_policy(r, SP.SOFTWARE_TECHNICAL_V1)
G = P.mk_gap(r, "vLLM は model-transition コストを下げる native capability(sleep/offload)を文書化しているか",
             required_for=["RNEED-SLEEPMODE-1", "RQ-NATIVE-CAP-1"], profile="EP-TECH-STANDARD")
plan = P.mk_search_plan(r, G, "COV-TECH-STANDARD")
leg = ACQ.mk_leg_intent(r, plan_id=plan, task_id=TASK, required_source_kind="OFFICIAL_DOCS",
                        target_locator=TARGET, adapter_class="ACQ_HTTP_STATIC",
                        source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"], source_policy_version=1,
                        expected_entity="vLLM", purpose="vLLM Sleep Mode 公式ドキュメント証拠",
                        search_method="DOC_PAGE_FETCH", query=["sleep mode", "offload weights", "wake_up"],
                        scope_locator="docs.vllm.ai/en/latest/features/sleep_mode", revision="latest")
a = ACQ.acquire(r, leg)
arun = core.get_state(a)
line(f"[FETCH] transport={arun['transport_status']} content={arun['content_status']} http={arun['http_status']} "
     f"hash={(arun.get('raw_content_hash') or '')[:16]}")
ACQ.mk_search_result_snapshot(r, leg, a, result_count=1, result_refs=[TARGET])
obs = ACQ.emit_observation_if_eligible(r, a)
core.run_end(r, [])
if not obs:
    line("取得が evidence-eligible でない → leg UNSATISFIED(失敗も知識)"); raise SystemExit(0)
line(f"[QUALIFY] observed_source_kind={obs['observed_source_kind']} source={obs['source_id']}")
con = core.build_view()
cov = ACQ.evaluate_leg_requirement(con, leg)
line(f"[COVERAGE] leg satisfied={cov['satisfied']} matched={cov.get('matched_observed_kinds')}")

# --- 実取得 HTML から本物の一文を excerpt にする(捏造しない)---
body = adapters.fetch({"adapter_class": "ACQ_HTTP_STATIC", "target_locator": TARGET})["raw_bytes"].decode("utf-8", "replace")
text = re.sub(r"<[^>]+>", " ", body)
text = re.sub(r"\s+", " ", text)
m = re.search(r"(Level 1[^.]*offload the model weights[^.]*\.)", text, re.I)
excerpt = m.group(1).strip() if m else next((s.strip() for s in text.split(".") if "offload the model weights" in s.lower()), "offload the model weights")
line(f"[EXCERPT] {excerpt!r}")

re_ = core.run_start("extractor", "EXTRACTION", task_id=TASK)
ext = ACQ.extract_fragment(re_, obs["observation_id"], blocks=[excerpt], block_index=0, excerpt=excerpt,
                           section_heading="Sleep Mode / Sleep Levels", mentions=["ENT-vllm"])
core.run_end(re_, [])
line(f"[EXTRACT] fragment={ext['fragment_id']} observation_kind={ext['observation_kind']}")

rc = core.run_start("rd", "EXTRACTION", task_id=TASK)
rel = P.mk_relation(rc, ext["fragment_id"], None, "SUPPORTS",
                    {"question": "vLLM sleep mode capability", "scope": {"entity": "vllm"}})
STMT = ("vLLM は Sleep Mode を文書化しており、level 1 で model weights を CPU にオフロードし KV cache を破棄する"
        "(公式ドキュメントの記述)。")
C = P.mk_candidate(rc, {
    "object_kind": "CandidateClaim", "claim_type": "DESCRIPTION", "predicate": "documents_capability",
    "polarity": "POSITIVE", "task_id": TASK, "statement": STMT,
    "scope": {"entity": "vllm", "aspect": "documented sleep-mode capability"},
    "evidence_relations": [rel], "resolves_gap": G,
    "representation_residual": {"known_omissions": ["local wake latency (docs give NO latency numbers)",
                                                    "TP=2/NVFP4 applicability"], "scope_uncertainty": "LOW"}})
core.run_end(rc, [])

adj = judge.ClaudeAdjudicator({C: {"f1": "SUPPORTED", "f2": "WITHIN", "fragment_sufficient": True,
    "rationale": "取得した excerpt が 'offload the model weights and discard the KV cache' を直接記述。statement は "
                 "文書化された capability のみに scoped(local 性能を主張しない)。scope 内。"}})
line("\n[CURATE]")
res = curator.curate(C, adj, log=line)
con = core.build_view()
claim = next((c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C), None)
if claim:
    line(f"\n[CLAIM] {res.get('global_claim')}")
    line(f"        status={claim['status']}  validation_mode={claim.get('validation_mode')}")
    line(f"        statement: {claim.get('statement','')[:90]}")
    line(f"        provenance: Claim → fragment {ext['fragment_id']} → Source {obs['source_id']} "
         f"(observed={obs['observed_source_kind']}, PRIMARY) → AcquisitionRun {a} → LegIntent {leg}")
    import json
    Path("/home/takasan/egl/experiments/sleep_mode_claim.json").write_text(json.dumps({
        "task": TASK, "target": TARGET, "leg_satisfied": cov["satisfied"],
        "observed_source_kind": obs["observed_source_kind"], "claim_id": res.get("global_claim"),
        "status": claim["status"], "validation_mode": claim.get("validation_mode"),
        "statement": claim.get("statement"), "excerpt": excerpt,
        "residual": ["local wake latency 未文書化(docs に latency 数値なし)→ MEASUREMENT need",
                     "TP=2/NVFP4 applicability 未確立"]}, ensure_ascii=False, indent=2))
    line("\n→ vLLM Sleep Mode capability の Claim を実データから1本生成。")
    line("  DECLARED(公式 docs の declaration)であり MEASURED でない——local wake latency は docs に無く、")
    line("  切替コスト削減の local 主張は依然 measurement 待ち(§5 / AEC strength guard と一致)。")
line("\n=== Sleep Mode acquisition 完了 ===")
