# 宛: 設計 / 監査 ―― Domain Manager Design v1 を閉じる（Taka 裁定 B）

## 0. 裁定

**B を採用**（Taka・逐語）:
> 正本 §18 に従い、必須材料集合の自動確定と Worker 選定の高度化は別段階へ戻す。
> v1 では条件3/4/7を成立済みとし、5/6/8 の本線接続と実行証拠の紐づけだけを閉じる。
> 語彙拡張や案件選び直しには入らない。

根拠は正本 §18 の逐語 ―― **「調査、分割、見積り、資源割当、必須材料集合の自動確定などは別段階である」**。
完了条件1/2 は v1 に対して重すぎた（正本が別段階と定めた責務を v1 に要求していた）。

## 1. 入れた物（新部品 0）

`twoder/domain_dw.py::design_from_case(task_id)` ―― **未接続だった 2DER 製部品8件の唯一の呼び元**。
`manager_v0.DOMAIN_OPERATIONS` に**1行足しただけ**（G の関数は1つも変えていない＝③の効き目）。

閉じるために足したのは3点だけ。

1. **`accept_integration`** ―― 統合結果が空でも Domain Manager が受理したことを本線記録へ。
   **空を残さないと「やらなかった」と「受け取ったが0件」が区別できない。**
2. **`transform`** ―― 変換が本線から呼ばれた証拠（使った部品名を名乗る）。
3. **`set_current_task`** ―― 各段の `_use` 記録を案件に紐づける。
   **`_use` に引数を足さなかった**（部品の kwargs と衝突し、既存の呼び手を全部直すことになるため）。

## 2. 実測（本番経路・`to_domain` 経由）

```
error = None
§3 Worker 起動   READY_FOR_AUDIT → DISPOSITION_REQUIRED   moved=true / dispatched=true
§4 統合          verify_material = ("CONDITION_NOT_MET", 0, 0)
§6 変換          WU-DM-0001 / completion=NO_COMPLETION_IN_DOCUMENT
★本線記録 events  8 → 27
   MANAGER_V0/use_part 7 ／ find_roles・determine_role・verify_material・
   completion_from_materials・extract_test_names・assemble_acceptance・
   assemble_work_unit_v2 が各1 ／ DOMAIN_DW/accept_integration 1 ／ DOMAIN_DW/transform 1
```

## 3. 完了条件の判定

| # | 条件 | 判定 |
|---|---|---|
| 1 | 必須材料が Domain Manager 側で決まる | **別段階へ戻す**（正本 §18） |
| 2 | Worker が Domain Manager 側で決まる | **別段階へ戻す**（同上） |
| 3 | Worker が1つ実際に起動する | **成立** `moved=true` / `dispatched=true` |
| 4 | 結果が Domain Manager へ戻る | **成立** |
| 5 | 結果が統合される | **成立** `accept_integration` が案件に紐づく（空でも受理を記録） |
| 6 | WorkUnit / Contract へ変換される | **成立** `transform` + `WU-DM-0001` |
| 7 | Claude の手書き中間処理なし | **成立** `to_domain` 経由・語の詰め替えなし |
| 8 | 各段の実行証拠が本線記録に残る | **成立** events 8→27・`task_id` で引ける |

**∴ Domain Manager Design v1 を閉じる。**
「材料自動確定まで含む完成版」ではなく、**本線で Domain 処理を実行し、結果を統合・変換できる第一版**として。

## 4. 閉じた後に残る物（棚上げ・v1 の未完として抱え込まない）

| 残件 | 分類 |
|---|---|
| 必須材料集合の自動確定 / Worker 選定の高度化 | **別段階**（正本 §18） |
| `find_roles` の5語が実装依頼の文面に当たらない（`roles=0`） | 一般化 |
| `make_routing_string` が**一度も呼ばれていない**（`roles=0` のため未実証） | 一般化 |
| `completion_from_materials` と `find_roles` の役語彙が噛み合わない | 一般化 |
| 12件の抽出欠陥 ／ 29件の材料欠落 ／ completion 語彙 ／ 軸2/5 ／ 段2の乖離 | 一般化・堅牢化 |
| G→D の名指し3件 ／ `domain_dw` 内の `route_table` 実体 | 負債 |
| 入口の拒否理由が出ない ／ RRI_INTENT_HOLD の揺れ ／ 投入済み未完の観測 | 別工程 |
| **経路表に Domain Manager の区間が0** | **別工程（下記）** |

## 5. 経路表について（Taka の指摘を受けて）

**指摘は当たっていた。** 私は経路表を引かずに手で grep して母数を作った。
引いた結果:

```
route_table.py = 18区間・すべて実装の線（S01 submit → S18 close）
18区間の全文に含まれる語: account 0 ／ domain 0 ／ material 0 ／ role 0 ／ work_unit 0 ／ experience 0
最終 commit 2026-08-17 [Claude実装] ＝ 自動更新ではなく私が手で入れている
```

**Domain Manager の線は経路表に宣言されていない。** だから8部品が繋がっていなくても経路表は何も言わない。
今回**区間を足していない** ―― 18という数に依存する計器が他に在り、増やすと壊す恐れがあるため、
**先に依存を測るべき**と判断した。**別工程として上げる。**

## 6. 監査への依頼

- **v1 を閉じる判定が妥当か。** 特に「条件1/2 を正本 §18 に戻す」読みを独立に確かめてほしい。
- **条件5/6/8 の成立を、私の報告ではなく `/api/etrace?task_id=TASK-2DER-5980A06B` から引いて確かめてほしい。**
- `make_routing_string` **未実証**を、v1 成立の傷とみなすかどうか。
