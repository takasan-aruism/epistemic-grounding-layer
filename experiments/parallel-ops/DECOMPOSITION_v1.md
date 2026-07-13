# ITEM-2DER-PARALLEL-OPS-DECOMPOSITION — 成果物 v1 (子ITEM候補一覧)

**⚠️ AC-14 兼務記録**: 本分解は router 未構築のため **単一 Claude context が提案者(3案)と監査者を兼務**して生成した。
これは仕様が是正対象とする非独立性そのものであり、**移行期 bootstrap** として明示記録する。ここで作るのは
**候補(candidate_name のみ)**であり、**正式子 ITEM ID は発行しない**(spec §5/§15 — 監査 + Taka 承認後)。
真の独立監査は「独立 Judge/worker-isolation の子 ITEM」実装後に再実施すべき(下記 sequencing の先頭)。

parent_item_id: ITEM-2DER-PARALLEL-OPS / parent_artifact: ART-e655b2cd72 / schema: ART-2817f0525a

---

## 分解案 3 案 (spec §12 Phase2: 最低3案)

### Proposal A — 役割層で切る (role-layer decomposition)
最終フロー(§14)の各役割 = 1 子 ITEM。
`DS-INTAKE / RRI-RESEARCH / RRI-PLAN / RRI-PLAN-AUDIT / DW-EXECUTOR / INDEPENDENT-JUDGE / PROCEDURE-AUDIT / PYTHON-ROUTER / EGL-INTEGRATION / DS-STATE-UPDATE`。
- 長所: フローと 1:1、責務が明快。 短所: packet schema が横断し重複、router が全役割に依存 → 依存集中、着手順が不明瞭。

### Proposal B — 契約(schema)先行の bottom-up
先にデータ契約と state machine を固め、その上に worker を載せる。
`ROLE-SCHEMA / RESEARCH-PACKET / PLAN-PACKET / ATOMIC-TASK-SCHEMA / EXECUTION-PACKET / JUDGE-PACKET / ESCALATION-PACKET / PARALLEL-ROUTER(state machine+transition validator) / EGL-INTEGRATION / (以降 worker 群) / MODEL-ROUTING / MODEL-SELECTION-TEST / CONCURRENCY-BENCHMARK / ACCEPTANCE-HARNESS / MIGRATION`。
- 長所: §6 の schema・§4 の遷移固定が土台、hermetic 試験しやすい、AC-01..AC-14 を schema/validator で強制できる。 短所: 動く物が出るまで長い。

### Proposal C — 独立性・安全先行 (independence & safety first)
直近 ITEM-0015 の穴(判定非独立 AC-08)を最初に閉じる順。
`INDEPENDENT-JUDGE(+JUDGE-PACKET) / PROCEDURE-AUDIT / ROLE-SCHEMA(context/task 分離の最小核) / EGL-INTEGRATION(evidence class 昇格制御) / ATOMIC-TASK+EXECUTION-PACKET / PARALLEL-ROUTER / RESEARCH+PLAN+PLAN-AUDIT worker / MODEL-ROUTING / MODEL-SELECTION-TEST / CONCURRENCY-BENCHMARK / ACCEPTANCE-HARNESS / MIGRATION`。
- 長所: **最大リスク(自己判定)を最初に是正**、小さく検証可能、Phase4 dry-run(§12)を早期に回せる。 短所: full 並列運用は後半。

---

## 兼務監査 (self-audit, 独立でない — 要再監査)

| 観点 | 指摘 |
|---|---|
| gaps | 3案とも **APPROVAL-GATE / authority 統合**を明示子 ITEM にしていない(既存 twoder.authority を再利用する前提を候補に足すべき)。**benchmark artifact 読込**(§7 固定値禁止)が B/C で MODEL-SELECTION と混在。 |
| overlaps | PROCEDURE-AUDIT と PLAN-AUDIT が名称近接だが別物(手順準拠 vs 計画健全性)。ROLE-SCHEMA と各 PACKET schema の境界要明確化。 |
| dependency_cycles | PARALLEL-ROUTER ↔ 各 PACKET は「router は schema に依存、schema は router に非依存」で非循環化必須。JUDGE は EXECUTION+PROCEDURE-AUDIT に依存(逆流禁止)。 |
| granularity | Proposal A は粒度粗(1役割=多機能)。B/C は schema 単位で適正。 |
| missing_acceptance | 各候補に AC-01..AC-14 の対応を明示すること(下記候補表で付与)。 |
| missing_rollback | worker 系は state 巻き戻し、router は transition validator の feature flag で無効化を rollback とする。 |
| migration_conflicts | 既存 submit.py / dispatch.py / operator.py / de_admission / intervention / conformance と**二重化させない**(EGL-INTEGRATION は既存 de_admission/intervention を SoR として再利用、新 SoR 禁止=DE-0223 の教訓)。MODEL-ROUTING は既存 execution_economy と整合。 |

**監査の限界(明示)**: 提案者=監査者=単一 Claude。独立性なし → この監査は**暫定**。独立 Judge 子 ITEM 実装後、または Taka/外部レビューで再監査を要する。

---

## 推奨子 ITEM 候補セット (candidate_name のみ、正式ID未発行)

Proposal C(独立性先行)を基軸に、B の schema 土台を組み込んだ hybrid。各候補は DECOMPOSITION_SCHEMA の CHILD_ITEM_CANDIDATE 準拠。

| # | candidate_name | role_layer | 主 deliverable | depends_on | 主 AC | requires_live | authority |
|---|---|---|---|---|---|---|---|
| 1 | ROLE-SCHEMA | PYTHON | context/task-id/output-schema 分離の最小核 + 兼務記録 hook | — | AC-01,08,14 | no | AUTO |
| 2 | JUDGE-PACKET | JUDGE | §6.5 judge packet schema + verdict enum | ROLE-SCHEMA | AC-05,06 | no | AUTO |
| 3 | INDEPENDENT-JUDGE | JUDGE | 実施と別 context の判定器(誘導文除去、verdict 限定) | JUDGE-PACKET | AC-08,05,06 | (判定にLLM使う場合)yes-gated | REQUIRES_APPROVAL |
| 4 | PROCEDURE-AUDIT | JUDGE | 手順準拠監査(実行 vs 計画の一致、既存 conformance と接続) | ROLE-SCHEMA | AC-05,07 | no | AUTO |
| 5 | EXECUTION-PACKET | DW | §6.4 (interpretation=null 強制) + stdout/stderr/exit/hash/env 保存 | ROLE-SCHEMA | AC-03,07 | no | AUTO |
| 6 | ATOMIC-TASK-SCHEMA | RRI-PLAN/DW | §6.3 + 原子性 validator(複数意味操作禁止) | ROLE-SCHEMA | AC-02 | no | AUTO |
| 7 | RESEARCH-PACKET | RRI-RESEARCH | §6.1 schema | ROLE-SCHEMA | AC-10 | no | AUTO |
| 8 | PLAN-PACKET | RRI-PLAN | §6.2 schema + PLAN-AUDIT hook | RESEARCH-PACKET | AC-01 | no | AUTO |
| 9 | ESCALATION-PACKET | RRI | 未解決入力のみ受ける追加実験 packet(判定文非入力) | JUDGE-PACKET | AC-06 | no | AUTO |
| 10 | EGL-INTEGRATION | EGL | 全 stage 並走記録 + evidence class 昇格制御(実施者昇格禁止)。**既存 de_admission/intervention を SoR 再利用** | ROLE-SCHEMA | AC-04,05 | no | AUTO |
| 11 | PARALLEL-ROUTER | PYTHON | state machine + 許可遷移固定 + queue/worker isolation/timeout/retry/schema validation | 1-10 schema | AC-01,04,09 | no | AUTO |
| 12 | MODEL-ROUTING | PYTHON | model 選択を benchmark artifact から読む(固定埋め込み禁止) | PARALLEL-ROUTER | AC-11 | no | AUTO |
| 13 | MODEL-SELECTION-TEST | (test) | §9 カテゴリ別選別テスト(調査/計画/コード/判定/性能) | MODEL-ROUTING | AC-10,11 | yes-gated | REQUIRES_APPROVAL |
| 14 | CONCURRENCY-BENCHMARK | (test) | §7 8/16/30 並列 isolation + tok/s/OOM/timeout 実測 artifact | PARALLEL-ROUTER | AC-09 | yes-gated | REQUIRES_APPROVAL |
| 15 | ACCEPTANCE-HARNESS | (test) | AC-01..AC-14 hermetic 受入 harness | 1-11 | AC-01..14 | no | AUTO |
| 16 | MIGRATION | (all) | 既存 submit/dispatch/operator を段階移行、二重 SoR 回避 | 全部 | AC-12,13 | (最終)yes-gated | REQUIRES_APPROVAL |

追加(監査 gap 由来): `APPROVAL-GATE-INTEGRATION`(既存 twoder.authority + scoped token を router に接続) を候補に含める。

## sequencing (§12 Phase 対応)
- **Phase2 完了条件**: 本候補セットの**独立監査**(現状は兼務のため暫定) + Taka 承認 → 正式子 ITEM ID 発行。
- **Phase3 (schema+router)**: 1 ROLE-SCHEMA → 2,5,6,7,8,10 schema群 → 11 PARALLEL-ROUTER → 15 ACCEPTANCE-HARNESS。
- **独立性先行(推奨)**: 3 INDEPENDENT-JUDGE + 4 PROCEDURE-AUDIT を **schema 群と並行で最優先**(AC-08 の穴を早期に閉じる)。
- **Phase4 dry-run**: ITEM-0015 の sleep level2/level1/AB を既存ログ入力に工程を通し、「level2 初回=方式失敗と確定しない/procedure error か insufficient evidence へ/level1 提案/A/B を限定 MEASURED」を検証。
- **Phase5 hermetic → Phase6 限定 live(承認token) → Phase7 本運用**。

## open_questions (人間承認が要る論点)
1. PHASE-09 を既存 ROADMAP-2DER-EVOLUTION-v0.1 内に置くか、別 ROADMAP にするか。
2. INDEPENDENT-JUDGE の「独立」を **別 model** まで要求するか、**同一 model 別 context/seed** で足りるとするか(§2.1)。
3. 子 ITEM 数(16+1)の粒度は適切か、統合/分割すべきか。
4. live を伴う 13/14/16 の承認方針(scoped token の operation_class 設計)。

## child_ids_issued: false (正式子ITEM IDは未発行 — 監査+承認後)
