# 2DER 時間プロヴェナンス・完成予測基盤 実装指示書 — Claude監査反映版 / Phase-10拡張仕様

> 原文保存（verbatim, Taka 提供）。登録のみ実施。schema実装・既存recordへのretrofit・DB変更・子ITEM正式発行は行わない。
> 依存: HUMAN-ESCALATION-PACKET 完了後 かつ Economy Operator / vLLM Runtime Profiler / モデル比較 / 並列router より前。

本書は、2DERにおける時間情報、進捗計測、完成条件、完成予測を、LLMの印象や自己申告ではなく、EGL・CHANGE_LOG・DE台帳・JREV・commit履歴・受入試験artifactに基づいて管理するための実装指示書である。

## 1. 実装時期の決定
本仕様は今すぐ正式登録する。ただし、現在実装中のESCALATION-ROUTERを中断して割り込ませない。ESCALATION-ROUTERの実装、L1確認、L2監査、commit、EGL登録が完了した直後に、本仕様を次の独立ITEMとして着手する。理由は、本機構が以後のEconomy Operator、モデルベンチマーク、並列worker、完成予測、人間介入計測の共通基盤になるためである。これらを先に実装すると、後から全artifactへ時間bindingを追加する再工事が発生する。
実装順: 1. 現在のESCALATION-ROUTERを完了する。 2. 本書を親artifactとして登録し、TEMPORAL-PROVENANCE-AND-FORECAST ITEMを発行する。 3. 時間schema、event binding、実測速度算出、完成フラグregistryを実装する。 4. その後にEconomy Operator、vLLM Runtime Profiler、モデル比較、並列routerへ進む。

## 2. 目的
LLMが作業量や会話密度から経過時間を推測することを禁止する。すべての重要な状態遷移、実行、監査、承認、成果物に時間情報を持たせる。完成予測を、残ITEM・残受入試験・想定セッション数・実測分布から算出する。完成フラグを自己申告ではなく、受入試験artifactとJREV裁定へbindingする。暦時間、能動作業時間、ツール待機、人間待機を分離する。見積もり誤差を継続的に測定し、domain・change class・task type別に改善する。

## 3. 基本原則
### 3.1 時間の推測禁止
開始時刻、現在時刻、対象event IDが存在しない場合、LLMは「何日目」「数週間経過」「近いうち」等を回答してはならない。許可される回答は、timestampから機械計算された値、またはUNKNOWNのみとする。
### 3.2 自己申告速度の禁止
「現在の速度」「最近の実装速度」「1日あたりの進捗」は、Claude Codeの印象から生成してはならない。EGL event log、ITEM完了、DE起票、JREV通過、commit時刻を参照し、算出式と参照record IDを併記する。
### 3.3 暦時間と処理量の分離
Claude Codeが直接評価可能なのは、主に1セッションあたりの処理量と各taskの実測時間である。週あたりの稼働セッション数はユーザー都合に依存するため、暦日付は条件付き換算としてのみ提示する。
### 3.4 完成フラグの自己宣言禁止
完成フラグは、Claude Codeが文章でPASSを宣言しただけでは立たない。各フラグは、事前登録された受入条件、run artifact、evidence chain、JREV裁定にbindingする。

## 4. 必須時間schema
（原文では表として提示。重要record は少なくとも recorded_at + timezone を持ち、task は started_at / completed_at / wall_clock_seconds、active_work / tool_wait / human_wait の分離、対象event ID・参照record IDを保持する。）

## 5. 実測速度の算出
実測速度は以下のrecordから機械的に算出する: ITEMのIN_PROGRESS遷移時刻とDONE遷移時刻 / DE起票時刻 / CHG起票・commit・push時刻 / JREV開始・裁定時刻 / 受入試験run開始・終了時刻 / Claude session内のtool実行時間 / 人間承認要求・承認時刻。
最低限、以下を domain・change class・task type 別に集計する: sample_count / median duration / p50・p80・p95 / min・max / active work・wall clock比 / 再実装回数 / 監査差し戻し回数 / 人間介入回数 / 見積もり誤差。

## 6. 完成予測の出力契約
完成予測の主答は日付ではなく、残工程量と想定セッション数とする: 残ITEM数 / 残受入試験数 / critical path上のITEM / 並列実行可能なITEM / 必要なJREV裁定数 / 想定セッション数 / UNKNOWN-VARIANCEのITEM数 / 既存実績に基づくp50・p80・p95処理量。
暦日付は「週Nセッション稼働」と明示した条件付き換算に限り許可する。類似実績が存在しないCLASS-N ITEMは数字を捏造せず、UNKNOWN-VARIANCEと記録する。

## 7. 完成フラグregistry
完成条件の集合自体を版管理する。フラグの削除、緩和、追加はCHG・DE・JREVを必要とし、黙って変更してはならない。

## 8. Completion Definitionの版管理
完成条件集合はCOMPLETION-DEFINITION artifactとして登録し、completion_definition_id、version、hash、created_at、approved_by、required_flag_idsを持たせる。完成間際にフラグを減らす行為は逆方向のscope縮小として監査対象とする。追加する場合も、その追加理由と既存見積もりへの影響を記録する。

## 9. 受入条件
AC-TIME-01 重要recordの100%にrecorded_atとtimezoneが存在する。AC-TIME-02 taskのstarted_at/completed_atからwall_clock_secondsを再計算できる。AC-TIME-03 active work・tool wait・human waitを分離できる。AC-EST-01 実測速度の全数値に算出式と参照record IDがある。AC-EST-02 類似実績なしのITEMがUNKNOWN-VARIANCEとして出力される。AC-EST-03 暦日付が週Nセッションの仮定なしに提示されない。AC-FLAG-01 各完成フラグが受入試験artifactとJREV裁定を参照する。AC-FLAG-02 completion definitionの版とhashを逆引きできる。AC-FLAG-03 フラグ集合の黙示的削除・緩和が検出される。AC-FORECAST-01 p50/p80/p95と前提を提示できる。

## 10. 既存Phase-10との接続
本仕様はESCALATION-ROUTERの完了後、Economy Operatorおよびモデルbenchmarkより前に実装する。依存関係: ESCALATION-ROUTER完了→人間待機時間と介入時刻の記録先が確定 / TEMPORAL-PROVENANCE実装→Economy Operatorの配分時間・待機時間を測定できる / →vLLM benchmarkのrun時間と条件を正式にbindingできる / →基盤完成予測をself-reportから機械計算へ移行できる。

## 11. Claude Codeへの初期指示
ESCALATION-ROUTERの現在作業を完了した後、以下のみを実施し、実装前に停止する。 1. 本書を原文保存し、親artifact IDを発行する。 2. TEMPORAL-PROVENANCE-AND-FORECAST分解ITEMを一件発行する。 3. 既存EGL、CHANGE_LOG、ROADMAP、JREV、git履歴に存在するtimestampを棚卸しする。 4. 追加必須フィールドと既存フィールドの差分を示す。 5. 過去recordへretrofitする範囲と、今後のみ必須化する範囲を分ける。 6. completion definition v1候補を作る。 7. 実測速度算出式、参照record、UNKNOWN-VARIANCE規則を定義する。 8. 子ITEM正式発行・コード実装・DB移行はまだ行わない。

## 12. 推奨実装単位
TEMPORAL-EVENT-SCHEMA / TIME-BINDING-VALIDATOR / ACTIVE-WORK-AND-WAIT-LEDGER / HISTORICAL-VELOCITY-CALCULATOR / ESTIMATION-BASIS-BINDING / UNKNOWN-VARIANCE-POLICY / COMPLETION-DEFINITION-REGISTRY / COMPLETION-FLAG-GATE / FOUNDATION-FORECAST-REPORT / TEMPORAL-EGL-INTEGRATION。

## 13. 最終判断
本仕様は現在案件の全完了まで待たせない。ESCALATION-ROUTERという現在のatomic workを完了した直後に挿入する。理由は、今後の主要案件すべてが時間・速度・完成条件を必要とし、後回しにすると新規artifact全体へのretrofit工数が増えるためである。一方、現在の実装を途中で止めて割り込ませる必要もない。現在taskを閉じてから境界で切り替えることが、一担当一責務とatomic taskの原則にも一致する。

> 運用注記（Taka 指示 2026-07-14）: ESCALATION-ROUTER は既に完了済み。境界となる atomic work は HUMAN-ESCALATION-PACKET とし、その完了直後に本仕様を次の独立 ITEM として着手する。本ターンでは登録のみ（子ITEM発行・schema実装・retrofit・DB変更は行わない）。
