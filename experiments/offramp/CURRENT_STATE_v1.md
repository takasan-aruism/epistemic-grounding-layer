# Off-ramp CURRENT STATE — evidence-backed inventory v1

> Taka 追記 2。曖昧語禁止。VERIFIED は受入試験(regression) or JREV 参照がある場合のみ。Claude の説明だけを根拠にしない。
> status: VERIFIED / PARTIAL / REGISTERED_ONLY / NOT_IMPLEMENTED / UNKNOWN。実状態を実コード/実台帳から確認して記述。
> 重要: 多くの機構は **hermetic に VERIFIED(=機構は動く)** だが、**live loop で Claude なしに回る capability は別**。
> `claude_code_currently_substitutes` がその真実を担う。

| capability_id | status | acceptance_test_ids | jrev_ids | artifact_ids / DE | known_gap | claude_code_currently_substitutes |
|---|---|---|---|---|---|---|
| memory-retention | PARTIAL | (none dedicated) | none | MEMORY.md, DESIGN_EVIDENCE_LEDGER.jsonl | 自律 consumer 無し。台帳は live だが読むのは私 | YES — 私が MEMORY.md を読み状態を再構成 |
| state-management | PARTIAL | (none dedicated) | none | ROADMAP_REGISTRY.jsonl, roadmap_registry.py | set_status/register を driving するのは私 | YES — 全 status 遷移を私が呼ぶ |
| provenance | VERIFIED(機構) | test_knowledge_packet_provenance.py | none | DE-0256, artifact_registry(content_hash) | 呼出しは私。autonomous binding 無し | PARTIAL — 私が register/admit を invoke |
| audit-routing | VERIFIED(機構) | test_escalation_router.py(12/12), test_two_level_audit_policy.py(12/12) | none | DE-0263, DE-0264 | live 配線無し | YES — 実運用の routing は私 |
| failure-classification | VERIFIED(機構) | test_failure_resource_precheck/schema/retry_guard.py | none | DE-0251, DE-0252, DE-0253 | live worker 未接続 | YES — 失敗分類を私が手で | 
| temporal-provenance | VERIFIED(機構) | temporal 10 tests + parity sweep 10/10 | none | DE-0276..DE-0285 | wait-ledger 実データ未投入。ts は実運用で self-typed | YES — ts を私がタイプ(=REPORTED) |
| completion-gates | VERIFIED(機構) | test_completion_flag_gate.py, test_completion_definition_registry.py | none | DE-0282, DE-0283, CDEF-2DER-v1(hash b935ce10) | 実 CDEF-2DER-v1 は JREV 未参照ゆえ 0/7 = **未完成**(正直) | PARTIAL |
| rri-decomposition | PARTIAL | (rri tests 存在, off-ramp 用受入無し) | none | rri.* (PHASE-06) | 現行実装の task decomposition を driving していない | YES — task 分解は私 |
| worker-routing | PARTIAL | test_parallel_router.py(11/11), test_model_routing_table.py(11/11) | none | DE-0248, DE-0273, dw/dispatch.py, dw/adapters.py(QWEN_LIVECODER) | live worker が outer loop でない(コメント "CLAUDE was still the OUTER LOOP") | YES — 私が worker |
| shell-execution | PARTIAL | (dw.executor に test 要確認) | none | dev-workcell/dw/executor.py(run_command: 実 subprocess + security policy) | 実行器は存在するが autonomous 駆動でない | YES — Bash を私が実行 |
| test-execution | PARTIAL | dw dispatch adapter(QWEN_LIVECODER "real subprocess test") | none | dev-workcell/dw/dispatch.py | autonomous 駆動でない | YES — test を私が実行 |
| judge-integration | VERIFIED(機構) | test_independent_judge.py | none | DE-0244 | live judge worker 未接続。異種重み裁定者 pool 無し | YES — 私が判定/同一重み |
| egl-binding | VERIFIED(live) | egl/test_admission.py | JREV-0001..0007(EGL 近傍) | de_admission(sole writer, claim ceiling 実発火 DE-0234 REJECT) | 呼出しは私 | PARTIAL — writer は autonomous, caller=私 |
| commit-proposal | NOT_IMPLEMENTED(autonomous) | (none) | none | (git 手動 + prose 要約) | 自律 commit proposal 生成無し | YES — 全て私(prose + git) |
| control-surface | PARTIAL | (UI endpoint 受入無し) | none | twoder/webui.py(483行: submit + run_next + read-only roadmap/resolve view + auth), memory 上 thin UI(tailscale+auth) live | observability grade。approval/scoped-token 面・off-ramp 報告面は未 | YES — Taka は承認/報告で私と話す(UI でない) |

## Gap 要約（off-ramp 障害の核）
- **報告窓口**: 素材(forecast/roadmap/DE/intervention/flags)は VERIFIED 機構で揃うが、Taka 向け read-only 報告面が
  未(control-surface PARTIAL)。→ workstream A で埋まる(決定的、GPU 不要)。
- **承認窓口**: authority scoped-token 機構は存在(過去 ITEM-0015 で使用)だが、Taka が私を介さず発行する UI が無い。
  → workstream B。
- **git 窓口**: commit-proposal NOT_IMPLEMENTED(autonomous)。policy 上 commit=Taka。→ workstream C は設計止まり。
- **実装窓口**: worker-routing / shell-execution / test-execution / judge-integration は機構 VERIFIED または実行器
  存在(PARTIAL)だが、**Claude が outer loop**。live worker が counterfactual に一周して初めて移譲。→ workstream D/E。
- **異種重み監査**: judge-integration は同一重み(私)。HETEROGENEOUS_L2_AUDITOR_AVAILABLE 未成立。CLASS-H/N の除去
  対象外(pool 依存)。

## 全体判定
off-ramp の**機構層は広く VERIFIED**、しかし **live-loop capability(Claude なしで一周)は 15 中 0 が VERIFIED**。
`commit-proposal` は autonomous 版が NOT_IMPLEMENTED。全 off-ramp フラグ現在 **UNMET**。「機構がある」を「Claude 依存
除去」と読み替えない(本 doc の存在理由)。
