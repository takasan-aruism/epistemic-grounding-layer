# 宛: Taka / 設計 / 監査 ―― GM「観測面 v1」―― `item_id` 1つで ITEM→TASK→RRI が見えた

**新しい判断器 0 ／ 新しい対応表 0 ／ 書き込み・routing・authority 判定 0。**

## 1. 実測（★入口は `item_id` 1つだけ・1回の呼び出し）

`manager_v0.item_state("ITEM-2DER-EVO-0077")`:

| 欄 | 値 | source |
|---|---|---|
| `item_in_ledger` | `true` | `roadmap_registry.resolve`（引けたか） |
| `task_ids` | `["TASK-2DER-3BD206A0"]` | `roadmap_registry.resolve.task_ids` |
| `task_details[].dw_state` | `CREATED` | front door `/api/state`（`webui.build_state`） |
| `task_details[].next_operation` | `PLAN` | 同上 |
| `task_details[].actor_role` | `CLAUDE` | 同上（**★中身は `nlo["actor_id"]`** ―― §3） |
| `task_details[].claude_barrier` | `true` | 同上 |
| `task_details[].rthread_id` | `RTHREAD-206fd571` | 同上 |
| `task_details[].question_ids` | `["Q-e6202bea"]` | 同上（`rthread_question_ids`） |
| `task_details[].rri_thread` | `{"status":"SOFT", …}` | `rri.request_thread.resolve_thread`（**★task の rthread_id 経由**） |
| `task_details[].question_counts` | `raised_total=1 / resolved=0 / in_flight_count=1` | 同上（★件数は既存欄を写すだけ） |
| `task_details[].open_gaps` | `[]` | 同上 |
| `task_details[].unresolved_question_ids` | **`null`（UNKNOWN）** | §2 |

**ITEM→RRI の直接対応は作っていない。** `rri_thread` は必ず `task_ids` → `rthread_id` の順に辿る。

## 2. ★UNKNOWN のまま残した欄（推測しない）

**`unresolved_question_ids` は埋められない。**

```
★実測(2026-08-19)=★RRI が 持つのは
    ・件数 : raised_total / resolved / open_gap / rejected / merged / in_flight_count
    ・一覧 : open_gaps
  ★『未解決の question id 一覧』を 返す 口は ★無い
★`raised` から `resolved` を 引いて 作れば ★それは 私の 新しい 規則
∴ ★作らない = UNKNOWN のまま(★source に 理由を 書いた)
```

**この ITEM では `in_flight_count = 1`。「未解決が1件ある」ことは分かるが、「どの id か」は引けない。**

## 3. ★実測で出た食い違い（直していない）

**同じ `actor_role` という名前で、口によって別の値が出る。**

```
dw.dispatch.next_legal_operation("TASK-2DER-3BD206A0") は ★両方 持つ:
      actor_role = "MANAGER"
      actor_id   = "CLAUDE"

front door /api/state(webui.py:208) = "actor_role": nlo["actor_id"]   ← ★actor_id を 載せている
manager_v0.whose_turn                = nlo["actor_role"]              ← ★actor_role を 載せている

∴ 同じ ITEM の 同じ TASK で   /api/state → "CLAUDE"
                              whose_turn → "MANAGER"
```

**★どちらが正しいかを私は決めていない。** `source` に**どの欄を写したかを名前まで書いて両方残した**。
**`webui.py` は触っていない**（production・今回の範囲外）。**同型は `webui.py:305` にもある。**

これは繰り返し出ている型 **「鍵が違う」** の新しい実例。

## 4. ★対照で出た欠陥（私の足場・直した）

```
★台帳に 無い item(ITEM-2DER-NO-SUCH)と ★task が 無い item(EVO-0044)が
  ★同じ 返り(error=None / UNKNOWN)に なっていた = ★★不在が 遵守に 見える
```

**`item_in_ledger` の1欄で分けた。** 3件の対照:

| ITEM | `item_in_ledger` | `task_details` の source |
|---|---|---|
| EVO-0077 | `true` | 在り（1件） |
| EVO-0044 | `true` | ★UNKNOWN=★task_ids が空（★TASK が無い＝★推測しない） |
| NO-SUCH | **`false`** | ★UNKNOWN=**★item が台帳に無い**（★task が無いのとは別） |

## 5. していないこと

```
★書き込み 0 ／ routing 0 ／ authority 判定 0 ／ 次工程の 決定 0
★α（契約投入への マーカー要求）に 入っていない
★過去 27件の 遡及 0 ／ 冪等性の 測定 0 ／ 契約経路の 一般化 0
★acceptance 照合に 入っていない
```

commit `c36b57b`（`[Claude実装]` / source のみ）。
