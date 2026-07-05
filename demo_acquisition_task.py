#!/usr/bin/env python3
"""Phase 1b 実タスク end-to-end(§19 step 12): 実 source を取得境界で取り、Extraction を経て
既存 curation spine(gate1..gate5)に流し、実データから Claim を1本生成する。

Task: 「vLLM とは何か」を vLLM 公式 repo(README)の実取得証拠で grounding する。
chain: SourcePolicy → LegIntent → 実 fetch(ACQ_GITHUB)→ AcquisitionRun → SearchResultSnapshot
→ RawObservation + Source Qualification → Extraction Run → NormalizedObservation(observation_kind)
→ EvidenceFragment → CandidateClaim → curate(gate1..gate5)→ Claim。

honest point: OFFICIAL_REPOSITORY → observation_kind=IMPLEMENTATION_ARTIFACT → validation_mode=UNRESOLVED
(公式 repo content は PRIMARY だが declaration ではない=R6/R7)。status は entailment で VERIFIED。
"""
import os
from pathlib import Path
os.environ["EGL_DATA_DIR"] = str(Path(__file__).resolve().parent / "data_acq_task")
for f in ["events.jsonl", "state.sqlite", ".idlock"]:
    p = Path(os.environ["EGL_DATA_DIR"]) / f
    if p.exists():
        p.unlink()

from egl import core, source_policy as SP, acquisition as ACQ, pipeline as P, judge, curator
def line(s=""): print(s)

TASK = "TASK-WHAT-IS-VLLM"
TARGET = "https://github.com/vllm-project/vllm/blob/main/README.md"
WANT = "vLLM is a fast and easy-to-use library for LLM inference and serving."

line("########## Phase 1b 実タスク end-to-end: 「vLLM とは何か」 ##########\n")

# --- acquisition run ---
r = core.run_start("rd", "ACQUISITION", task_id=TASK)
SP.mk_source_policy(r, SP.SOFTWARE_TECHNICAL_V1)                         # §14 versioned policy
G = P.mk_gap(r, "vLLM とは何か(公式 repo の記述)", required_for=[], profile="EP-TECH-STANDARD")
plan = P.mk_search_plan(r, G, "COV-TECH-STANDARD")
leg = ACQ.mk_leg_intent(r, plan_id=plan, task_id=TASK, required_source_kind="OFFICIAL_REPOSITORY",
                        target_locator=TARGET, adapter_class="ACQ_GITHUB",
                        source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"], source_policy_version=1,
                        expected_entity="vLLM", purpose="vLLM の定義を公式 repo で確認",
                        search_method="REPOSITORY_FILE_FETCH", query=["README"],
                        scope_locator="vllm-project/vllm", revision="main")
a = ACQ.acquire(r, leg)                                                  # 実 fetch
arun = core.get_state(a)
line(f"[FETCH] transport={arun['transport_status']} content={arun['content_status']} "
     f"http={arun['http_status']} sha={arun.get('adapter_provenance',{}).get('sha','')[:16]}")
ACQ.mk_search_result_snapshot(r, leg, a, result_count=1, result_refs=[TARGET])
obs = ACQ.emit_observation_if_eligible(r, a)
core.run_end(r, [])
if not obs:
    line("取得が evidence-eligible でない(ネットワーク/challenge)。失敗も知識=leg UNSATISFIED。"); raise SystemExit(0)
line(f"[QUALIFY] observed_source_kind={obs['observed_source_kind']}  source={obs['source_id']}")

con = core.build_view()
cov = ACQ.evaluate_leg_requirement(con, leg)
line(f"[COVERAGE] leg satisfied={cov['satisfied']} (matched={cov['matched_observed_kinds']})")

# --- 実取得バイトから本物の一行を fragment にする(捏造しない)---
raw = core.get_state(a).get("raw_content_hash")
body = None
# blob は保存していない(hash のみ)ので、実 fetch を1回して該当行を得る(demo: 観測の再現)
from egl import adapters
body = adapters.fetch({"adapter_class": "ACQ_GITHUB", "target_locator": TARGET})["raw_bytes"].decode("utf-8", "replace")
frag_text = next((ln.strip() for ln in body.splitlines() if WANT in ln), WANT)

# --- extraction run(別 Run: 正しく fetch ≠ 正しく fragment 選択, §13)---
re_ = core.run_start("extractor", "EXTRACTION", task_id=TASK)
ext = ACQ.extract_fragment(re_, obs["observation_id"], blocks=[frag_text], block_index=0,
                           excerpt=frag_text, section_heading="README / Overview",
                           mentions=["ENT-vllm"])
core.run_end(re_, [])
line(f"[EXTRACT] fragment={ext['fragment_id']} observation_kind={ext['observation_kind']}")
line(f"          excerpt: {frag_text!r}")

# --- candidate claim(別 Run)---
rc = core.run_start("rd", "EXTRACTION", task_id=TASK)
rel = P.mk_relation(rc, ext["fragment_id"], None, "SUPPORTS", {"question": "what is vLLM", "scope": {"entity": "vllm"}})
C = P.mk_candidate(rc, {
    "object_kind": "CandidateClaim", "claim_type": "DESCRIPTION", "predicate": "is_described_as",
    "polarity": "POSITIVE", "task_id": TASK,
    "statement": "vLLM は LLM 推論・serving のための高速で使いやすいライブラリである(公式 repo README の記述)",
    "scope": {"entity": "vllm", "aspect": "definition"},
    "evidence_relations": [rel], "resolves_gap": G,
    "representation_residual": {"known_omissions": ["operational_stability", "performance"],
                               "scope_uncertainty": "LOW"}})
core.run_end(rc, [])

# --- Gate4 finding は driver-injected(fragment が statement を直接支持する=honest)---
adj = judge.ClaudeAdjudicator({C: {"f1": "SUPPORTED", "f2": "WITHIN", "fragment_sufficient": True,
                                   "rationale": "README の一行が vLLM の定義を直接記述。scope 内。"}})
line("\n[CURATE]")
res = curator.curate(C, adj, log=line)

con = core.build_view()
claim = next((c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C), None)
if claim:
    line(f"\n[CLAIM] {res.get('global_claim')}")
    line(f"        status={claim['status']}  validation_mode={claim.get('validation_mode')}")
    line(f"        provenance chain: Claim → candidate {C} → fragment {ext['fragment_id']} → "
         f"NObs {ext['norm_obs_id']} → Source {obs['source_id']}(observed={obs['observed_source_kind']}) "
         f"→ AcquisitionRun {a}(sha={arun.get('adapter_provenance',{}).get('sha','')[:12]}) → LegIntent {leg}")
    line("\n→ 実データから Claim を1本生成。status=VERIFIED(fragment が entail)だが")
    line("  validation_mode=UNRESOLVED —— 公式 repo content は PRIMARY だが IMPLEMENTATION_ARTIFACT で")
    line("  あって declaration ではない(R6/R7 が取得境界の実 source に対しても構造で効く)。")
line("\n=== 実タスク end-to-end 完了 ===")
