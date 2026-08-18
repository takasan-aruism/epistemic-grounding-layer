# 宛: Taka / 設計 / 監査 ―― 管理系 component を既存の経路表育成機構へ載せた（★1件実測）

**新しい経路表・新しい機能表・新しい分類器・新しい観測方式を作っていない。**

## 0. 完了条件の結果

```
★★「管理系 component を1件だけ 既存の 育成機構へ 正規に 載せられるか」= ★★可能。実測した。

  R-b7387386c1bf  MANAGER_V0.use_part -> roadmap_registry.resolve.called
                  kind=observed_both_sides ／ origin=machine
  ★経路表 machine 206 → ★207   ／ ★機能表の 候補母数 75 → ★76
  ★採択したのは ★常駐 route_worker（★Claude は 代行していない・★3分後に 自力で 採った）
```

## 1. 落ちていた段 ―― **1箇所。「呼び方」だった**

**篩の不足でも機構の不在でもない。**

### 静的側 `route_edge_vote._candidates()` の篩（①〜⑤・逐語）

```
① internal だけ（internal = REPOS ∪ {"dw"}）
② ★経路表に 既に 在る head は 除く
     known = {dispatch, ds, dw, egl, rri, rungate, runner, seal, submit}
③ 試験 / docs を 除く
④ ★repo 跨ぎだけ（head == repo は 除く）
⑤ 昇順で 先頭1件
```

| 対象 | 静的候補 | どこで落ちるか |
|---|---|---|
| `roadmap_registry` | **kept 0** ／ dropped `self_import` **18** | **④**（`from twoder import roadmap_registry` は同一 repo） |
| `manager_v0` | kept 5 | **②**（宛先 `ds`/`dw`/`rri` は3つとも `known`） |
| `request_thread` | kept 5 | **②**（宛先 `rri` が `known`） |

（`candidates_v2` の全体: `total_scanned 1140` → `kept 243` ／ `dropped {self_import 778, test_file 110, doc_snapshot 9}`）

### 観測側（★実際に効いている入口）

```
manager_v0._use(part, fn) が ★両側を emit:
    MANAGER_V0.use_part  handed_to = part + ".called"
    part.called          received_from = "MANAGER_V0.use_part"
→ observed_edges.segments_from_records で evidence = "BOTH"
→ route_worker.refresh_route_table が ★決定論で 採択（votes=[{seed:"records",answer:"BOTH"}]）
```

**∴ 経路表 224行のうち `MANAGER_V0.*` は 24行 在った。**
**`roadmap_registry` が 0行 だったのは ―― GM が `_use` を通さず直に呼んでいたから。**

## 2. 修復（★既存の物だけ・1行）

```python
# 変更前
rec = _R.resolve(item_id) or {}
# 変更後（★既存の _use を 通すだけ）
rec = _use("roadmap_registry.resolve", _R.resolve, item_id) or {}
```

**新規実装 = 1行（★足場 `manager_v0`）／ 新しい観測方式 0 ／ 新しい判断規則 0。**

### 実測の順序（★私が代行した所と、機械が自力でやった所を分ける）

| # | 誰が | 何が起きたか |
|---|---|---|
| 1 | **Claude(MGR)** | `_use` 経由に変えて `item_state` を1回呼んだ（走行 `ETR-38442c6665c7`） |
| 2 | **機械** | `handed_edges` に辺が出た（count 1） |
| 3 | **機械** | `segments_from_records` で **`evidence: "BOTH"`**（BOTH 56 → **57**） |
| 4 | **★機械（常駐）** | **3分後に `route_worker` が自力で採択**（machine 206 → 207） |
| 5 | **機械** | 機能表の候補母数 75 → **76**（`roadmap_registry.resolve.called` が入った） |

## 3. ★`function_index(...,'machine')` から引けるか → **★まだ引けない**

```
母数 = 76 ／ ★我々の component の 位置 = ★47番目
run_stage3(limit=76) → ★asked 7 で 停止
    stop_why = 「同じ名前が2部品で揃った ∴ ここで一度停止する」
    funnel = {asked 7, unanimous_not_in_list 4, name_captured 4,
              duplicate_of_existing 0, ★name_twice 1, approved 0}
    処理 -> ["DS.phase1", "FRONT_DOOR.claude_packet"]   ← 7件目で 条件成立
★asked に roadmap_registry は 入っていない（★47番目に 到達しない）
```

### ★機構は「往復」で前進する設計だった

```
段2(run_stage3) が 名前を 捕まえて 停止
  → 段4(register) が 採択する
  → 次の 走行で その名前は `duplicate_of_existing` として 飛ばされ ★より 先へ 進む
```

**∴ 前進の速さは「段4 が何回呼ばれたか」で決まる。**
**段4 の呼び手は 0（既知）。∴ 母数の後方（47番目）は永久に訊かれない。**

**これが不足している段。**（前回 machine 0→1 にした時と同じ場所。今回はその影響が「前進しない」という形で出た。）

## 4. ★前回報告の訂正 2件

```
①「経路表 machine 206行 に manager_v0 = 0件」→ ★誤り。
   行の 表記は `MANAGER_V0`（★大文字）。★小文字で 数えて 0 と 報告していた。
   正しくは ★24行。★大小を 書かなかった 私の 数え方の 欠陥。

②「管理経路は 経路表候補に 入らない」→ ★言い過ぎ。
   `manager_v0` / `request_thread` は 静的候補に kept 5件ずつ 在り、
   `manager_v0` は 観測側で 24行 採択済みだった。
   ★入っていなかったのは `roadmap_registry` だけ。
```

## 5. FINDING（★修理していない）

| # | 内容 | 一周を止めるか |
|---|---|---|
| **F14** | `run_stage3` は最初に条件成立した1件で停止する。段4 の呼び手が0のため、**母数の後方は永久に訊かれない**（我々の component は47番目） | **★止める**（`function_index` から引けない） |
| **F15** | `_use` を通す＝**呼ぶたびに etrace 2行が増える**。観測を載せると記録が増える（既存 `MANAGER_V0.*` 24行も同じ形） | 止めない |
| **F16** | `route_worker` の1周は front door `/api/control?include=observed_edges`（**実測 310秒**）を含む。`INTERVAL=60` は実効しない | 止めない |

## 6. 報告

```
★2DER 単独で 動いた段    = 採択（★route_worker が 3分後に 自力で 採った）
★Qwen が 担当した段      = 名前付け（★asked 7・3seed 全会一致）
★Claude が 必要になった段 = 2 … ①`_use` 経由への 変更（1行） ②`run_stage3` の 起動（★段2 の 呼び手が 0）
★Taka が 必要になった段   = 0
★新規実装数              = ★1行（足場・既存ラッパを 通しただけ）
★新規判断規則数          = ★0
★FINDING 数              = 3（★止める物 1 = F14）
★完了条件（1件 載せる）   = ★達成（経路表 207行目・機能表 母数 76）
★function_index から 引ける = ★まだ（★F14）
★次の停止点              = ★段4 の 呼び手 0 が 段2 の 前進を 止めている（★往復しない）
```

## 7. していないこと

```
★新しい 経路表 0 ／ 新しい 機能表 0 ／ 新しい 分類器 0 ／ 新しい 観測方式 0
★採択を Claude が 代行していない（★常駐に 任せた）
★append_task_id の 実装 0 ／ F1 修理 0 ／ acceptance 0 ／ RRI 0 ／ 並列化 0
★register を 追加で 呼んで 47番目まで 無理に 進めていない
```
