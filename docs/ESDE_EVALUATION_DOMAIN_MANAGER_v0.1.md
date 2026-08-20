# ESDE Evaluation Domain Manager v0.1 ―― 2DER の 構造監査 指標（★正本）

**受領 2026-08-20（Taka）／ ★試験導入 ／ ★最初の 実測 = `CC_MGR_2026-08-20_ESDE_AUDIT_real_repo_reflection.md`**

## 1. 役割分離（★ESDE 原型 → 2DER）

| 概念 | 2DER への 変換 | 第一段階 |
|---|---|---|
| 対等性 | 存在を 先に 価値づけて 捨てない ―― ★観測・列挙・比較の **制約** | ★採点しない（前提） |
| **対称性** | 作る側／読む側、要求／受入、入口／出口の **対応充足** | **★測る** |
| **連動性** | declared edge と observed edge の **一致・伝播** | **★測る** |
| **階層性** | 責務・authority・層境界・正規経路の **適合** | **★測る** |
| 軸(AXIS) | 関連する 存在群を 囲う **集約境界**（★採点項目では ない） | ★単位と して 使う |
| 了解 | 因果鎖が **閉じた**か（★局所情報の 有無では ない） | ★上位状態 候補・後段 |
| 創造性 | 予測から 外れ かつ GOAL への 距離を 縮めたか | ★事後評価・後段 |

## 2. 測り方（★総合点に 潰さない）

```
Symmetry : required_counterparts / present / ★missing_ID
Linkage  : declared_edges / observed_edges / ★broken_ID
Hierarchy: required_boundaries / passed / ★violation_ID ／ unreachable

★正本には ★★分母・分子・欠損ID を 残す。
★百分率は ★表示のみ。★『72点だから良い』では なく ★『何が 2件 欠けているか』を 2DER が 判断できる 形に する。
```

## 3. 軸の 再帰

```
AXIS=DW    → 内部の 存在群を Symmetry / Linkage / Hierarchy で 測る
AXIS=2DER  → RRI / DW / EGL / Manager / Runtime を ★存在と して 相互に 測る
★★＝ ★軸は 入れ子に なる。★同じ 3指標を そのまま 上位へ 適用できる。
```

## 4. 第一実測（★AXIS = REAL_REPO_REFLECTION ／ 2026-08-20）

```
Symmetry : required=6 / present=4 / missing=2
   missing_ID = ENERGIZATION_ADJUDICATION(writer) / ENERGIZATION_REVOCATION(writer)
   ★別枠: 本番 caller を 持つ counterpart = 1/6
Linkage  : declared=8 / observed=6 / broken=2
   broken_ID = ①Taka authority→adjudication record / ⑥energize token→apply
Hierarchy: required=5 / passed=4 / violation=1 / unreachable=0
   violation_ID = 新規file配置(_place_and_commit) と 既存file変更(apply_cycle) の 責務差を 混同
                  （★機構では なく ★観測者(Claude)の 認識 violation）
```

## 5. ★この 一件が 3指標で どう 読めるか（★Taka メモ §5 の 検証）

```
★対称性欠損 = ★linkage を 読む 門は 在る が ★作る 本線主体が 居ない  … ★実測で 一致
★連動性欠損 = ★GENERATE → sandbox → 実 repo が ★既存file変更で 閉じない … ★実測で 一致
★階層性欠損 = ★新規file配置 と 既存file変更 の 責務差の 見落とし        … ★実測で 一致
★★＝ ★3指標は ★今回の 失敗を ★3つの 別々の 欠損と して 正しく 分離できた。
★★＝ ★『連動性だけの 故障』と 読んで いたら ★対称性(writer 0)を 見落として いた。
```

## 6. 2DER への 導入順序（★Taka メモ §8）

```
①今回を 最初の 実測データに する          … ★済（本文 §4）
②分母・分子・欠損ID を 機械取得できるか   … ★一部 済（★下記）
③RRI / DW / EGL / Manager を AXIS と して 同形式で 集約
④総合点を 作らず 離散 finding と 分母付き 測定値を 保持
⑤実例が 溜まってから 『了解』を 上位状態と して 定義
⑥創造性・対等性は 実例から 役割を 決める
```

**★機械取得の 現状（★実測）:**

```
✔ Symmetry の reader/writer      … ★全件検索で 機械取得できる（★作用ベース）
✔ Linkage の observed edge       … ★`etrace.resolve_task → run_ids → resolve_run` の `handed_to`
                                   ＋ ★`completion_blockers` の `LINKAGE_EDGE_NOT_OBSERVED`（★実装済）
☐ Linkage の declared edge       … ★PLAN の `linkage.required_edges`（★第四が 未完 ∴ 本線で 生まれない）
☐ Hierarchy の required boundary … ★★機械の 一覧が 無い（★今回は 私が 手で 5件 挙げた）＝ ★UNVERIFIED
```

## 7. ★後で 繋げる ための 名前

```
★この 指標系の 名前 = ★★`ESDE Evaluation Domain Manager`
★★2DER 側の 位置づけ = ★Domain Manager の 1つ（★RRI / DW / EGL と 同じ 段）
★★いま 作らない もの = ★新しい 台帳 ／ 新しい state ／ 総合点
★★次に 決める こと = ★Hierarchy の `required boundary` を ★どこから 機械取得するか
```
