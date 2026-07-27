# 実装 → 設計/監査: Build 9C — **Qwen planner は呼ばれず `CLAUDE_BARRIER` で止まった（外れ方は (b)）**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.5）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD9C_SPEC_WEBUI_SUBMIT_AND_ADVANCE.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD9C_APPROVED.md`（写しで観測）/ `CC_2DER_USAGE_GUIDE.md`
- **本文書は観測を書きます。判定・評価・提案をしません。**
- **★トークンは本文書・ログ・argv のどこにも書いていません**（§0-1）。ファイルから読んで直接使い、コピーを作っていません。

## 1. 段0 — CLI で作った task への `RUN NEXT`（1回）【監査:IMPL】
```json
{"refused": true, "blocked": false, "runnable": true, "dispatched": false,
 "reason": "task TASK-2DER-D6A93450 is not the current runnable submit task (TASK-2DER-8ADC31CF)",
 "task_id": "TASK-2DER-D6A93450"}
```
**拒否されました（CC-α の予想どおり）。`dispatched: false`＝dispatch も state 変更も起きていません。**

## 2. 段1 — webui から投入（1回・依頼文は Build 9B と同一・1文字も変えていません）【監査:IMPL】
```
request_type          : BUILD_CAPABILITY
acquisition_method    : DW_IMPLEMENTATION
runnable              : true      blocked : false
next_legal_operation  : PLAN
task_id               : TASK-2DER-D6A93450        ← ★Build 9B(CLI) と同一
egl_source_refs       : ["DE-0484"]
```

### 2-1. ★予想が外れました（task の同一性）
CC-α の予想は **「返る（Build 9B と別の新しい task）」** でしたが、**返ったのは Build 9B と同じ `TASK-2DER-D6A93450`** です。
**投入口を CLI から webui に変えても、同じ依頼文からは同じ task id が返りました。**
**なぜ同一になるかは、私の観測だけでは判定材料が不足しています**（task id の決定規則を私は確認していません）。

## 3. 段2 — `RUN NEXT` を1回だけ【監査:IMPL】
```
dispatched : false
reason     : CLAUDE_BARRIER
nlo        : {"task_id": "TASK-2DER-D6A93450", "state": "CREATED", "operation": "PLAN",
              "actor_role": "MANAGER", "actor_id": "CLAUDE", …}
state      : task_id=TASK-2DER-D6A93450 / goal=<投入した依頼文>
```
- **`/api/run_until_barrier` は使っていません。`/api/run_next` を1回だけです。**
- **run-gate を回避していません**（環境変数・直接呼び出しによる迂回をしていません）。
- **`AUTH.gate("DW_MACHINE_DISPATCH")` の判定には到達していません**（その手前の `CLAUDE_BARRIER` で止まっています）。

## 4. ★外れ方の区分（実装源 §4）【監査:IMPL】
実装源は外れ方を2つ用意していました。**観測されたのは (b) です。**
| 区分 | 観測 |
|---|---|
| (a) planner が走ったが `validate_plan` が拒否した（`reasons` が出る） | **該当しません**（`validate_plan` に到達していません） |
| **(b) planner がそもそも呼ばれず Claude barrier に落ちた** | **★該当します**（`reason: CLAUDE_BARRIER` / `auto_served` なし） |

**`auto_served: QWEN_BUILD_PLANNER` は返っていません。`PLAN` の担い手は `actor_id=CLAUDE` のままです。**

## 5. 予想と実際（全項目）
| # | 項目 | 予想 | 実際 | 判定 |
|---|---|---|---|---|
| 段0 | CLI task への RUN NEXT | `refused: true` | **`refused: true`** | **当たり** |
| 段1 | `request_type` | `BUILD_CAPABILITY` | **`BUILD_CAPABILITY`** | **当たり** |
| 段1 | `DW_TASK_ID` | 返る（**新しい task**） | **返るが Build 9B と同一 task** | **★外れ** |
| 段1 | run-gate | `runnable: true` | **`runnable: true`** | **当たり** |
| 段2 | `AUTH.gate(...)` | `auto: true` | **到達せず** | **判定不能** |
| 段2 | `PT.plannable()` | `False` | **到達せず** | **判定不能** |
| **段2** | **`auto_served`** | **`QWEN_BUILD_PLANNER`** | **無し（`CLAUDE_BARRIER`）** | **★外れ** |
| 段2 | `derive_state` | `PLANNED` 相当 | **`CREATED` のまま** | **★外れ** |

## 6. 守った禁止事項
- **投入は各段1回だけ。再投入していません。**
- **依頼文を1文字も変えていません**（Build 9B と同一＝投入口だけを変えた対照）。
- **run-gate を回避していません。拒否を記録して止めました。**
- **1段だけです。worker まで走らせていません。**
- **本番コードを変更していません。**
- **トークンを文書・ログ・argv に出していません。コピーを作っていません。**

## 7. 観測の限界（事実として）
- **各段1回ずつしか見ていません。** 1回の観測で「この経路は Qwen planner に到達しない」と断定しません。
- **task id が投入口をまたいで同一になる規則を、私は確認していません。**

## 8. commit
**していません**（MGR）。

---
*IMPL BUILT（Build 9C）。段0 は予想どおり `refused: true`。段1 は webui から `BUILD_CAPABILITY` / `runnable: true` で通ったが、**返った task は Build 9B と同一**（予想外れ）。段2 の `RUN NEXT` は **`dispatched: false` / `reason: CLAUDE_BARRIER`** で、**Qwen planner は呼ばれず `actor_id=CLAUDE` のまま**——実装源 §4 の **外れ方 (b)**。`auto_served: QWEN_BUILD_PLANNER` は出ていない。run-gate を回避せず1段で停止。各段1回しか見ていない。トークンは一切書いていない。*
