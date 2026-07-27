# 実装 → 設計/監査: Build 11 — **`planner_outcome` キーが出た（修理の実証）。PLAN も記録された**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.7）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD11_SPEC_NEW_TASK_THROUGH_PLAN.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD11_APPROVED.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**（Taka 指示により削除。参照ゼロを確認してから実行・未追跡だったため git 履歴に残らず）

---

## 1. 投入と進行（各1回）【監査:IMPL】
```
POST /api/submit    → task_id=TASK-2DER-B9B4DA3B / request_type=BUILD_CAPABILITY / runnable=true
POST /api/run_next  {"task_id":"TASK-2DER-B9B4DA3B"}   → 1回だけ
```
**依頼文は実装源 §1 のまま1文字も変えていません。`run_until_barrier` を使っていません。間に他の submit を挟んでいません。**

## 2. ★本 build の主目的 — 修理の実証【監査:IMPL】
```
run_next の返りキー : ['dispatched', 'nlo', 'planner_outcome', 'reason', 'state']
planner_outcome     : ★キーが存在する（値は null）
```
**＝ Build 10 の修理（S3）が新プロセスで効いていることが実証されました。**
Build 10 では同じ確認でキー自体が存在せず、Build 10R では証拠②③が成立しませんでした。**本 build で初めて、キーの存在を直接観測できました。**

**値が `null` であることについて**: 実装源 §3 は「**成功しても失敗しても、キーが在れば修理は実証される**」としており、**その条件は満たしています。**
**値が `null` である理由を、私は本 build では確認していません**（成功パスを通ったこととの関係は、私の観測だけでは判定材料が不足しています）。

## 3. PLAN の結果【監査:IMPL】
```
dispatched : true      reason : None      auto_served : None
nlo        : state=CREATED / operation=PLAN / actor_role=MANAGER / actor_id=CLAUDE
derive_state('TASK-2DER-B9B4DA3B') = READY_FOR_IMPLEMENTATION / has_plan: True
events = ['CREATE', 'PROCESS_EVENT', 'PLAN']
```
**`PLAN` が記録され、`READY_FOR_IMPLEMENTATION` になりました。**

## 4. 予想と実際
| 項目 | 予想 | **実際** | 判定 |
|---|---|---|---|
| `request_type` | `BUILD_CAPABILITY` | **`BUILD_CAPABILITY`** | **当たり** |
| `DW_TASK_ID` | 新しい id | **`TASK-2DER-B9B4DA3B`**（`D6A93450` ではない） | **当たり** |
| run-gate | `runnable: true` | **`runnable: true`** | **当たり** |
| **`planner_outcome` キー** | **★在る** | **★在る** | **当たり** |
| **PLAN の成否** | **成功** | **成功**（`dispatched: true` / `has_plan: True`） | **当たり** |
| 成功時の `auto_served` | `QWEN_BUILD_PLANNER` | **`None`** | **★外れ** |
| 失敗時の `stage` | `validation` | **該当せず**（失敗しなかった） | — |

**`auto_served` が `None` である理由を、私は確認していません。** **判定材料が不足しています。**

## 5. 仕様どおり止まりました（§2）
- **`derive_state` が `READY_FOR_IMPLEMENTATION` になったので、`run_next` を追加で打っていません。**
- **worker（`CODING_WORKER`）に進んでいません。成果物の生成をしていません。**

## 6. 守った禁止事項
- **投入1回・`run_next` 1回。`run_until_barrier` 不使用。**
- **依頼文を1文字も変えていません。**
- **token を要求されませんでした。gate を迂回していません。**
- **本番コードを変更していません**（本 build では1行も）。
- **トークンを文書・ログ・argv に出していません。**

## 7. 観測の限界（事実として）
- **各操作1回ずつです。** planner は揺れる（Build 9C は barrier / Build 10・11 は成功）ため、**1回の成功で「常に成功する」とは書きません。**
- **`planner_outcome` が実際に失敗理由を運ぶかは、依然として未確認です**（今回も PLAN が失敗しなかったため）。**確認できたのは「キーが応答に到達する」ところまでです。**

## 8. commit
**していません**（MGR）。**本 build では本番コードを変更していません。**

---
*IMPL BUILT（Build 11）。新しい task `TASK-2DER-B9B4DA3B` を投入し `run_next` を1回。**★`planner_outcome` キーが応答に存在することを初めて観測＝Build 10 の修理が新プロセスで効いていることの実証**（値は null）。**PLAN も記録され `READY_FOR_IMPLEMENTATION`**。予想は5項目当たり・`auto_served` が `None` の1項目が外れ（理由は未確認）。仕様どおり worker へ進まず停止。各操作1回のみ。*
