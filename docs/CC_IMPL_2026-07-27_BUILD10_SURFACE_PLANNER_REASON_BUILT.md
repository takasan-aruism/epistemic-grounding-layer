# 実装 → 設計/監査: Build 10 — 3箇所を修理した。**ただし今回は planner が成功したため、修理が効いたかは確認できていない**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.7）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD10_SPEC_SURFACE_PLANNER_REASON.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD10_APPROVED.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 1. 修理（追加のみ・3箇所とも）【監査:IMPL】
| # | ファイル | 変更 |
|---|---|---|
| **S1** | `dev-workcell/dw/dispatch.py` | 関数冒頭で `planner_outcome = None` を初期化。planner 呼出後に `planner_outcome = pres` を保持。**barrier の戻り値**に `"planner_outcome": planner_outcome` を追加 |
| **S2** | `dev-workcell/dw/dispatch.py` | `run_until_barrier` の trace 各要素に `"planner_outcome": step.get("planner_outcome")` を追加 |
| **S3** | `twoder/webui.py` | `/api/run_next` の応答に `"planner_outcome": step.get("planner_outcome")` を追加 |

**変えていないもの**（実装源 §2-4）: `dispatched` / `reason`（`"CLAUDE_BARRIER"` の文字列）/ `nlo` / `pending_actor` / `auto_served` / `_emit_pending` の書き込み内容 / `record_plan` の呼ばれ方 / fail-closed の判定条件 / `runtime_inspection`（未変更）。
**`planner_outcome` は raw のまま運んでいます**（要約・整形・切り詰めをしていません）。**`None`（呼ばれなかった）と `dict`（呼ばれた）を区別できるよう、キーを常に置いています。**

## 2. 非回帰（実装源 §3・12本すべて実行）【監査:IMPL】
| テスト | 結果 |
|---|---|
| `test_build_planner`（★直撃） | **9/9 PASS** |
| `test_alpha_beta_integration` | 17/17 PASS |
| `test_concurrency_and_run_gate` | 7/7 PASS |
| `test_full_live_e2e` | 7/7 PASS |
| `test_preflight_gate` | 13/13 PASS |
| `test_return_loop` | 12/12 PASS |
| `test_dispatch_provenance` | 11/11 PASS |
| `test_plan_template` | 11/11 PASS |
| `test_dw_workflow_equivalence` | 7/7 PASS |
| `test_upper_review_gate` | 9/9 PASS |
| `test_auto_disposition` | 9/9 PASS |
| **`test_submit_e2e`** | **7/10**（下記 §2-1） |

### 2-1. `test_submit_e2e` は **私の変更の前も 7/10** です【監査:IMPL】
落ちているのは `2 OBSERVE: DS_INPUT_REF resolves + no DW task + no :8005` / `7 BUILD task sits at PLAN barrier` / `10 no route touched :8005`。
**変更を `git stash` して同テストを実行し、`7/10 passed` を確認しました**（＝ **私の変更が原因ではありません**）。
**assert は書き換えていません。**（stash 復元時に `twoder/failure_recurrence.jsonl` がテスト実行で更新され pop が一度失敗したので、当該ファイルを `git checkout --` してから pop し、修理の復旧を確認しています。）

## 3. ★受入の本体 — 修理後にもう1回だけ動かした結果【監査:IMPL】
```
POST /api/submit    （依頼文は Build 9B/9C と同一・1文字も変えていない）→ task_id=TASK-2DER-D6A93450 / runnable=true
POST /api/run_next  {"task_id":"TASK-2DER-D6A93450"}                    → 1回だけ
```
**返り:**
```
返りのキー : ['dispatched', 'nlo', 'reason', 'state']
dispatched : true
reason     : None
nlo        : state=CREATED / operation=PLAN / actor_role=MANAGER / actor_id=CLAUDE
planner_outcome : ★キー自体が応答に無い
```
**task の状態（修理後）:**
```
derive_state('TASK-2DER-D6A93450') = READY_FOR_IMPLEMENTATION / has_plan: True
events = [CREATE, PROCESS_EVENT, PROCESS_EVENT, PLAN]
```

### 3-1. ★`planner_outcome` は出ていません。理由は「失敗しなかったから」です
今回は **`dispatched: true`＝planner が PLAN を記録して成功**しました。
私が追加したのは実装源 §2-1 の指示どおり **barrier の戻り値**であり、**成功パス（`auto_served` を返す側）には載せていません。**
**∴ 今回の実行では、失敗理由を出す経路を通っていません。修理が効いたかどうかは確認できていません。**

### 3-2. ★同じ入力で結果が変わりました（事実）
| | Build 9C | **Build 10** |
|---|---|---|
| `dispatched` | `false` | **`true`** |
| `reason` | `CLAUDE_BARRIER` | `None` |
| task 状態 | `CREATED` / `has_plan: False` | **`READY_FOR_IMPLEMENTATION` / `has_plan: True`** |

**同じ task・同じ依頼文・同じ経路で、Build 9C は barrier に落ち、今回は PLAN が記録されました。**
**各1回ずつしか見ていないので、どちらが常態かは私には判定できません。**

## 4. 守った禁止事項
- **投入1回・`RUN NEXT` 1回。`run_until_barrier` を使っていません。**
- **依頼文を1文字も変えていません。**
- **run-gate を回避していません。**
- **assert を書き換えていません。**
- **トークンを文書・ログ・argv に出していません。**
- **効果を測っていません。「2DER が良くなった」と書いていません。**

## 5. 観測の限界（事実として）
- **修理の動作確認ができていません**（失敗経路を通らなかったため）。**`planner_outcome` が実際に理由を運ぶかは未確認です。**
- **`test_submit_e2e` の既存 3 失敗の原因を、私は調べていません**（本 build の範囲外）。

## 6. commit
**していません**（MGR）。触った本番ファイル: `dev-workcell/dw/dispatch.py` / `twoder/webui.py`。

---
*IMPL BUILT（Build 10）。S1/S2/S3 の3箇所を**追加のみ**で修理（`planner_outcome` を raw で運ぶ・`None` と `dict` を区別・既存キーと fail-closed は不変）。非回帰は11本 PASS、`test_submit_e2e` 7/10 は **stash して変更前も 7/10 を確認**（私の変更が原因ではない）。**★受入の本体では planner が成功してしまい（`dispatched: true` / `has_plan: True` / `PLAN` 記録）、失敗経路を通らなかったため修理が効いたかは確認できていない。** 同じ入力で Build 9C は barrier・今回は成功——各1回ずつしか見ていない。*
