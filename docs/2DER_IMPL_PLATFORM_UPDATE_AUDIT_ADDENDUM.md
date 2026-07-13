# 2DER 実装基盤アップデート指示書 監査追補 — Self-report / Provenance / Resource Failure / 重み共有リスクの閉鎖

> 原文保存（verbatim, Taka 提供）。親 = 2DER_IMPL_PLATFORM_UPDATE_SPEC.md。本追補は親仕様の分解ITEMを正式発行する前に取り込む。

## 0. 位置づけ
本書は「2DER 実装基盤アップデート指示書」への監査追補。新しい思想の追加でなく、EGL/DW/JREV/HBB系で既に確認された失敗パターン（leaf self-report / implementation-to-claim scope expansion / provenance欠如 / stale packet参照 / failure class誤分類 / 同一重み間の盲点相関 / resource failureの実装失敗への誤変換 / 人間介入の未記録）が新運用層で再発するのを防ぐ。親仕様の分解ITEMを正式発行する前に取り込むこと。

## 1. ベンチマークの自己申告禁止
### 1.1 原則
LLMが文章で報告した性能値を運用判断の根拠に使ってはならない。「単発約200 tok/s」「30並列で約3,000 tok/s」「27Bは3/3成功」「A3Bは2/3成功」等の報告文は単独ではREPORTEDを超えない。MEASURED以上への昇格には機械生成されたraw benchmark artifactを必須とする。
### 1.2 VLLM-RUNTIME-PROFILER出力（最低限）
`{"benchmark_run_id":"","model_id":"","model_revision":"","quantization":"","serving_engine":"vllm","vllm_version":"","cuda_version":"","driver_version":"","gpu_models":[],"tensor_parallel_size":0,"max_num_seqs":0,"max_num_batched_tokens":0,"gpu_memory_utilization":0.0,"input_token_distribution":{},"output_token_distribution":{},"request_count":0,"concurrency":0,"warmup_runs":0,"measured_runs":0,"ttft_ms":{},"latency_ms":{},"request_tok_per_sec":{},"aggregate_tok_per_sec":{},"success_count":0,"failure_count":0,"timeout_count":0,"oom_count":0,"truncation_count":0,"raw_request_log_artifact_id":"","raw_server_log_artifact_id":"","environment_artifact_id":"","created_at":""}`。
### 1.3 Claim Scope
性能claimには必ずscopeを付ける。`{"claim":"...","scope":{"model":"","quantization":"","gpu":"","concurrency":0,"input_token_range":"","output_token_range":"","vllm_version":"","max_num_seqs":0,"max_num_batched_tokens":0},"evidence_ids":[],"representation_residual":[]}`。scope外への一般化を禁止。許可: 「この条件では約3,000 tok/sを測定した」。禁止: 「Qwen3.6は30並列で常に3,000 tok/s出る」。
### 1.4 Routing Gate
MODEL_ROUTING_READY=true に追加: BENCHMARK_RAW_ARTIFACT_PRESENT / BENCHMARK_SCOPE_BOUND / BENCHMARK_PROVENANCE_VALID / BENCHMARK_AUDIT_PASS / REPRESENTATION_RESIDUAL_REVIEWED。

## 2. FAILURE-CLASSIFIERの監査とループ制御
### 2.1 原則
自由文で原因を説明するだけのLLMとして実装してはならない。分類はevidence参照付き離散findingで返す。
### 2.2 分類出力schema
`{"failure_classification_id":"","candidate_classes":[{"class":"FAILURE-DESIGN","confidence":0.0,"supporting_evidence_ids":[],"contradicting_evidence_ids":[],"required_missing_evidence":[]}],"selected_class":"","selection_rule":"","unresolved_alternatives":[],"classification_context_id":"","created_at":""}`。自由文は補助説明に限定。
### 2.3 再試行上限
same_class_retry_count / same_artifact_retry_count / same_failure_signature_count を記録。`same_class_retry_count>=2 OR same_failure_signature_count>=2 OR same_revision_pattern_repeated=true` で分類を強制的に疑う → FAILURE_CLASSIFICATION_CHALLENGED → FAILURE_UNKNOWN → RECLASSIFICATION_REQUIRED。同一分類のまま無制限に再実装してはならない。
### 2.4 分類の独立確認
CLASS-N/CLASS-Hでは一つのLLMだけで確定しない。Classifier A / Classifier B / Deterministic pre-check / Independent adjudication を使用。Classifier間不一致はFAILURE-UNKNOWN。

## 3. FAILURE-RESOURCEの追加
### 3.1 新分類 FAILURE-RESOURCE
対象: output truncation / context truncation / timeout / OOM / queue starvation / backpressure / insufficient max_num_seqs / insufficient max_num_batched_tokens / token budget不足 / premature cancellation / rate limit / worker starvation / model endpoint overload / invalid Economy Operator allocation。
### 3.2 分類前の決定的検査
LLM分類より前にPythonで確認: timeout_detected / oom_detected / output_truncated / context_truncated / max_tokens_reached / server_disconnect / queue_timeout / worker_unavailable / rate_limit_hit / resource_budget_exhausted。一つでもtrueなら原則先にFAILURE-RESOURCE候補を立てる。実装失敗や設計失敗へ直接送ってはならない。
### 3.3 Economy Operatorの監査ログ（append-only）
`{"economy_decision_id":"","task_id":"","selected_model":"","worker_count":0,"max_concurrency":0,"max_num_seqs":0,"max_num_batched_tokens":0,"input_token_budget":0,"output_token_budget":0,"timeout_seconds":0,"retry_limit":0,"runtime_metrics_snapshot_id":"","decision_rule_version":"","fallback_route":"","created_at":""}`。成果物は必ずeconomy_decision_idを参照。
### 3.4 変更クラス
Economy Operatorの以下はCLASS-H: routing rule変更 / concurrency上限変更 / token budget policy変更 / timeout policy変更 / retry policy変更 / GPU allocation変更 / fallback route変更 / priority policy変更。

## 4. Knowledge Packetのprovenance
### 4.1 必須識別子
`{"packet_id":"","packet_version":"","domain":"","parent_requirement_id":"","created_at":"","created_by_role":"","created_by_context_id":"","valid_from":"","valid_until":"","supersedes_packet_id":"","source_evidence_ids":[],"source_artifact_ids":[],"claim_ids":[],"open_uncertainty_ids":[],"content_hash":""}`。
### 4.2 自由文packetの禁止
known_failures / constraints / supported_procedures / version compatibility / security assumptions / performance assumptions / architecture assumptions を根拠なし自由文だけで構成してはならない。各項目はclaim/evidenceを参照。`{"constraint_id":"","statement":"","evidence_ids":[],"scope":{},"confidence":"","status":"ACTIVE|SUPERSEDED|CONTRADICTED|UNRESOLVED"}`。
### 4.3 Downstream Binding
全設計・実装・テスト成果物は使用packetを明示: `{"based_on_packet_ids":[],"based_on_packet_versions":[],"packet_hashes":[]}`。packet更新後も古い設計が自動的に正当化されないように。
### 4.4 Stale Packet Gate
packet_version_mismatch / packet_superseded / packet_hash_mismatch / required_evidence_missing / packet_expired のいずれかで成果物を次工程へ進めない。状態: STALE_KNOWLEDGE_PACKET / REBIND_REQUIRED。

## 5. 同一重み監査の残余リスク
### 5.1 原則
別contextは同一推論履歴の共有を避ける効果はある。ただし同じモデル重みの盲点・学習分布・誤推論傾向は共有される。別contextを完全な独立性とみなしてはならない。
### 5.2 リスク表記
Claude作成物を別Claude contextが監査した場合: CONTEXT_INDEPENDENT=true / WEIGHT_INDEPENDENT=false / CORRELATED_BLIND_SPOT_RISK=ACCEPTED を記録。
### 5.3 CLASS-N/CLASS-HのL2監査は三者構成
Creator / Adversarial Reviewer / Independent Adjudicator。これは第三段階監査でなく第二監査の内部構成。Creator=成果物作成。Adversarial Reviewer=誤っていると仮定し 隠れた前提/反例/scope expansion/未検証接続/stale knowledge/missing evidence/test blind spot/interface conflict を探す。Independent Adjudicator=双方を見て事前定義状態から選ぶ: APPROVED / REVISION_REQUIRED / ADDITIONAL_EVIDENCE_REQUIRED / HUMAN_DECISION_REQUIRED。
### 5.4 Weight Diversity
可能ならCLASS-N/CLASS-Hで異なる重み。初期候補: Creator=Qwen3.6, Adversarial Reviewer=別Qwen contextまたは別モデル, Independent Adjudicator=Claude CodeまたはGPT。Claude CodeがCreatorの場合: Adversarial=Qwen, Adjudicator=GPTまたは別重み。同一重みしか使えない場合は残余リスクを明記し人間承認条件を厳しくする。

## 6. Interface Contract担当の境界
定めてよい: endpoint contract / schema / error contract / timeout contract / port / path / lifecycle / resource contract / ownership / version compatibility。定めてはならない: 各領域内部architecture / UI内部 / database内部実装 / network topology内部選択 / container内部構成 / model選定 / resource allocation policy / security内部設計。領域内選択が必要なら該当domain designerへ差し戻す。万能設計者の代替にしてはならない。

## 7. 人間介入ログ
ESCALATION-ROUTERは全人間介入を記録: `{"human_escalation_id":"","parent_item_id":"","trigger_state":"","trigger_reason":"","failure_class":"","decision_required":"","options_presented":[],"recommended_option":"","user_decision":"","decision_timestamp":"","downstream_effects":[],"resolved":false}`。集計: ITEM/domain/failure class/modelごとの介入回数 / redesign round数 / 同一問題の再介入 / Taka判断を要した割合。目的は人間介入を責任逃れの出口にしないこと、2DERが単独で閉じられない領域を測定すること。

## 8. 初期実装優先順位の修正（既存子ITEM候補より前または同時）
BENCHMARK-RUN-LEDGER / BENCHMARK-CLAIM-SCOPE / FAILURE-CLASSIFIER-SCHEMA / FAILURE-CLASSIFIER-RETRY-GUARD / FAILURE-RESOURCE-PRECHECK / ECONOMY-DECISION-LEDGER / KNOWLEDGE-PACKET-PROVENANCE / STALE-PACKET-GATE / WEIGHT-INDEPENDENCE-POLICY / CLASS-NH-TRIAD-AUDIT / HUMAN-ESCALATION-LEDGER。これら無しにMODEL_ROUTING_READY/DOMAIN-SPECIALIZATION/ECONOMY-OPERATORを本運用へ入れてはならない。

## 9. 追加受入条件
AC-BENCH-01 性能claimがraw benchmark artifactを参照。AC-BENCH-02 claimにmodel/量子化/context/concurrency/vLLM設定がscopeとして含まれる。AC-FAIL-01 同一failure classで2回失敗で分類が自動再審査。AC-FAIL-02 timeout/OOM/truncationが実装失敗へ誤分類されない。AC-KP-01 全knowledge packetにID/版/hash/provenance。AC-KP-02 設計成果物から使用packetを逆引き可能。AC-KP-03 superseded packet参照成果物が停止。AC-WEIGHT-01 同一重みの別context監査がweight-independentと記録されない。AC-WEIGHT-02 CLASS-N/HでCreator/Adversarial Reviewer/Adjudicatorが分離。AC-ECON-01 Economy Operator全決定がappend-only記録。AC-HUMAN-01 人間介入回数と理由をITEM単位で集計可能。

## 10. Claude Codeへの追加指示（親仕様の初期登録工程に追加）
1 本追補を親仕様へ関連付けて保存 / 2 既存EGL機構から流用可能な要素を調査（representation_residual / claim scope / packet ID binding / evidence-class gate / independent adjudication）/ 3 再実装せず既存機構を参照・接続できる箇所を明示 / 4 ベンチマーク値を現時点でREPORTEDまたは限定scope MEASUREDとして扱う / 5 FAILURE-RESOURCEを正式分類候補へ追加 / 6 FAILURE-CLASSIFIERの再分類guardを分解案へ入れる / 7 knowledge packet provenanceを必須要件に / 8 CLASS-N/HのL2監査を三者構成として設計 / 9 人間介入ledgerをESCALATION-ROUTERの必須成果物に / 10 子ITEM正式発行・実装・live操作はまだ行わない。
報告: 既存EGL機構の流用候補 / 新規実装が必要な機構 / 重複実装リスク / 追加子ITEM候補 / 受入条件への追加 / 未解決の重み分離条件 / 現在のベンチマークclaimの正確なevidence class。
