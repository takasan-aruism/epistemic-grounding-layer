# 宛: Taka / 設計 / 監査 ―― GM → Qwen → GM の一周: **段3 で止まった**

**独自 grep・使い捨て走査を管理判断の根拠にしていない。すべて 2DER / GM の正規面から取得した。**

## 0. 結論

```
★★一周は 成立しなかった。★停止点 = 段3「既存機能 / 既存 pattern を 検索」
★理由（★2DER 自身の 面が 返した 値）:
    function_index('登記','machine') -> {"in_list": true, "components": [], "count": 0}
    function_table.function_list()   -> by_origin {"hand": 8, "machine": 0}
    function_table_view()            -> name_captured 0（★3走行・記録90件）
★∴ GM は EXISTING_ANALOG（=`append_task_id` 相当）を ★既存面から 取得できない。
★★Claude が 穴埋めしていない（★停止したまま 記録して 終える）。
```

## 1. 一周を実際に辿った結果

| 段 | 使った 2DER/GM の面 | 結果 |
|---|---|---|
| **段1 現在ITEMを観測** | `manager_v0.item_state(item_id)` | **○ 成立**（下記 §2） |
| **段2 blocking finding を選択** | GM の公開面 / 台帳 / `/api/state` | **△** ―― §3 |
| **段3 既存機能・pattern を検索** | `function_table.function_index(name, kind)` | **✗ 停止** ―― 口は在る／**収穫 0** |
| 段4 Work Packet を機械生成 | `manager_v0.contract_with_precheck(plan)` → `contract_from_plan` | **未到達**（段3 の材料が無い） |
| 段5 Qwen GENERATE | `dw.dispatch` / `build_planner` | 未到達 |
| 段6 Qwen AUDIT | `domain_dw.audit_case` | 未到達 |
| 段7 機械テスト | runner | 未到達 |
| 段8 GM 再観測 | `item_state` | 未到達 |

**2DER 単独で通過した段 = 1**（段1）。

## 2. 段1（成立）―― GM から取得した現在地

`manager_v0.item_state("ITEM-2DER-EVO-0077")`:

```
status           = "PROPOSED"                    <- roadmap_registry.resolve.status
task_ids         = ["TASK-2DER-3BD206A0"]        <- roadmap_registry.resolve.task_ids
task_details     = dw_state / next_operation / rthread_id …  <- front door /api/state
rri_thread       = RTHREAD-206fd571              <- ITEM→TASK→RRI
artifact_ids     = []                            <- roadmap_registry.resolve.artifact_ids
evidence_de_ids  = []                            <- roadmap_registry.resolve.evidence_de_ids
change_ids       = []                            <- roadmap_registry.resolve.change_ids
wiring_evidence  = null                          <- roadmap_registry.resolve.wiring_evidence
```

**F1 を Claude の記憶ではなく 2DER の面から再確認した。** 3欄は空のまま。

## 3. 段2（△）―― blocking を機械可読で持つ面が無い

**探した範囲（★「無い」の前に書く）:**

```
GM の 公開面        … tick / whose_turn / item_state / to_domain / contract_with_precheck /
                      submit_next_contract / receive_finished / record_stages / set_current_task
台帳               … roadmap_registry.resolve / items（★F1 は ITEM-2DER-EVO-0077 に ★散文で 在る）
TASK 層            … front door /api/state の `completion_blockers`（★在る。★ただし TASK 単位）
front door         … /api/control の 鍵（completion / forecast / interventions / offramp_flags …）
```

**∴ 管理層の blocking は「ITEM の description（散文）」としてしか存在しない。**
TASK 層の `completion_blockers` は在るが、**層が違う**（1件の依頼が完了できない理由であって、GM の blocking finding ではない）。

## 4. 段3（✗ 停止）―― 口は在る・収穫が 0

**2DER の面がそのまま返した値:**

```
function_table.menu()           = ['受信','検証','分類','登記','配送','監査','実行','rollback',
                                   'NOT_IN_LIST','NOT_DECIDED']
function_index('登記','machine') = {"in_list": true,  "components": [], "count": 0}
function_index('登記','hand')    = {"in_list": true,  "components": [], "count": 0}
function_index('追記', …)        = {"in_list": false, "components": [], "count": 0,
                                    "note": "一覧に無い(★エラーにしない・★引かれた回数には数える)"}

function_list()      = by_origin {"hand": 8, "machine": 0} ／ names 8 ／ rows 8
function_table_view():
    by_origin_note   = "★hand の8語は module の定数=★記録から来ていない(★実績と読まない)"
    records          = 90（3走行）
    funnel           = asked 30 / name_captured 0 / unanimous_not_in_list 0
    undecided        = DISPATCH.next_legal_operation … votes NOT_DECIDED
```

**∴ 機能表は「動いてはいるが 1件も 捕まえていない」。**
**GM が `append_task_id` に辿り着く道が、2DER 側に無い。**

**★これが「GM が Claude なしで F1 を処理するために不足している最小機構」。**
不足しているのは *F1 の実装* ではなく、**「既存 pattern を名前で引ける面」**。

## 5. Work Packet 側（段4）は口が在る ―― 材料が無いだけ

```
manager_v0.contract_with_precheck(plan) → to_domain → domain_dw.contract_with_precheck(plan)
    ① precheck_names（判定=2DER の `name_matches_route`）
    ② STOP なら 契約を 作らない
    ③ GO なら `contract_from_plan(requirement, target_file, test_plan, test_body)`

★Qwen へ 渡す 口は ★2本 在る:
   ①契約（骨格＋封印試験）… `test_body` = ★完全な python source が 要る
   ②BUILD_CAPABILITY … `build_planner.build_plan()`（★Qwen が PLAN を作る）
     ★この部品の 存在理由（逐語）= 「That made Claude a REQUIRED runtime PLAN actor.」
     ＝★Claude を PLAN から 外すために 既に 作られている
```

**∴ 段4以降の口は揃っている。止めているのは段3だけ。**

## 6. FINDING（★修理していない・本線へ昇格させていない）

| # | 何をしていて発見したか | 一周を物理的に不可能にするか | 既存機能で解決できるか | 別ITEM化 |
|---|---|---|---|---|
| **F8** | 段3 で EXISTING_ANALOG を引こうとして | **★する（停止点）** | 口（`function_index`）は在る。**収穫が0**＝機能表 段3 の取り込みが未達 | 既存の機能表 item の範囲（★新ID を作っていない） |
| **F9** | 段2 で blocking を引こうとして | しない（散文で代替可） | 管理層の blocking を持つ面が無い（TASK 層の `completion_blockers` は層違い） | 同上 |
| **F10** | 現在地を2面から引いて | しない | `/api/roadmap.status_counts` 合計 **136** ／ `roadmap_registry.items()` **144** ＝**鍵が違う** | 記録のみ |

**FINDING 数 = 3（新規）／ そのうち一周を止める物 = 1（F8）。**

## 7. 最終報告（Taka 指定の項目）

```
★2DER 単独で 通過した段        = 1（段1: GM 現在ITEM観測）
★Qwen が 担当した段            = 0（★段5-7 へ 到達しなかった）
★Claude が 必要になった段       = 2（段2 の blocking 供給 ／ 段3 の analog 供給）
★Taka が 必要になった段         = 0
★新規実装数                    = 0（★今回 1行も 実装していない）
★新規判断規則数                = 0
★FINDING 数                    = 3（止める物 1）
★GM→Qwen→GM の 一周           = ★成立しなかった
★次回 Claude を 呼ばずに 済むか = ★いいえ（★段3 が 埋まるまで）
```

**★主指標「Claude を通常経路から1回外せたか」= ★外せていない。**
**★外すために必要な最小の1つ = 機能表 段3 の収穫を 0 から 1 にすること（F8）。**

## 8. していないこと

```
★F1 を 実装していない ／ 穴埋めして 完走させていない
★新ID 0 ／ 新台帳 0 ／ 新証拠形式 0 ／ 新判断器 0
★submit を 1本も 投げていない
★経路表は route_table_view()（合成後）を 使い、route_table.py の hand 側だけを 読んでいない
★管理経路が 経路表に 出ない件は 既知 FINDING の まま 触っていない
```
