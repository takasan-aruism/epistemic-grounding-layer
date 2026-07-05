#!/usr/bin/env python3
"""Phase 1b 取得境界 実ネットワーク end-to-end デモ(§19 step 12)。

実 adapter(ACQ_GITHUB / ACQ_HTTP_STATIC)で本物の source を取得し、取得境界を通す:
LegIntent(immutable)→ 実 fetch → AcquisitionRun(実 transport/content status)→ SearchResultSnapshot
→ Source Qualification(observed_source_kind)→ Policy Matcher → leg requirement 判定。

実データで示す:
  (1) 実 GitHub 取得が SUCCESS/OBSERVED、blob SHA を provenance に持つ
  (2) AB-1 counter-factual(実バイト): 同じ github 取得でも required=OFFICIAL_DOCS なら
      observed=OFFICIAL_REPOSITORY ≠ 要求 → 取得成功でも UNSATISFIED
  (3) required=OFFICIAL_REPOSITORY なら SATISFIED
ネットワーク不通時は adapter が NETWORK_ERROR/TIMEOUT を付し、leg は正しく UNSATISFIED(失敗も知識)。
"""
import os
from pathlib import Path
os.environ["EGL_DATA_DIR"] = str(Path(__file__).resolve().parent / "data_acq_live")
for f in ["events.jsonl", "state.sqlite", ".idlock"]:
    p = Path(os.environ["EGL_DATA_DIR"]) / f
    if p.exists():
        p.unlink()

from egl import core, source_policy as SP, acquisition as ACQ
def line(s=""): print(s)

TARGET = "https://github.com/vllm-project/vllm/blob/main/README.md"
line("########## Phase 1b 取得境界 実ネットワークデモ ##########")
line(f"target: {TARGET}\n")

r = core.run_start("rd", "ACQUISITION", task_id="TASK-VLLM-EVID")

# --- leg A: required=OFFICIAL_REPOSITORY(正しい分類)---
legA = ACQ.mk_leg_intent(r, plan_id="PLAN-1", task_id="TASK-VLLM-EVID",
                         required_source_kind="OFFICIAL_REPOSITORY", target_locator=TARGET,
                         adapter_class="ACQ_GITHUB",
                         source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"], source_policy_version=1,
                         expected_entity="vLLM", purpose="vLLM 公式 repo 証拠",
                         search_method="REPOSITORY_FILE_FETCH", query=["README"],
                         scope_locator="vllm-project/vllm", revision="main")
aA = ACQ.acquire(r, legA)                         # 実 fetch
arunA = core.get_state(aA)
line(f"[ACQ A] transport={arunA['transport_status']} content={arunA['content_status']} "
     f"http={arunA['http_status']} hash={(arunA.get('raw_content_hash') or '')[:20]}")
line(f"        provenance sha={arunA.get('adapter_provenance',{}).get('sha','')[:16]}")
ACQ.mk_search_result_snapshot(r, legA, aA, result_count=1, result_refs=[TARGET])
obsA = ACQ.emit_observation_if_eligible(r, aA)
line(f"        observed_source_kind={obsA['observed_source_kind'] if obsA else None}")

# --- leg B: required=OFFICIAL_DOCS だが target は github repo(AB-1 誤分類の実データ counter-factual)---
legB = ACQ.mk_leg_intent(r, plan_id="PLAN-1", task_id="TASK-VLLM-EVID",
                         required_source_kind="OFFICIAL_DOCS", target_locator=TARGET,
                         adapter_class="ACQ_GITHUB",
                         source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"], source_policy_version=1,
                         expected_entity="vLLM", purpose="(誤)公式ドキュメント要求に repo を当てる",
                         search_method="REPOSITORY_FILE_FETCH", query=["README"],
                         scope_locator="vllm-project/vllm", revision="main")
aB = ACQ.acquire(r, legB)
ACQ.mk_search_result_snapshot(r, legB, aB, result_count=1, result_refs=[TARGET])
ACQ.emit_observation_if_eligible(r, aB)
core.run_end(r, [])

con = core.build_view()
sA = ACQ.evaluate_leg_requirement(con, legA)
sB = ACQ.evaluate_leg_requirement(con, legB)
line(f"\n[COVERAGE A] required=OFFICIAL_REPOSITORY → satisfied={sA['satisfied']}  {sA['reasons']}")
line(f"[COVERAGE B] required=OFFICIAL_DOCS(誤)→ satisfied={sB['satisfied']}")
line(f"             理由: {sB['reasons']}")
line("\n→ AB-1 実データ実証: 同じ実 GitHub 取得が SUCCESS/OBSERVED でも、required と observed が食い違えば")
line("  coverage は満たさない。『予定した種別 ≠ 実際に観測した種別』が実ネットワークでも構造で効く。")
line("\n=== 取得境界 実ネットワークデモ完了 ===")
