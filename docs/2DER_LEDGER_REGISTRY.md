# 2DER 台帳登記簿（LEDGER REGISTRY / 実測 2026-07-22）

- **これは何か:** 2DER 全 5 repo の *台帳*（.jsonl の記録簿）を 1 冊に登記したもの。
  台帳がこのシステムの根幹であり、大半の開発が何かしらの台帳に紐づく。特定部分の深掘りで
  全体像を忘れる「AI 痴呆」が起きても、この 1 冊から *何をしたかったか* を復元できるようにする。
- **生成:** `egl/structure/s10_ledger_registry.py`（決定論・再生成可能）→ `LEDGER_REGISTRY.jsonl`
- **検査:** `python3 s10_ledger_registry.py --check`（宣言 sole 書き手 vs 本番複数 / live 読みだが真の書き手ゼロ）
- **claim ceiling:** 書き手は静的解析（2 層・本番/テスト分離）。`purpose` は発明せず genesis 件名と docstring の raw。
- **典拠 DE:** DE-0489（de_admission.py 経由で ADMITTED）

## §1. 全体像

台帳 **47 本** / git 追跡 33・追跡外 14

| 生死 | 本数 | 意味 |
|---|---|---|
| LIVE | 21 | live path から読まれている |
| IDLE_HAS_WRITER | 8 | 書き手はあるが live から読まれない |
| ORPHAN | 7 | 真に誰も書かない箱（実験残渣） |
| REPLICA_SHADOW | 9 | 4層 bootstrap の複製（canonical は egl のみ） |
| SHIPMENT_COPY | 2 | 出荷束/docs 同梱の複製 |

> **最も重要な運用台帳ほど git 追跡外にある。** 実行の一次記録（events / records）は
> `.gitignore` 下の単一ファイルにしか無い。消えれば実行史が消える（耐久性は Taka 裁定事項）。

## §2. LIVE 台帳（live path が実際に読む）

| 台帳 | 行 | 追跡 | 本番書き手 | 確信 | 放置日 | 目的（genesis 件名）|
|---|--:|:-:|---|:-:|--:|---|
| `twoder/audit/ARTIFACT_REGISTRY.jsonl` | 4517 | T | artifact_registry.py | ✓ | 8 | edge5 ID+artifact coverage (DE-0179/0180/0181, CHG-0001): re |
| `egl/data/events.jsonl` | 2001 | · | core.py | ✓ | 2 | [追跡外] EGL core: append-only event log (SoR) + rebuildabl |
| `ds/ds_events.jsonl` | 1008 | · | phase0.py | ~ | 1 | [追跡外] DS Phase 0 — 「頭脳」より先に「箱」を作る(SRC-A §6.17 / §6.20)。  |
| `rri/rri_records.jsonl` | 680 | · | intent_record.py | ~ | 2 | [追跡外] RRI record store (DE-0180): mint + resolve canonic |
| `dev-workcell/events.jsonl` | 674 | · | workcell.py | ~ | 4 | [追跡外] DW walking skeleton の本体 — event-sourced Task Unit  |
| `egl/DESIGN_EVIDENCE_LEDGER.jsonl` | 485 | T | de_admission.py | ✓ | 0 | EGL Phase 1a: walking skeleton + component decomposition + r |
| `twoder/audit/ROADMAP_REGISTRY.jsonl` | 349 | T | roadmap_registry.py | ✓ | 0 | DE-0188/CHG-0008: ROADMAP_REGISTRY (roadmap/phase/item, stab |
| `dev-workcell/data/pending_actor.jsonl` | 334 | · | dispatch.py | ✓ | 4 | [追跡外] Persist the fact that the loop is waiting for a sp |
| `twoder/audit/CHANGE_LOG.jsonl` | 195 | T | artifact_registry.py | ✓ | 0 | edge5 ID+artifact coverage (DE-0179/0180/0181, CHG-0001): re |
| `dev-workcell/run_sor/events.jsonl` | 160 | · | workcell.py | ~ | 15 | [追跡外] DW walking skeleton の本体 — event-sourced Task Unit  |
| `twoder/failure_recurrence.jsonl` | 109 | · | failure_memory.py | ~ | 7 | [追跡外] Record each match, then annotate non-blocking matc |
| `egl/data_jrev0003/events.jsonl` | 40 | · | core.py | ✓ | 17 | [追跡外] EGL core: append-only event log (SoR) + rebuildabl |
| `egl/audit_backlog.jsonl` | 34 | T | ai_work_system_loop_demo.py | ~ | 16 | EGL Phase 1a: walking skeleton + component decomposition + r |
| `egl/data_gate4/events.jsonl` | 31 | · | core.py | ✓ | 16 | [追跡外] EGL core: append-only event log (SoR) + rebuildabl |
| `egl/data_acq_task/events.jsonl` | 23 | · | core.py | ✓ | 16 | [追跡外] EGL core: append-only event log (SoR) + rebuildabl |
| `egl/data_sleepmode_claim/events.jsonl` | 22 | T | core.py | ✓ | 15 | EGL: Sleep Mode external-spec acquisition — boundary passed, |
| `egl/data_acq_live/events.jsonl` | 12 | · | core.py | ✓ | 17 | [追跡外] EGL core: append-only event log (SoR) + rebuildabl |
| `egl/REVIEW_LEDGER.jsonl` | 11 | T | test_self_grounding.py | ~ | 1 | EGL: JREV property-level review + R5/R2 fixes + guard non-gu |
| `egl/data_sleepmode_acq/events.jsonl` | 7 | T | core.py | ✓ | 15 | EGL: Sleep Mode external-spec acquisition — boundary passed, |
| `twoder/failure_memory.jsonl` | 7 | T | failure_memory.py | ~ | 10 | FAILURE_MEMORY_GUARD: read-only failure-history consult in t |
| `twoder/audit/COMPLETION_DEFINITION_REGISTRY.jsonl` | 1 | T | completion_definition_registry.py | ~ | 9 | COMPLETION-DEFINITION-REGISTRY: version+hash completion defi |

確信 ✓=当該パスへの write を確認 / ~=参照+書込みありだがパス未確認 / ✗=書き手なし

## §3. 死んだ台帳（畳む/保存の判断材料。判断は Taka）

### 3.1 ORPHAN — 真に誰も書かない（実験残渣、live 参照ゼロ）

| 台帳 | 行 | genesis 日 | 目的（件名）|
|---|--:|---|---|
| `egl/afe_operators_ledger.jsonl` | 12 | 2026-07-08 | AFE step 2: Aruism-core operators compiled + independent |
| `egl/ENERGIZATION_OBSERVATIONS.jsonl` | 7 | 2026-07-19 | DE-0438: first real-repo energization run (option A) + e |
| `egl/optimization_heuristics.jsonl` | 5 | 2026-07-07 | EGL: DD-ARCH-4 Naming (2DER) + optimization-heuristics l |
| `egl/ontology_sources.jsonl` | 4 | 2026-07-08 | AFE (Axiomatic Frame Engine): source registration + pre- |
| `egl/ENERGIZATION_LEDGER.jsonl` | 2 | 2026-07-19 | DE-0438: first real-repo energization run (option A) + e |
| `egl/process_property_set.jsonl` | 2 | 2026-07-07 | EGL: Process Optimizer contracts (§11/§12/§13) + open ga |
| `egl/optimization_candidates.jsonl` | 1 | 2026-07-07 | EGL: OPT-001 batching ADOPTED — model-switch overhead re |

### 3.2 IDLE_HAS_WRITER — 書き手はあるが live から読まれない

| 台帳 | 行 | genesis 日 | 目的（件名）|
|---|--:|---|---|
| `egl/experiments/metaframe_verification.jsonl` | 18 | 2026-07-07 | PHASE 0: verification trust root — VERIFICATION_RECORD r |
| `egl/PROBLEM_LOG.jsonl` | 8 | UNTR |  |
| `egl/AUTONOMY_LEDGER.jsonl` | 5 | 2026-07-11 | 2DER autonomous loop v0 — SLICE-6: client-usable surface |
| `egl/metaframe_ledger.jsonl` | 5 | 2026-07-07 | EGL: Meta-Frame Factory walking slice complete — inducti |
| `dev-workcell/authorizations.jsonl` | 3 | 2026-07-07 | DW: ASSIGNMENT_AUTHORIZATION minimal impl — closes the O |
| `egl/INVESTIGATIONS.jsonl` | 1 | UNTR |  |
| `egl/PROBLEMS.jsonl` | 1 | UNTR |  |
| `egl/optimization_triggers.jsonl` | 1 | 2026-07-07 | EGL: Process Optimizer contracts (§11/§12/§13) + open ga |

### 3.3 複製の影 — bootstrap 複製 / 出荷コピー（消しても canonical は残る）

| 台帳 | 行 | 種別 |
|---|--:|---|
| `rri/DESIGN_EVIDENCE_LEDGER.jsonl` | 12 | REPLICA_SHADOW |
| `dev-workcell/DESIGN_EVIDENCE_LEDGER.jsonl` | 7 | REPLICA_SHADOW |
| `ds/DESIGN_EVIDENCE_LEDGER.jsonl` | 3 | REPLICA_SHADOW |
| `dev-workcell/REVIEW_LEDGER.jsonl` | 2 | REPLICA_SHADOW |
| `ds/audit_backlog.jsonl` | 2 | REPLICA_SHADOW |
| `rri/audit_backlog.jsonl` | 1 | REPLICA_SHADOW |
| `dev-workcell/audit_backlog.jsonl` | 0 | REPLICA_SHADOW |
| `ds/REVIEW_LEDGER.jsonl` | 0 | REPLICA_SHADOW |
| `rri/REVIEW_LEDGER.jsonl` | 0 | REPLICA_SHADOW |
| `egl/docs/SUBMIT_2026-07-21/02_ledger/REVIEW_LEDGER.jsonl` | 10 | SHIPMENT_COPY |
| `egl/docs/SUBMIT_2026-07-21/05_de/DE-0474_DE-0475.raw.jsonl` | 2 | SHIPMENT_COPY |

## §4. 書き手規律の質（台帳ごとにバラバラ、が測定で出た）

| 台帳 | 本番書き手 | 宣言sole | 行 |
|---|---|:-:|--:|
| `egl/DESIGN_EVIDENCE_LEDGER.jsonl` | de_admission.py | ✓ | 485 |
| `twoder/audit/ROADMAP_REGISTRY.jsonl` | roadmap_registry.py |  | 349 |
| `twoder/audit/CHANGE_LOG.jsonl` | artifact_registry.py |  | 195 |
| `twoder/audit/ARTIFACT_REGISTRY.jsonl` | artifact_registry.py |  | 4517 |
| `twoder/failure_memory.jsonl` | failure_memory.py |  | 7 |
| `egl/REVIEW_LEDGER.jsonl` | — なし |  | 11 |

> DE 台帳は書き手を `de_admission.py` 単一に縛った（"ONLY sanctioned writer"）から 484 件で重複0。
> `REVIEW_LEDGER`/`audit_backlog` は本番書き手ゼロ = 手で埋める前提のまま放置された。
> **規律の有無がそのまま台帳の健全性に出ている。**

