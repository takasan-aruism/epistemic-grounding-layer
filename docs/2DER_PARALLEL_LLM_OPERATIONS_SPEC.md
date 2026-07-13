# 2DER 分離型LLM運用基盤 実装仕様書

> 原文保存。Claude Code は本書を独自に要約・再解釈して既存 ITEM へ吸収してはならない。
> 親 artifact として原文を保存し、決められた分解工程に従う。以下は Taka 提供の原文（verbatim）。

## 0. 文書の位置づけ

本書は、2DERにおいて複数LLMを並列処理資源として利用し、調査、実験計画、実行、判定、記録を役割分離して運用するための実装仕様である。

本書は方針メモではない。2DERへ正式登録し、実装計画、子ITEM、受入試験へ展開する親仕様書として扱う。

Claude Codeは本書の内容を独自に要約・再解釈して既存ITEMへ吸収してはならない。原文を親artifactとして保存したうえで、決められた分解工程に従うこと。

## 1. 実装目的

2DER内で以下を自動的に実行できる状態を作る。

1. 作業要求をDSが受け取る
2. 調査担当を複数並列で起動する
3. 調査結果から複数の実験計画候補を作る
4. 計画作成者と実施者を分離する
5. 計画を原子的なタスクへ分割する
6. 各実施者には原則一つの操作だけを渡す
7. Pythonルーターが成果物を次工程へ受け渡す
8. EGLが各工程のraw evidenceを記録する
9. 実施者とは別の判定者が結果を判定する
10. 判定不能時は失敗確定せずエスカレーションする
11. モデル別の品質、速度、失敗率を蓄積する
12. 実測結果に基づいてモデルを自動選別する

## 2. 最重要原則

### 2.1 役割分離
以下を同一AIセッションに担当させてはならない。
* 調査
* 実験計画
* 実験実施
* 手順準拠監査
* 結果判定
* 追加実験計画
* 最終状態更新

同一モデルを使用すること自体は禁止しない。ただし、別context、別task ID、別入力packet、別出力schemaを使用し、前工程の推論過程を共有させない。

### 2.2 一担当一責務
一つのプロンプトに「調査し、計画し、実行し、結果を判定し、失敗したら修正する」のような複合指示を渡さない。以下のように分割する。
調査する / 計画案を作る / 計画を監査する / 一つの操作を実行する / 成果物を検証する / 結果を判定する / 追加実験を設計する

### 2.3 実験失敗と方式失敗を区別する
一つの実験で異常が出ても、方式全体の失敗を確定してはならない。状態を最低限、以下に分ける。
OBSERVED_FAILURE / PROCEDURE_ERROR / CAUSE_UNRESOLVED / INSUFFICIENT_EVIDENCE / METHOD_CONTRADICTED / ESCALATION_REQUIRED / ACCEPTED

### 2.4 LLMの規律に依存しない
以下の指示は制御機構として扱わない（補助文にとどめる）。
* 慎重に考えること / 教訓を忘れないこと / 断定しないこと / 冷静に判断すること / 過去の失敗を参照すること

実際の制御は以下で行う。
* 入力制限 / 出力schema / 役割分離 / 権限制御 / 状態遷移制限 / 独立context / Pythonによる検証 / EGLによる証拠固定

## 3. システム構成

### 3.1 DS
DSは全体の受付、ルーティング、状態更新を担当する。
責務: 要求受付 / 親WORK ITEMの作成 / 既存ITEMとの重複確認 / リスク区分 / 必要な処理経路の選択 / RRIへの調査依頼 / DWへの実行許可 / 判定結果を受けた状態更新 / 人間承認が必要な箇所の停止 / エスカレーション先決定。
禁止: 自分で調査を完結する / 自分で実験計画を作り、そのまま実行する / raw logだけを見て原因を確定する / EGL記録なしにITEMをDONEへ変更する。

### 3.2 RRI
RRIは調査、仮説生成、実験計画候補の作成を担当する。内部で最低限 RRI-RESEARCH / RRI-PLAN / RRI-PLAN-AUDIT / RRI-ESCALATION-PLAN を分離する。
RRI-RESEARCH: 公式ドキュメント調査 / GitHub Issue調査 / GitHub PR調査 / バージョン差分確認 / 既知制約確認 / 正常手順確認 / 失敗事例確認 / 復旧手順確認 / 競合仮説列挙。
RRI-PLAN: research packetだけを入力にする / 複数の識別可能な実験案を作る / 各実験の前提、操作、観測、停止条件を定義する / どの結果ならどの仮説が弱まるかを記述する。
RRI-PLAN-AUDIT: 計画の漏れ / 対照条件 / 手順依存 / バージョン不一致 / 原子性 / 再現性 / ログ保存設計 / rollback設計 を監査する。
RRI-ESCALATION-PLAN: 未解決時の追加実験だけを作る。入力は 未排除仮説 / 不足証拠 / 矛盾観測 / 実行済みタスク一覧 / 禁止された再試行 のみ（元の判定文は入力にしない）。

### 3.3 DW
DWは承認済みatomic taskの忠実実行だけを担当する。
責務: 指定コマンド実行 / 指定ファイル作成 / 指定テスト実行 / stdout, stderr保存 / exit code保存 / 時刻保存 / 環境情報保存 / 実行前後の状態保存 / rollback実行 / raw artifact提出。
禁止: 原因判定 / 次の実験の独自作成 / 手順変更 / 省略 / 成功条件の変更 / 失敗時の独自回避 / ITEM状態の変更 / EGL evidence classの昇格。
想定外時は次で停止: EXECUTION_DEVIATION / UNEXPECTED_STATE / MISSING_PREREQUISITE / SAFETY_STOP。

### 3.4 EGL
EGLは工程ではなく全工程に並走する。記録対象: 親要求 / 調査結果 / 参照source / 実験計画 / 計画監査 / 承認token / atomic task / 実行command / stdout / stderr / exit code / 生成物hash / environment snapshot / 判定 / エスカレーション / rollback / 最終状態。
EGLは解釈よりraw evidenceを優先する。evidence class を区別: REPORTED / INFERRED / OBSERVED / MEASURED / REPRODUCED / ACCEPTED / CONTRADICTED。MEASUREDへの昇格は、実施者が行ってはならない。

## 4. Python制御層
Python制御層は、LLM間のバケツリレーを担当する。仮称: 2DER Parallel Operations Router。
担当: ID発行 / queue管理 / worker割当 / concurrency制御 / request送信 / timeout / retry / schema validation / 必須artifact確認 / hash確認 / task state遷移 / context分離 / prompt template選択 / model routing / output収集 / EGL書込要求 / judgeへのpacket生成 / escalation packet生成。
Pythonは意味的な最終判定を行わない。許可する状態遷移だけを固定する。
遷移例: CREATED → RESEARCHING → RESEARCH_COMPLETE → PLAN_DRAFTED → PLAN_AUDITED → APPROVAL_REQUIRED → APPROVED → EXECUTING → RAW_RESULT → PROCEDURE_AUDIT → JUDGING → ACCEPTED / ESCALATION_REQUIRED / PROCEDURE_ERROR。
禁止する直接遷移: EXECUTING → ACCEPTED / RAW_RESULT → METHOD_CONTRADICTED / RESEARCHING → EXECUTING / PLAN_DRAFTED → DONE。

## 5. ID体系
本仕様書登録時に、既存registry規則に従って正式IDを発行する。推奨する親artifact名: 2DER_PARALLEL_LLM_OPERATIONS_SPEC。推奨する親ITEM名: ITEM-2DER-PARALLEL-OPS。正式ID番号はregistry側の決定的処理で発行すること。Claude Codeが手作業で番号を推測してはならない。
親仕様登録後、直ちに全子ITEMを発行してはならない。最初に次の分解ITEMを一件だけ作る: ITEM-2DER-PARALLEL-OPS-DECOMPOSITION。このITEMの成果物として、子ITEM候補一覧を作る。
想定される子ITEM候補: PARALLEL-ROUTER / ROLE-SCHEMA / RESEARCH-PACKET / PLAN-PACKET / ATOMIC-TASK-SCHEMA / EXECUTION-PACKET / PROCEDURE-AUDIT / JUDGE-PACKET / ESCALATION-PACKET / EGL-INTEGRATION / MODEL-ROUTING / MODEL-SELECTION-TEST / CONCURRENCY-BENCHMARK / ACCEPTANCE-HARNESS / MIGRATION。
正式な子ITEM IDは、分解案が監査・承認された後に発行する。

## 6. 成果物schema
### 6.1 Research Packet
```
{ "research_id":"", "parent_item_id":"", "scope":"", "model":"", "worker_id":"", "sources":[],
  "version_constraints":[], "supported_procedures":[], "known_failures":[], "open_issues":[],
  "workarounds":[], "uncertainties":[], "candidate_hypotheses":[], "raw_notes_artifact":"", "created_at":"" }
```
### 6.2 Plan Packet
```
{ "plan_id":"", "parent_item_id":"", "research_packet_ids":[], "hypotheses":[], "experiments":[],
  "controls":[], "expected_observations":[], "stop_conditions":[], "rollback_plan":[], "required_logs":[],
  "prohibited_actions":[], "human_approval_required":false }
```
### 6.3 Atomic Task Packet
```
{ "task_id":"", "plan_id":"", "single_objective":"", "prerequisites":[], "input_artifacts":[],
  "allowed_commands":[], "prohibited_commands":[], "expected_output_schema":"", "timeout_seconds":0,
  "retry_limit":0, "rollback_task_id":"", "executor_role":"DW" }
```
一つのAtomic Taskに複数の意味的操作を入れない。悪い例: 「serverを停止し、設定を変更し、再起動し、生成結果を評価する」。良い例: TASK-A serverを停止 / TASK-B 停止確認 / TASK-C 設定変更 / TASK-D hash確認 / TASK-E 起動 / TASK-F health確認 / TASK-G 生成結果保存。
### 6.4 Execution Result
```
{ "execution_id":"", "task_id":"", "executor_model":"", "started_at":"", "ended_at":"", "commands_executed":[],
  "exit_codes":[], "stdout_artifacts":[], "stderr_artifacts":[], "state_before":{}, "state_after":{},
  "deviation":false, "deviation_reason":"", "interpretation":null }
```
interpretationは常にnullとする。
### 6.5 Judge Packet
```
{ "judgement_id":"", "plan_id":"", "task_ids":[], "research_packet_ids":[], "execution_result_ids":[],
  "procedure_audit_id":"", "available_verdicts":["SUPPORTED","CONTRADICTED","PROCEDURE_ERROR","INSUFFICIENT_EVIDENCE","ESCALATION_REQUIRED"] }
```

## 7. 並列実行設計
現行Qwen3.6-35B-A3Bは実測上、単一処理 約200 tok/s、30並列時総量 約3,000 tok/s。この実測値を当面の運用前提とするが、固定値としてコードへ埋め込まず benchmark artifact から読み込む。
初期worker pool: 最大同時30 / 通常開始8 / 調査6〜12 / 計画候補生成3〜6 / 独立監査2〜4 / 実施worker task依存 / 判定worker 2以上。
同じ質問を30workerへ送らない。並列化軸を明示する: source別 / 仮説別 / version別 / subsystem別 / repo別 / failure mode別 / test case別。

## 8. モデル運用方針
### 8.1 当面の標準モデル
実テストで優位性が確定するまでは Qwen3.6-35B-A3B を標準モデルとする。使用対象: 調査 / 仮説列挙 / 計画候補 / atomic task生成 / ログ分類 / 軽中規模コード / 並列監査 / incident処理。
### 8.2 27B dense候補
Qwen3.6-27B dense は専門用途候補: 長文統合 / 大規模repo理解 / コーディング / 長い依存関係 / 複雑なデバッグ / A3B結果の不一致統合 / 最終候補生成。「27Bだから上位」と固定しない。実測で決める。
### 8.3 現在の暫定実測
Qwen3.6-35B-A3B: Pass@1 2/3, 速度 約167.6 tok/s。Qwen3.6-27B: Pass@1 3/3, 速度 約74.2 tok/s。Level 1 sleep/wake: 正常、garbageなし、切替約0.5〜0.6秒。
この結果はテスト件数が少ないため、モデル選別の確定根拠にはしない。evidence classは限定的なMEASUREDとし、一般的優位性は未確定とする。

## 9. モデル選別テスト計画
Claude Code自身がモデルを選んではならない。モデル選別用の独立ITEMを作成する。
対象カテゴリ: 9.1 調査（source精度/version条件認識/既知Issue発見率/誤情報率/競合仮説網羅率）/ 9.2 実験計画（対照条件/原子性/再現性/rollback/停止条件/証拠保存/誤断定抑制）/ 9.3 コーディング（Pass@1/テスト通過率/compile成功率/repo破壊率/修正回数/diff量/長context性能/複数repo理解）/ 9.4 判定（procedure error検出率/false failure率/false success率/insufficient evidence認識率/escalation精度/代替仮説保持率）/ 9.5 性能（tok/s/aggregate tok/s/TTFT/p50/p95/VRAM/concurrency別性能/timeout率/OOM率/retry率）。
モデルルーティングはこの結果を参照して決定する。

## 10. 判定分離
判定者に渡さない: 実施者の原因推測 / 計画担当の最終予想 / 過去の暫定結論 / 「成功のはず」「バグのはず」等の誘導文。
判定者へ渡す: research facts / approved plan / raw execution results / procedure audit / control results / predefined verdict options。
方式失敗を確定できる条件: 手順準拠確認済み / 必要な対照条件あり / 再現あり / 主要代替仮説の排除 / version一致 / ログ欠損なし / rollback結果確認 / 独立判定一致。満たさない場合は ESCALATION_REQUIRED。

## 11. Claude Codeの役割
現段階でClaude Codeは実装担当である。
行ってよいこと: 親仕様書の原文保存 / registryへの登録処理 / 分解ITEMの作成 / schema実装 / Python router実装 / テスト作成 / 承認済み子ITEMの実装 / commit proposal作成 / raw実行結果の保存。
行ってはならないこと: 親仕様の意味を独自変更 / 自分で全子ITEMを即時発行 / 自分で計画し、自分で実施し、自分で成功判定する / 小規模A/Bだけでモデル選別を確定する / evidence classを独断で昇格する / 未承認live operationを行う / 実施結果から方式全体の失敗を即断する。
移行期間中に複数役を兼務する場合、各役割を別task、別context、別artifactとして分離し、兼務であることをEGLへ記録する。

## 12. 実装順序
Phase 0 現状監査: 受付/調査/計画/計画監査/ID発行/実施/判定/EGL記録/CHG記録/状態更新/commit/rollback を誰が担当しているか一覧化。同一Claude Codeセッションが兼務している箇所を明示。
Phase 1 親仕様登録: 本書を原文保存 / artifact ID発行 / ARTIFACT_REGISTRY登録 / EGL登録 / CHANGE_LOG登録 / 分解ITEMを一件だけ発行。この段階では実装しない。
Phase 2 分解計画: 複数の独立workerで分解案（最低3案）。別workerが 漏れ/重複/依存/粒度/受入条件/rollback/migration を監査。人間承認後に子ITEM ID発行。
Phase 3 schemaとrouter: packet schema / state machine / ID発行 / queue / worker isolation / EGL hook / artifact hash / timeout / retry / transition validator を先に実装。
Phase 4 read-only dry run: 実システムを変更せず既存ログを入力に工程全体を通す（例: sleep level 2失敗事例 / level 1再試験 / Qwen対Coder A/B）。期待: level 2初回試験を方式失敗と確定しない / procedure error か insufficient evidence へ送る / level 1追加試験を提案 / A/B結果を限定的MEASUREDとして記録 / モデル優位性を一般化しない。
Phase 5 hermetic実験: 一時環境、mock server、fixture repo。productionへ触れない。
Phase 6 限定live試験: 人間承認token付きで実施。
Phase 7 本運用: DS受付からRRI、DW、独立判定、EGL記録まで自動化。

## 13. 受入試験
AC-01 役割分離: 同一task IDで計画と実施と判定が行われていない。
AC-02 原子性: 一つのatomic taskに複数の意味的操作が含まれていない。
AC-03 証拠保存: 全実行にstdout, stderr, exit code, time, environment, hashがある。
AC-04 EGL並走: 各state transitionにEGL evidence IDがある。
AC-05 失敗確定抑制: 単一異常ログだけでMETHOD_CONTRADICTEDへ遷移できない。
AC-06 エスカレーション: 証拠不足時にESCALATION_REQUIREDへ遷移する。
AC-07 実施者制限: DW出力に原因判定が含まれていない。
AC-08 独立判定: 実施者と判定者のcontext IDが異なる。
AC-09 並列動作: 8, 16, 30並列でtask isolationが保たれる。
AC-10 モデル記録: 各taskにmodel, quantization, context length, 速度, 結果が記録される。
AC-11 モデル選別非固定: 小規模テストだけでrouting ruleを恒久変更できない。
AC-12 rollback: live試験失敗時に既知正常構成へ戻せる。
AC-13 再現性: evidence IDから同じ実験条件を再構成できる。
AC-14 Claude兼務可視化: 移行期間中にClaude Codeが複数役を担当した場合、その兼務が記録される。

## 14. 最終運用フロー
```
USER / SYSTEM REQUEST → DS INTAKE → PARENT ITEM → RRI-RESEARCH WORKER POOL → RESEARCH PACKETS
→ RRI-PLAN WORKER POOL → PLAN CANDIDATES → RRI-PLAN-AUDIT → DS / PYTHON APPROVAL GATE
→ ATOMIC TASK IDS → DW EXECUTOR POOL → RAW RESULTS → PROCEDURE AUDIT → INDEPENDENT JUDGE
→ ACCEPT / ESCALATE / PROCEDURE ERROR → DS STATE UPDATE
EGL records every stage in parallel
```

## 15. 今回Claude Codeへ要求する最初の作業
以下だけを行い、停止すること。
1. 本仕様書を原文のまま正式ファイルとして保存
2. 正式artifact IDをregistry規則に従って発行
3. EGL, ARTIFACT_REGISTRY, CHANGE_LOGへ登録
4. 分解専用ITEMを一件だけ発行
5. 現在の役割兼務状況を監査
6. 分解ITEMの成果物schemaを作成
7. 変更予定ファイル一覧を提示
8. commit proposalを提示
9. 子ITEM発行、router実装、live操作はまだ行わない
報告には次を含める: 親artifact ID / 分解ITEM ID / EGL evidence ID / CHANGE ID / 保存path / registry entry / 現在の役割担当表 / Claude Codeが兼務中の役割 / 次工程で分離する役割 / 未実施事項 / commit proposal。

---
## 補足（Taka, 原文）
完成形は「DSからRRI、DWへ処理が流れ、EGLが全工程を記録する」で概ね正しいが、正確には単純な DS→RRI→EGL→DW の直列ではない。EGLは工程の一段ではなく全工程に並走する証拠台帳。判定機能は独立して必要。DS自身が最終判断を行う場合でも、実施を担当したDS contextとは分離する。最終形: **DS受付 → RRI調査・計画 → Python分解・配布 → DW実施 → 独立Judge → DS決定**、EGLは全体の横に常時存在。
