# task → thread の一括読み口 — 別担当への handoff v0.1

- 起票: CC_ALPHA(監視) 2026-08-24
- 宛先: MGR（担当を割り当てる。★ESDE は修理しない）
- 親: ITEM-2DER-EVO-0099（ESDE Domain Manager）から出た finding。★但し **ESDE 固有機能ではない**
- Taka 裁定 2026-08-24 逐語:
  > 「その次に task → thread の一括読み口を別担当へ渡す。これはESDE固有機能ではなく共通基盤です。
  > 609 TASKを1件ずつ /api/rthread?task_id= で引く構造は、今後Ledger/Research Domain Managerでも同じ問題になります。」

---

## 1. 何が無いか

**「どの TASK が明細(thread)を持っているか」を1回で引く口が無い。**

- front door の口は **24本**（全数確認・2026-08-24）。thread の一覧口は **0本**。
- 在るのは `GET /api/rthread?task_id=<1件>` だけ。

## 2. 実測（鍵つき）

| 測ったもの | 値 | 鍵 |
|---|---|---|
| TASK 全数 | **609** | `GET /api/tasks?limit=5000` の `tasks` |
| thread 全数 | **686** | `rri.request_thread.list_threads()` |
| `list_threads()` の所要 | **0.047 秒** | 686件・1回読み |
| `/api/rthread?task_id=` 1件 | **平均 2.6 秒** | 5件・06:39 実測（下の★訂正を見ること） |
| 609件を1件ずつ引く見積 | **約26分** | 上記から |
| ESDE が候補45件を探索した実測 | **約7分** | 入口を占有（★遅かった頃の値） |

### ★訂正（同日中に数字が動いた。★鍵を添える）

初版でここに **「1件10秒超 / 609件で100分超」** と書いた。**測り直したら 2.6秒 / 26分だった。**

| 鍵 | 1件あたり | 609件の見積 |
|---|---|---|
| 06:1x〜06:2x 実測（webui pid 2937960 世代） | **10秒超**（60件が600秒で引き切れず） | 100分超 |
| 06:39 実測（webui pid 2949147 世代） | **2.6秒**（5件・2.1〜3.6秒） | 約26分 |

★動いた理由 = front door の重い計算を並列化する作業が**並行して進んでいた**（EVO-0101）。
★∴ **「commit が在る」ではなく「どの webui プロセスが動いていたか」が鍵**（ソースに在る≠動く）。
★**依頼そのものは変わらない**: 26分でも Domain Manager の1周には使えない。
  ただし **緊急度は下がった** ∴ 優先順位は MGR が決めてよい。

## 3. 繋ぎ目は既に在る（★新台帳は要らない）

- `list_threads()` の返りは `{thread_id, ds_thread_ref, ts}`。
  **`ds_thread_ref` は `UTT-####` であって task_id ではない**（`TASK-` 始まり = **0 / 686**）。
  ∴ ★この関数だけでは task→thread にならない。
- **task→thread の値は `runs/<task_id>.trace.json` の `RTHREAD_ID` に在る。**
  - 既に `twoder/webui.py:170 _trace(task_id)` が1件ずつ読んでいる。
  - `build_state` が `"rthread_id": tr.get("RTHREAD_ID")` として載せている（webui.py:328・EVO-0049）。
- ∴ **不足しているのは「値」ではなく「まとめて返す口」だけ。**

## 4. なぜ `/api/rthread` が重いのか（★trace の読みが重いのではない）

`rthread_view(task_id)` は thread の有無を知るだけでも下を全部通る:
`build_state` 一式 → `list_questions` → `list_typed` → `_esde_for` → 依頼の形の不足の集計。
∴ **一括の口は `rthread_view` を609回呼ぶ形にしてはいけない。** trace の `RTHREAD_ID` だけを拾う別経路にする。

## 5. 依頼（実装は別担当）

**`GET /api/task_threads`** — 全 TASK の `{task_id, rthread_id}` を1回で返す。

- `rthread_id` は **無い場合 `null`**（★『無い』と『読めない』を分ける。読めなければ理由を返す）。
- 分母を必ず載せる: `{"total": N, "with_thread": M, "unreadable": K, "rows": [...]}`。
- **新台帳を作らない**。`runs/<task_id>.trace.json` の `RTHREAD_ID` を1回走査して返すだけ。
- `runs/` は横読み禁止面 ∴ **読むのは 2DER 側（webui）でなければならない**。これが「2DER に聞いて返させる」形。

### 受入条件
1. 609 TASK 分が **1回の呼び出し**で返る。
2. 既知の2本と一致する: `TASK-2DER-C032596E → RTHREAD-53614fdb` / `TASK-2DER-B14D7ACA → RTHREAD-6bfd5b30`。
3. `with_thread` と、1件ずつ引いた結果が一致すること（標本20件で照合。★全件照合は100分かかるので求めない）。
4. 新台帳0・新state0・新ID0。

## 5.5 ★7時間の実走で率が出た（2026-08-24 13:23 実測）

常駐を再起動してから **6時間59分**、**14回**発火した（間隔 31.7〜37.3分）。

| 測ったもの | 値 |
|---|---|
| 発火 | **14回** |
| うち **明細(thread)を持つ task** | **1件（7.1%）** |
| 持たない task | **13件（92.9%）** |
| backlog | 589 / 610 |

∴ **93% の発火は、結果が ETRACE にしか残らない。**
★これは「確率的」という言葉の中身で、**率が出たのは初めて**。

★この口ができれば、Domain Manager は **明細へ戻せる 7% を先に選べる**。
いまは backlog の先頭から順に舐めるので、**93% の発火が明細に届かないまま消費される**。

## 6. なぜ共通基盤なのか（★ESDE に閉じ込めない理由）

Domain Manager は「**結果を明細へ戻せる対象**」を選べないと、自動発火が明細に届くかが確率的になる。
これは ESDE だけの都合ではない:

- **ESDE**（実測済）: 自動発火4件のうち明細に届いたのは1件。残り3件は `wrote=False thread=None`。
- **Ledger Domain Manager**（Taka 指摘）: 同じ選別が要る。
- **Research Domain Manager**（Taka 指摘）: 同じ選別が要る。

∴ **口は ESDE でなく front door 側に置く。**

## 7. 今どう凌いでいるか（★手当てであって解決ではない）

`domain_esde.esde_evaluate_one` の既定は `require_thread=False`。
先頭の候補をそのまま測り、ETRACE の記録自体を「済み」の印にして餓死を避けている。
∴ **明細に届くかは確率的**。この口ができたら `require_thread=True` を既定に戻せる。
