# 2DER END-TO-END WIRING MAP（実測 2026-07-22）

- **導出:** `egl/structure/EDGE_INVENTORY.jsonl`（1,313 辺）/ `REACHABILITY.jsonl` / `EXECUTION_EVIDENCE.jsonl`
- **手法:** live entrypoint 4 本からの AST 到達性 + 呼出点 + 実行痕跡。**LLM 不使用**
- **claim ceiling:** 呼出点は実在する（行番号つき）。`LIVE` は「呼ばれうる ∧ 当該系統に実行痕跡がある」であり、**個々の呼出が毎回通ることは主張しない**

---

## §1. 規模

```
Python 全体          427 files / 44,914 LOC
live path 到達        68 files /  9,810 LOC   = 21.8%
コンポーネント間の辺   1,313
  LIVE                       113   8.6%
  TEST_ONLY_ISLAND           812  61.8%
  IMPLEMENTED_UNWIRED        362  27.6%
  WIRED_EXECUTION_UNRESOLVED  17   1.3%
  WIRED_UNENTERED              9   0.7%
```

---

## §2. live entrypoint（`wired` の根）

```
twoder/webui.py              HTTP。/api/submit /api/run_next /api/operator/advance
twoder/submit.py             直接入力 conductor
twoder/operator.py           operator ループ
dev-workcell/dw/dispatch.py  外側ループ
```
最大到達深度 4。

---

## §3. 前向き経路（submit の 1 往復）

実行痕跡 **117/117 トレース全件**に現れる（`twoder/runs/*.json`）。

```
/api/submit → twoder/submit.py:submit()

 ①DS      submit.py:137  → ds/ds/phase0.py::record_dialogue_event
          submit.py:158  → ds/ds/phase1.py::dialogue_state_packet
            └ trace: DS_INPUT_REF / DS_OUTPUT_PACKET_REF / DS_THREAD_BRANCH_CANDIDATES

 ②RRI     submit.py:111  → rri/rri/admission_request.py::detect
          (context_binding / request_type は d1 到達)
            └ trace: RRI_INPUT_REF / RRI_CONTEXT_BINDING / RRI_RESOLVED_INTENT / RRI_REQUEST_TYPE

 ②'RRI formal  submit.py:99 → twoder/rri_formal.py::run_formal_validation
            ⚠ WIRED_UNENTERED — `if formal_candidates:` の内側、既定は空
            └ trace: RRI_FORMAL_VALIDATION は 0/337

 ③EGL     submit.py:179  → egl/egl/self_grounding.py::answer_question
          submit.py:123  → egl/egl/de_admission.py::admit_design_evidence
          submit.py:387  → egl/egl/result_packet.py::admit_forward_claims
            └ trace: EGL_QUERY / EGL_SOURCE_REFS / EGL_CURRENT_CLAIMS / EGL_OPEN_GAPS

 ④DW      submit.py:364  → dev-workcell/dw/dispatch.py::next_legal_operation
          submit.py:47   → dev-workcell/dw/workcell.py::_read_events
            └ trace: DW_TASK_ID / NEXT_LEGAL_OPERATION / DISPATCH_RESULT / ACTOR_ROLE
```

## §4. 戻り経路（close_loop）

```
twoder/return_loop.py:23 → dw/workcell.py::build_result_packet
                    :28 → egl/egl/result_packet.py::ingest_result_packet
                    :33 → rri/rri/residual_update.py::form_residual
                    :38 → ds/ds/phase0.py::record_dialogue_event
```
**戻り経路は 4 系すべてに繋がっている。ループは閉じている。**

## §5. operator / dispatch 経路

```
twoder/operator.py:43  → dw/workcell.py::derive_state
                  :82  → dw/conformance.py::check
                  :150 → dw/dispatch.py::dispatch_once
                  :32  → twoder/gpu_inspection.py::collect
                  :108 → twoder/intervention.py::record_intervention
dev-workcell/dw/dispatch.py:63  → twoder/execution_economy.py::select_actor
dev-workcell/dw/adapters.py:140 → twoder/runtime_supervisor.py::supervised_text_call
```
**DW→TWODER の逆方向の辺が 3 本あり、依存は相互である**（層構造ではない）。

## §6. 実行器（唯一シェルを触る場所）

```
twoder/runtime_inspection.py:111 → dw/executor.py::run_command
twoder/gpu_inspection.py:24      → dw/executor.py::run_command
```
`dw/executor.py` は **live かつ、いかなるテストからも import されていない**
（`CONTRADICTIONS.jsonl` / `LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST`）。

## §7. 取得境界

```
twoder/research_acquisition.py:65 → egl/egl/acquisition.py::acquire     [LIVE]
twoder/runtime_inspection.py:168  → egl/egl/acquisition.py::acquire     [LIVE]
twoder/gpu_inspection.py:156      → egl/egl/acquisition.py::acquire     [LIVE]
```
ただし `egl/egl/adapters.py`（`fetch_github` / `fetch_http_static`）は
**`SUPPORT_OFF_LIVE_PATH`**。取得スパインは live だが、外部取得アダプタ本体は到達していない。

## §8. 実行ファネル（`dev-workcell/events.jsonl` 674 件）

```
CREATE 147 → PLAN 140 (95%) → GENERATE 90 (64%) → AUDIT 40 (44%) → DISPOSE 16 (40%)
                                                              COMPLETE 1
```
**タスク 147 件に対し COMPLETE 到達は 1 件。**
（`DISPOSE` の内訳は未解析。「成功 1 件」とは読めない。`PROGRESS.md` U13）

## §9. 欠けている辺

```
twoder/task_selector.py::select_next
    LIVE な呼出元 = 0（テストと実験ハーネスのみ）
dev-workcell/dw/workcell.py::create_task
    LIVE な呼出元 = twoder/submit.py:408 と twoder/experiment_candidate.py:116 の 2 本のみ
    どちらも task_selector を経由しない
```
→ 詳細は `2DER_MISSING_EDGES.md`。
