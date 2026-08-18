# 宛: Taka / 設計 / 監査 ―― 機能表 段3: **machine 0 → 1**（★新規実装 0行）

**独自 grep を管理判断の根拠にしていない。判定はすべて機能表・authority・artifact_registry・route_table_view の正規面が返した値。**

## 0. 完了条件の実測

```
★登記の前 : function_index('確認','machine') = {in_list:false, components:[], count:0}
★登記の後 : function_index('確認','machine') = {in_list:true,  components:["unregistered_keys.called"], count:1}
★function_list by_origin = {"hand": 8, ★"machine": 1}      ← ★0 → 1 達成
★権限 = AUTO_APPROVED「REVERSIBLE_LOCAL かつ evidence=OK かつ rollback=complete ∴ 層1」
★実在する 2DER 部品 = check_artifact.called ／ unregistered_keys.called
★名前を 付けたのは Qwen3.6-35B-A3B（prompt_version=menu_vote_v1・3seed 全会一致）
```

## 1. ★前回報告の訂正

**私は「`name_captured 0`」と報告した。誤り。** それは **3走行のうち1本**（`ETR-9b6d70615ffa`）の値。
`funnel_from_records()` の **通算**は:

```
asked 90 → any_not_in_list_vote 37 → unanimous_not_in_list 7 → name_captured ★7
        → duplicate_of_existing 1 → ★name_twice 0 → approved 0
```

**名前は7件 捕まっていた。0 だったのは `name_twice`（＝同じ名前が2部品で揃うこと）。**

## 2. 5段の判定（★2DER の面から）

| 段 | 存在 | 本線接続 | 実走実績 | 現在使用中 |
|---|---|---|---|---|
| **① 記録から候補取得** | ○ `components()` 75件 / `candidates_from_records()` | ○ | ○ 記録90件・3走行 → 今回 73 ask | ○ |
| **② 候補へ名前を付ける** | ○ `run_stage3()`（`menu_vote` → Qwen 3seed 全会一致） | **△** 常駐から呼ばれない | ○ `name_captured` 通算 7 → **今回 +18** | △（手で走らせた） |
| **③ 既存機能との照合** | ○ `fl_names` 重複判定 | ○ | ○ `duplicate_of_existing 1` | ○ |
| **④ 採択** | ○ `register()` | **✗ 呼び手 0** | **✗ `approved 0`** → 今回 **2行 approved** | ✗ |
| **⑤ 反映** | ○ `function_index` / `function_list` | ○ | ✗ machine 0 → **今回 machine 1** | ○ |

### ★最初の切断点 = ④ 採択（呼び手 0）

**対照が同じ repo に在る**（★これが根拠。私の推測ではない）:

```
route_adopt.adopt      ← twoder/route_worker.py:85 が 呼ぶ → 機械採択 206行・最後 2026-08-18 23:43
function_table.register ← ★呼び手 0                        → machine 0
```

`run_stage3` は条件成立時に **止まって報告するだけ**（逐語 `stop_why` = 「同じ名前が2部品で揃った ∴ ここで一度停止する」／`limit` 到達時は「★MGR へ上げる」）。**登録は設計上 外から呼ぶ。**

### ★到達性の壁（④の手前）

```
run_stage3(limit=MAX_COMPONENTS)  … ★既定 30 ／ ★comps = components() = 75
∴ ★3走行すべてが 同じ 先頭30件を 訊いていた = ★45件が 一度も 訊かれていない
★`names` は 1走行内だけの 集計（MIN_OCCURRENCES=2 に 届かない）
```

## 3. 修復（★新規実装 0行・既存の物だけ）

| # | したこと | 使った既存の物 |
|---|---|---|
| 1 | 母数を全件にした | **既存の引数** `run_stage3(limit=75)`（★コードを1行も変えていない） |
| 2 | **走行を開いてから** `register` を呼んだ | **2DER 自身が書いていた作法** ―― `route_worker.refresh_route_table` の逐語「★走行を 開いてから 呼ぶ（★開かないと evidence≠OK で 層3 に 落ちる＝2026-08-14 実測）」 |

**★1回目は失敗した（隠さない）**: `run_id=` を渡しただけで走行を開かず呼び、

```
authority.gate_for_item("REGISTER_FUNCTION","ITEM-2DER-EVO-0058")
  → evidence="UNVERIFIED" → 層3 → REQUIRES_TAKA（fail-closed）→ approved=False
```

走行を開いて呼び直したら **AUTO_APPROVED（層1）**。**門は正しく効いていた。**

## 4. ★同じ F1 で段3 を越えられたか → **★いいえ**

```
function_index('登記','machine') = {in_list:true,  components:[], count:0}
function_index('追記','machine') = {in_list:false, components:[], count:0}
function_index('確認','machine') = {in_list:true,  components:["unregistered_keys.called"], count:1}
```

**`append_task_id` は引けない。理由は候補母数:**

```
候補母数 = 75件（run_stage3 head の counted_by 逐語 =
           「★経路表(手書き18)＋採用行 の 相異なる component.function」）
★母数に roadmap_registry を 含む key = ★0件
★母数に append を 含む key          = ['DW._append_event']  ← 別物
```

**∴ `append_task_id` は候補になり得ない。**

## 5. ★次の停止点（次の GM 開発対象）

```
★★機能表の 候補母数が ★経路表 由来である。
★管理経路（roadmap_registry / manager_v0 / request_thread）は ★経路表に 出ない
   （★既知 FINDING。★machine 206行 中 0件・★handoff/receipt を emit しないため）
∴ ★管理層の 部品は ★永久に 機能表へ 入らない
∴ ★GM は F1 の EXISTING_ANALOG を ★今後も 引けない
```

**★これが次の停止点。** 今回は触っていない（Taka 指示どおり）。

## 6. FINDING（★修理していない）

| # | 内容 | 一周を止めるか |
|---|---|---|
| **F11** | `function_id = sha1(name)[:8]` ＝ **名前ごとに1行**。2部品を登記したが `count=1`・`components` は1件（latest-wins）。∴ **1つの名前に2部品を持てない** | 止めない（count≥1 は満たす） |
| **F12** | front door に **機能の登記口が無い**（18口すべて読み／`/api/control?include=` も読み専用）∴ **登記は in-process のみ**＝入口が1つでない | 止めない |
| **F13** | `register(approver=)` は「呼び手の認証済み識別」の設計だが in-process 呼び出しでは Basic 認証を通らない。既定値は `"taka-credential"`（★詐称になり得る）。今回は `"MGR"` を明示した | 止めない |

## 7. 報告

```
★2DER 単独で 通過した段          = ①②③⑤（★④だけ 人が 呼んだ）
★Qwen が 担当した段              = ②（★名前を 付けた=Qwen3.6-35B-A3B・3seed 全会一致・73部品を 判定）
★Claude が 必要になった段         = 2 … ②の 母数指定(limit=75) ／ ④の register 呼び出し
                                   （★どちらも ★呼び手が 居ないため）
★Taka が 必要になった段           = 0
★新規実装数                      = ★0 行
★新規判断規則数                  = ★0（MIN_OCCURRENCES=2・全会一致・authority 層判定は すべて 既存）
★FINDING 数                      = 3（F11/F12/F13・★止める物 0）
★完了条件（machine 0 → 1以上）    = ★達成
★F1 で 段3 を 越えたか            = ★いいえ（★候補母数に roadmap_registry が 無い）
★次の停止点                      = ★機能表の 候補母数が 経路表由来 ∴ 管理層の 部品が 入らない
```

## 8. していないこと

```
★新しい 機能表 0 ／ 新しい 分類器 0 ／ 新しい 台帳 0 ／ 新ID 0
★F1 を 実装していない ／ acceptance に 入っていない
★経路表の 管理経路を 触っていない（★既知 FINDING の まま）
★EVO-0075 / 0076 / RRI / 並列化に 入っていない
★一周を Claude が 穴埋めして 完走させていない
```
