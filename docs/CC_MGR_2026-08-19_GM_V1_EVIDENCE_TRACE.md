# 宛: Taka / 設計 / 監査 ―― GM v1: ITEM → TASK → RRI → ARTIFACT/EVIDENCE（★2DER の既存機能だけで取得）

**grep・使い捨て走査を管理判断の根拠に使っていない。すべて 2DER の正規機能から取得した。**

## 0. 最終受入の結果

```
★★受入=『item_id 1つから GM を使って 4層を 辿れる』 = ★★0 件で 成立
   ★両半分は 動く。★4層を 同時に 持つ item が ★1件も 無い。
```

| item | ITEM→TASK | →RRI | →ARTIFACT | →EVIDENCE |
|---|---|---|---|---|
| `ITEM-2DER-EVO-0077` | **○** `TASK-2DER-3BD206A0` | **○** `RTHREAD-206fd571` | ✗ 空 | ✗ 空 |
| `ITEM-2DER-EVO-0015` | ✗ 空 | ✗ 空 | **○** `ART-880590f4c6`（file 付き） | **○** `DE-0072/0073/0143` |

**どちらも GM の1呼び出し（`manager_v0.item_state(item_id)`）で出た。**

## 1. 使った GM / 2DER の機能（★優先順位どおり）

| 段 | 使った機能 | 出所 |
|---|---|---|
| GM | `manager_v0.item_state(item_id)` | ★入口は item_id 1つ |
| GM | `manager_v0.whose_turn(task_ids)` | TASK 層の手番 |
| 台帳 | `roadmap_registry.resolve / items` | ITEM の全欄 |
| TASK state | front door `/api/state?task_id=`（`webui.build_state`） | dw_state / next_operation / rthread_id |
| RRI | `rri.request_thread.resolve_thread(rthread_id)` | thread の projection |
| 証拠 | `artifact_registry.resolve` / `all_active` | ART の file・在否・所有 |
| 経路表 | `route_adopt.route_table_view()` | **224行**（hand 18 / machine 206） |
| 機能表 | `function_table.function_list / function_table_view` | 登録8語・machine 0 |
| 機能→部品 | `function_first()` | ITEM→ART→区間 の既存対応 |
| 権限 | `authority.item_ceiling` | 上限 |
| front door | `/api/control?include=…` / `/api/resolve` / `/api/etrace` | 正規API |

## 2. ★対象5欄 ―― 2DER の情報源から答えた

| 欄 | ①書き込み責務（★正本の記述） | ②既存の書き込み口 | ③本線接続 | ④空欄の意味 |
|---|---|---|---|---|
| `task_ids` | `roadmap_registry.py:21` 逐語 **`(proof when DONE)`** | `register_item`（作成時）＋**`append_task_id`（2026-08-19 新設）** | **○**（`submit.py` の進捗マーカー付き投入） | **記録経路あり・実績1件** |
| `artifact_ids` | 同上 | **`register_item` のみ**（作成時） | **✗** | **★記録経路なし**（★下記） |
| `evidence_de_ids` | 同上 | **`register_item` のみ** | **✗** | **★記録経路なし** |
| `change_ids` | 同上 | **`register_item` のみ** | **✗** | **★記録経路なし** |
| `wiring_evidence` | ―（正本に責務の記述なし） | **`egl/structure/s9_done_semantics.py`**（★一度きりの移行・実行済みなら終了） | **✗**（常駐・本線から呼ばれない） | **★記録経路なし**（★DONE 57件のみ） |

### ★「対象なし」ではない ―― 数で示す（★出所=2DER の正規API）

```
artifact_registry.all_active()            = ★222 件
そのうち item から 参照されている ART      = ★ 36 件
★どの item からも 参照されない ART        = ★186 件（★83.8%）

計器が出した最新id（監視 2026-08-19 01:22）= DE-0804 ／ CHG-0208
item から 参照されている DE = 40 種 ／ CHG = ★1 種（★全144 item で 1件）
```

**∴ 証拠は在る。結び付ける記録経路が無い。**

### ★`register_item` の唯一の呼び手が渡していない

```
呼び手 = twoder/submit.py:321（★全repo で 1箇所）
渡している物 = item_id / phase_id / roadmap_id / title / description / ts
★渡していない物 = evidence_de_ids ／ artifact_ids ／ task_ids ／ change_ids
∴ ★front door から 生まれた item は ★4欄が 永久に 空（★task_ids だけ 今夜 口が 出来た）
```

## 3. ★FINDING（★修理していない・本線へ昇格させていない）

| # | 何をしていて発見したか | GM v1 を物理的に止めるか | 既存機能で解決できるか | 別ITEM化 |
|---|---|---|---|---|
| **F1** | 5欄の書き込み口を調べていて | **★止める**（最終受入が成立しない） | **できる** ―― `append_task_id` と同型の追記を `artifact_ids` 等へ（★今回は作らない） | **不要**（`ITEM-2DER-EVO-0077` の範囲） |
| **F2** | `wiring_evidence` の書き手を辿って | 止めない | 一度きりの移行スクリプトのみ＝本線の口は無い | 不要（EVO-0077） |
| **F3** | 機能表で「誰が書くか」を引こうとして | 止めない | **★引けない** ―― 登録は hand 8語・machine 0・`name_captured 0`。機能表自身が `by_origin_note` で「★実績と読まない」と書いている | 既知（機能表の収穫0） |
| **F4** | `function_first` で ITEM→TASK を結ぼうとして | 止めない | rows に `task_ids` 欄が無い＝機能表側では結べない | 不要 |
| **F5** | 経路表を調べていて | 止めない | ―（★私の誤報。§4） | ― |
| **F6** | `/api/control?include=observed_edges,edge_measures` が **310秒** | 止めない | 段0 の懸念が再発 | 別途 |
| **F7** | 経路表の未登録残 ―― `observed 67` のうち **`unregistered 49`** | 止めない | 自動採択の口は在る（§4） | 別途 |

**FINDING 数 = 7 ／ そのうち GM v1 を止める物 = 1（F1）。**

## 4. ★経路表 ―― 前回の私の報告は誤りでした（訂正）

**私は「経路表は18区間しかない／私の作業に区間が無い」と報告した。誤り。**

```
★実際 = route_adopt.route_table_view() = ★224 行
      hand    18（★route_table.py の 手書き＝★これしか 見ていなかった）
      machine 206（★機械が 採択した 行）
   kind = from import 144 ／ observed_both_sides 56 ／ import 6
   最初の採択 2026-08-12T19:43 ／ ★最後の採択 2026-08-18T23:43:06 ／ revoked 0
   票の model = Qwen3.6-35B-A3B 150 行（残 56 行は 票なし＝決定論の枝）
```

**★自動更新は動いている。約2時間前も更新された。**

**なぜ `route_table.py` が手作業でしか変わっていないか** ―― `route_adopt.py` の正本 docstring に逐語:

> 「採用=★経路表へ1行 足す（★新台帳0=★票と同じ器 event_trace へ emit）。**★route_table.py には1行も書かない（★規律§1）**」

**∴ 設計どおり。** `route_table.py` は手書き18区間の器で、機械の206行は event_trace 側に積まれ、**読む時に `route_table_view()` が合成する**。
**私は合成後を見ずに、手書き側だけを見て「18区間」と言った。**

**常駐も動いている**: `twoder-route-worker.service` = active/running、**2026-08-15 07:22 起動・再起動0**。
引き金は `needs_refresh`（2DER が書いた判断）。部品は相互接続済み（`route_worker` が `observed_edges`/`route_adopt`/`static_edges`/`edge_measures`/`anatomist`/`function_table`/`function_first`/`unstable_keys` を呼ぶ）。

**切れているのは経路表の自動更新ではなく、管理経路が観測されないこと:**

```
machine 206 行に roadmap_registry = ★0 ／ manager_v0 = ★0 ／ request_thread = ★0
（★webui は 20 行 在る）
★理由=採択の材料は ①静的 import 辺 ②observed_both_sides（handed と receipt の 両側が 在る 対）
   ★管理経路は handoff / receipt を emit していない ∴ ②に 出ない
```

## 5. 報告（Taka 指定の項目）

```
★使った GM/2DER の機能            = 11（§1 の表）
★使えなかった既存機能              = 2
     ・機能表(function_table)      … 5欄の書き手を答えられない（F3）
     ・function_first の rows      … task_ids 欄が無い（F4）
★Claude が代行した作業             = 1（★前ターンの grep 走査）
     → 今回は route_table_view / function_first / artifact_registry で ★置き換えた
★新規実装数                        = 1
     manager_v0.item_state への ★読み取り追記のみ（★判断器0・書き込み0・新形式0）
★FINDING 数                        = 7（★GM v1 を止める物 = 1）
★GM v1 の本線が進んだ段             = 1 段
     観測面が ★2層(ITEM→TASK→RRI) から ★4層(→ARTIFACT/EVIDENCE) を 1呼び出しで 返す形に なった
     ★ただし 1件で 4層 全通しは ★0件（★F1 が 物理的に 止めている）
```

## 6. していないこと

```
★acceptance 照合器 0 ／ 新台帳 0 ／ 新ID 0 ／ 新証拠形式 0 ／ 新判断器 0
★F1 を 直していない（★本線へ 昇格させていない）
★submit を 1本も 投げていない（★DEFERRED の item に 作り話の task を 付けない）
★ここで 停止する。次を 勝手に 作らない。
```
