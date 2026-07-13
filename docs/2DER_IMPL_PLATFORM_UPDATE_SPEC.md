# 2DER 実装基盤アップデート指示書 — 専門分離・二段監査・並列LLM運用・設計エスカレーション

> 原文保存（verbatim, Taka 提供）。Claude Code は本書を独自解釈で設計・分解・実装・判定まで一括で行ってはならない。
> 親 artifact として保存し、決められた分解工程に従う。関連: 監査追補 = 2DER_IMPL_PLATFORM_UPDATE_AUDIT_ADDENDUM.md

## 0. 本書の位置づけ
本書は、2DER自身の開発および2DERが今後扱うAI開発について、実装運用を更新するための親指示書である。単なる教訓文書ではない。以下へ展開される正式仕様として登録する: 親artifact / 分解ITEM / 子ITEM / state transition / role schema / model routing / Economy Operator / audit policy / escalation policy / acceptance test。本書の内容を一つのClaude Codeセッションが独自解釈し、設計、分解、実装、判定まで一括で行ってはならない。

## 1. 更新の目的
1. 開発工程を調査、設計、実装、テストへ分離 2. 開発対象を専門領域ごとに分離 3. 専門性を役割名でなく調査済み情報packetで成立 4. 設計監査・実装監査・テスト確認を二段階 5. 三段目の標準監査は置かない 6. Qwen3.6-35B-A3Bの並列性能を標準利用 7. Qwen3.6-27Bを長文・統合・コーディング候補として実測 8. vLLMのbatch/concurrency/context/token budgetを動的制御 9. LLM処理能力をEconomy Operatorが配分 10. Qwen結果不十分時はClaude Codeへ単純転送せず問題の種類を分類してエスカレーション 11. 人間へのエスカレーションを必要最小限に 12. 「当面」「後で」等の曖昧な時間表現を状態とフラグへ置換。

## 2. 開発工程と専門領域の二軸分離
### 2.1 工程軸
RESEARCH / DESIGN / DESIGN AUDIT / IMPLEMENTATION / IMPLEMENTATION AUDIT / TEST EXECUTION / TEST AUDIT / RELEASE DECISION。
### 2.2 専門領域軸（最低限、別開発単位）
UI / APPLICATION LOGIC / API / DATABASE / FILESYSTEM・DIRECTORY / ENVIRONMENT / CONTAINER / NETWORK / AUTH / SECURITY / LLM SERVING / MODEL ROUTING / OBSERVABILITY / DEPLOYMENT / OPERATIONS / MIGRATION。
UI担当がネットワーク構成を決めてはならない。機能実装担当がディレクトリ構造・Docker・認証方式・GPU割当まで一括で決めてはならない。大きく異なる専門領域を一つのAI作業へ混在させない。

## 3. AI専門家の定義
「あなたは専門家です」というrole promptだけでは専門性は成立しない。AI専門家 = 専門領域 + ユーザー要求 + 現行システム情報 + 領域別事前調査 + 既知制約 + 過去障害 + 公式仕様 + 判断可能範囲 + 禁止範囲 + interface contract。各担当に領域別knowledge packetを与える。
例: `{"domain":"NETWORK","user_requirements":[],"current_topology":{},"ports":[],"containers":[],"official_sources":[],"known_failures":[],"constraints":[],"allowed_decisions":[],"prohibited_domains":["UI","DATABASE_SCHEMA","MODEL_SELECTION"],"required_interfaces":[]}`。専門性はモデル内の人格設定でなく担当が実際に持つ情報で形成する。

## 4. 領域別情報の保存
各専門領域について保存: DOMAIN REQUIREMENT / RESEARCH / CONSTRAINTS / DESIGN / DECISIONS / INTERFACES / OPEN QUESTIONS / IMPLEMENTATION / TEST CONDITIONS / TEST RESULTS / KNOWN FAILURES。実装だけが残ると、ユーザー要求に基づく設計でなくAIの学習分布から一般的説明が再生成される危険がある。

## 5. Interface Contract担当
領域分離すると領域間境界が新たな失敗点になる。万能設計者でなく、領域間契約だけを担当するInterface Contract担当を置く。担当範囲: endpoint / input schema / output schema / error schema / timeout / retry / cancellation / auth requirement / filesystem path / port / process lifecycle / resource requirement / ownership / version compatibility。例: UI→API, API→DATABASE, API→LLM SERVER, LLM SERVER→ENVIRONMENT, OBSERVABILITY→ALL。Interface Contract担当は各領域の内部実装へ介入しない。

## 6. 二段監査
### 6.1 第一段階（L1）: 成果物作成AIが自己確認（明白な欠落/schema違反/内部矛盾/未定義/compile/lint/test起動不能/必須成果物欠落）。第一段階は独立監査とみなさない。
### 6.2 第二段階（L2）: Claude Codeの別contextが監査（ユーザー要求一致/承認仕様一致/実装可能性/隠れた仕様変更/過剰・不足設計/module接続/state transition/concurrency/rollback/testability/acceptance/evidence completeness）。同一Claude Codeセッションが作成と第二監査を兼務してはならない。
### 6.3 三段目: 標準監査は置かない（監査者が仕様膨張/承認外改善要求/過剰一般化/速度低下/責任境界曖昧化）。L2で解決しない場合は第三監査でなく: 追加調査 / 追加evidence / 設計差し戻し / 限定的追加テスト / 人間判断 へ進める。

## 7. 変更クラス
**CLASS-N（新規・未知）**: ESDE/新規architecture/algorithm/評価未確立/reference無し。必須: 設計L1+L2, 実装L1+L2, テストL1+L2。設計は必要に応じ変数・型・関数・module接続まで指定。
**CLASS-H（高影響）**: production/model routing/evidence判定/state machine/GPU制御/DB migration/security/複数repo。完全な二段監査。
**CLASS-M（通常機能追加）**: 既知pattern・影響限定。設計監査L2はinterface変更/複数module/設計不確実性がある場合に実行。
**CLASS-S（小規模）**: 単一module/rollback容易/外部interface不変/既存pattern。必須: 実装L1, テストL1。異常時のみL2起動。
**CLASS-T（自明）**: typo/formatting/comment/behavior不変。機械的diff確認のみ。

## 8. LLM Serving設計
2DERの処理速度はモデル単体能力だけでなくvLLM運用設計に依存。一列処理を標準としてはならない。実測: Qwen3.6-35B-A3B 単発~200 tok/s, 30並列~3,000 tok/s。標準運用へ反映。ただし固定値扱いしない: 最大concurrency/max_num_seqs/max_num_batched_tokens/context length/output token limit/prefill budget/decode budget/queue depth/timeout/retry/priority。モデル・仕事種類・context長・VRAM・TTFT・throughputに応じ変更。

## 9. Economy Operator
vLLM資源配分を仮称Economy Operatorが担当。内容の正しさは判断しない。担当: worker数/concurrency/batch size/max_num_seqs/max_num_batched_tokens/context budget/output token budget/queue priority/timeout/retry/model endpoint選択/prefill・decode負荷/VRAM余裕/task cost予測/task split/backpressure/throughput測定。
入力: `{"task_type":"","task_count":0,"estimated_input_tokens":0,"estimated_output_tokens":0,"latency_priority":"low|medium|high","quality_priority":"low|medium|high","independence_required":true,"model_candidates":[],"current_queue":{},"runtime_metrics":{}}`。
出力: `{"selected_model":"","worker_count":0,"max_concurrency":0,"input_token_budget":0,"output_token_budget":0,"batch_policy":"","timeout_seconds":0,"retry_limit":0,"priority":0,"fallback_route":""}`。
Economy Operatorは設計や判定を行わない。処理資源の配分のみ。

## 10. Qwen3.6-35B-A3Bの初期運用
以下成立まで標準モデルはQwen3.6-35B-A3B: MODEL_SELECTION_TEST_PLAN=APPROVED, MODEL_SELECTION_TEST_RUN=COMPLETE, MODEL_SELECTION_DESIGN_AUDIT_L2=PASS, MODEL_SELECTION_IMPLEMENTATION_AUDIT_L2=PASS, MODEL_SELECTION_TEST_AUDIT_L2=PASS, MODEL_ROUTING_DECISION=ACCEPTED, MODEL_ROUTING_READY=true。「当面Qwen3.6を使う」とは記録しない。READY=trueが立つまでdefault_modelを変更しない。標準用途: 多数の独立調査/仮説列挙/計画候補/ログ分類/schema変換/incident処理/軽中規模コード/独立採点/並列監査/atomic task実行。

## 11. Qwen3.6-27Bのテスト
用途候補: 長文/repo横断/複雑coding/多数成果物統合/長い依存/A3B結果不一致/設計候補統合/複雑デバッグ。性能差は必ず実測: 単発tok/s, 2/4/8/16並列, 最大安定並列数, aggregate tok/s, TTFT, p50, p95, context長別, VRAM, OOM率, timeout率, Pass@1, successful task per minute, per GPU-hour。27Bはdenseゆえ35B-A3Bと同じ30並列を前提にしない。並列上限はテスト結果から決める。

## 12. モデル選別テスト
Claude Codeの印象で決めない。独立したテスト計画で同一入力・条件・採点基準で比較。カテゴリ: 技術調査/設計/設計監査/コーディング/実装監査/ログ解析/procedure error検出/長文理解/repo横断/テスト実行/test result判定/並列処理/単位成功作業あたりコスト。「賢さ」だけでなく 品質×処理時間×並列性×失敗率×再試行率×GPU占有時間 を評価。

## 13. Qwen結果不良時のエスカレーション
無条件にClaude Codeへ転送してはならない。先に失敗の種類を分類する。
- **13.1 FAILURE-EXECUTION**: 設計十分・実装が仕様どおりでない（compile error/test failure/missing function/wrong interface/command error/file omission）→ Claude Code実装監査/実装差し戻し/再実装。
- **13.2 FAILURE-DESIGN**: 仕様・設計が不十分（interface未定義/state transition不足/concurrency不足/rollback未設計/要求矛盾/module境界不適切/acceptance不足/未知領域を一般patternで埋めた）→ Claude Codeへ実装依頼しない/RRI再調査へ戻す/別contextで再設計/複数設計案/Claude Codeは設計監査L2のみ。
- **13.3 FAILURE-KNOWLEDGE**: 外部情報不足 → 再調査/公式文書取得/issue検索/version確認/runtime inspection/実システム観測。
- **13.4 FAILURE-TEST**: テスト手順・環境が不正 → テストを作り直す/実装や方式を失敗扱いしない。
- **13.5 FAILURE-UNKNOWN**: 原因判定不能 → 原因確定を禁止/追加evidence/最小識別実験/人間への限定質問。

## 14. Claude Codeの役割
万能な上位解決者ではない。過去ESDE開発でClaude Code自身の設計・実装起因の誤りが複数発生。役割を限定: 設計監査L2/実装監査L2/テスト監査L2/既知システムの実装/coding/repo操作/diff確認/test実行/evidence整理/revision要求。渡してはならないもの:「問題があるので全部調べて直して判定して」。渡す時点で少なくとも: failure class/approved specification/affected domain/raw evidence/known constraints/prohibited changes/expected output/acceptance criteria をpacket化。設計問題の場合、Claude Codeは解決者でなく監査者。

## 15. 人間へのエスカレーション
全件を送らない。条件を限定: USER_INTENT_CONFLICT / NOVEL_ARCHITECTURE / MULTIPLE_VALID_DESIGNS / IRREVERSIBLE_CHANGE / HIGH_COST_DECISION / SAFETY_OR_LEGAL_IMPACT / EVIDENCE_CONTRADICTION_UNRESOLVED / DESIGN_AUDIT_L2=ESCALATION_REQUIRED / TWO_REDESIGN_ROUNDS_FAILED。送る内容は長い作業履歴でなく: 決めるべき一点/選択肢/各選択肢の差/推奨/不確実性/決定しない場合の既定動作。「全部見てください」と送らない。

## 16. 直感的監査の代替
ユーザーの「結果を信じず違和感から問題を見つける」監査は形式的テストだけでは完全代替できない。近似: **16.1 Dissent Worker**（主結果を知らない別workerへ「この設計/結果が誤っていると仮定し最も疑うべき箇所を3つ挙げよ」）/ **16.2 Assumption Extractor**（暗黙前提を列挙）/ **16.3 Counterexample Search**（成功条件を崩す最小例）/ **16.4 Reality Contact**（実ログ・実行結果・外部仕様との不一致確認）/ **16.5 Surprise Flag**（出力が過度に一貫/失敗原因が一つに即断/対照実験がない/過去結論と一致しすぎ/説明が証拠より長い/raw logより解釈が先）。これらは第三監査でなく、第二監査へ渡す補助evidence。

## 17. 状態遷移
REQUEST_ACCEPTED → CHANGE_CLASSIFIED → DOMAIN_SPLIT_COMPLETE → DOMAIN_RESEARCH_COMPLETE → INTERFACE_CONTRACT_DRAFTED → DESIGN_COMPLETE → DESIGN_AUDIT_L1 → DESIGN_AUDIT_L2 → DESIGN_APPROVED → IMPLEMENTATION_COMPLETE → IMPLEMENTATION_AUDIT_L1 → IMPLEMENTATION_AUDIT_L2 → IMPLEMENTATION_APPROVED → TEST_EXECUTED → TEST_AUDIT_L1 → TEST_AUDIT_L2 → RELEASE_ACCEPTED。
LLM runtime: MODEL_BENCHMARK_PLAN_APPROVED → MODEL_BENCHMARK_RUNNING → MODEL_BENCHMARK_COMPLETE → MODEL_BENCHMARK_AUDITED → ECONOMY_PROFILE_GENERATED → MODEL_ROUTING_DECISION_ACCEPTED → MODEL_ROUTING_READY。

## 18. 実装ITEM候補（登録後に分解、正式子ITEM IDは分解監査後）
1 DOMAIN-SPECIALIZATION-SCHEMA / 2 KNOWLEDGE-PACKET-SCHEMA / 3 INTERFACE-CONTRACT-SCHEMA / 4 CHANGE-CLASSIFIER / 5 TWO-LEVEL-AUDIT-POLICY / 6 CLAUDE-L2-AUDITOR / 7 DISSENT-WORKER / 8 ASSUMPTION-EXTRACTOR / 9 FAILURE-CLASSIFIER / 10 ESCALATION-ROUTER / 11 HUMAN-ESCALATION-PACKET / 12 ECONOMY-OPERATOR / 13 VLLM-RUNTIME-PROFILER / 14 QWEN35-A3B-CONCURRENCY-BENCHMARK / 15 QWEN27-CONCURRENCY-BENCHMARK / 16 MODEL-SELECTION-TEST / 17 MODEL-ROUTING-TABLE / 18 DOMAIN-EGL-INTEGRATION / 19 AUDIT-EGL-INTEGRATION / 20 END-TO-END-ACCEPTANCE-HARNESS。

## 19. 最初にClaude Codeへ要求する作業（実装しない）
1 本書を原文保存 / 2 親artifact ID発行 / 3 EGL登録 / 4 ARTIFACT_REGISTRY登録 / 5 CHANGE_LOG登録 / 6 分解ITEMを一件だけ発行 / 7 既存parallel operations仕様との重複と差分を調査 / 8 統合・拡張・新規対象を分類 / 9 既存ROLE-SCHEMA/INDEPENDENT-JUDGE/PROCEDURE-AUDIT/EGL-INTEGRATIONとの接続点を明示 / 10 分解案を最低3案 / 11 子ITEM正式発行・コード実装・GPU操作・vLLM設定変更は行わない / 12 commit proposalを提示して停止。
報告: 親artifact ID / 分解ITEM ID / EGL evidence ID / CHANGE ID / 保存path / 既存仕様との関係 / 統合候補 / 新規子ITEM候補 / 役割重複 / 未実施事項 / commit proposal。

## 20. 最終原則
2DERの性能は最大モデル一体の賢さでなく: 正しい専門分離 + 十分な事前調査 + 詳細度を調整した設計 + 独立した実装 + 二段監査 + 実処理によるテスト + 並列LLM運用 + 資源配分 + 適切なエスカレーション で決まる。A3B=多数の独立処理を並列実行する基盤。27B=長文・統合・コーディング候補、実測後に役割決定。Claude Codeは失敗時の万能解決者でない。失敗が設計/実装/知識/テストのどこに属するか先に分類し適切な工程へ戻す。人間は全作業の監査者でなく、ユーザー意図・未知設計・不可逆判断・解消不能な矛盾への最終決定者。
