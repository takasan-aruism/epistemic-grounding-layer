# 宛: Taka / 設計 / 監査 ―― DISPOSE の比率実測（★507 task 全件・新しい分類規則 0）

**`_TEST_CATEGORIES` / `_MAP` / disposition 規則を触っていない。所見の正誤を Claude が判断していない。**

## 0. 母数と鍵

```
★母数 = front door `/api/tasks` の 全 task = ★507（★手で 選んでいない）
★判定 = ★既存の `dw.disposition.mechanically_dispositionable(findings, view)` を そのまま 呼んだ
★findings = ★既存の `dw.workcell._latest_findings(view)`
★引けなかった task = ★0
```

## 1. 求められた数

| 項目 | 値 |
|---|---|
| **findings 総数** | **178**（★findings を持つ task = 125） |
| **機械処分可能** | **97 task** ／ **77.6%** |
| **judgment-required** | **28 task** ／ **22.4%** |
| **実際に Claude DISPOSE まで到達** | **11 回**（★`manager_identity = "claude-manager"`・延べ） |

### category 別（★findings 単位・178件）

```
test_failure                 ★97   （54.5%）← ★_TEST_CATEGORIES に 当たる
scope_expansion               27   （15.2%）
requirement_not_implemented   25   （14.0%）
test_not_load_bearing          9
self_report_primitive          9
dead_guard                     8
failure_pattern_recurrence     3
```

### 誰が処分したか（★記録の `manager_identity`・★自己申告ではなく記録）

```
dispose 記録を 持つ task = 101
   ★2der-auto-dispose  = ★122 回（★機械）
   ★claude-manager     = ★ 11 回（★Claude）
                          → ★機械 91.7% ／ ★Claude 8.3%

内訳:
   機械処分可(True) の task   … 2der-auto-dispose 122 ／ claude-manager ★1
   judgment-required(False) … claude-manager ★10（★機械は ★0＝★fail-closed が 効いている）
```

## 2. judgment-required は通常系か例外系か

**★例外系。** 根拠は2つ:

```
①★件数比  = ★22.4%（28/125 task）／ ★処分の 実行回数では ★8.3%（11/133）
②★機械が judgment-required を 処分した 記録 = ★0
   ＝★境界が 一度も 破られていない（★fail-closed が 実際に 効いている）
```

**★ただし「例外系」と言い切れない点も出た（★隠さない）:**

```
★現在 DISPOSITION_REQUIRED で 止まっている task = ★25
   うち ★judgment-required = ★18 ／ 機械処分可 = 7
★機械処分可なのに 止まっている 7件 = ★★DISPOSE を 誰も 呼んでいない だけ（★別件）
★judgment-required 18件 = ★Claude を 待っている 実数
```

**∴ 「Claude を待つ滞留」は現時点で 18件。★これは例外処理として現実的な量。**

## 3. 「証拠不足」か「本質的に裁量」か ―― **★既存フィールドでは区別不能（UNKNOWN）**

**★決定的な実測:**

```
★`reproduced` 欄を 持つ finding = ★★0 / 178
```

`disposition.py` の機械処分条件は逐語で2つ:

```
「an explicit `reproduced` boolean, or a test-category finding checked against the recorded
  generate `test_result`」
```

**★前者（`reproduced`）は一度も使われていない。∴ 実質 `category ∈ _TEST_CATEGORIES` の1本だけで判定されている。**

### findings が持つ欄（★178件の実測）

```
178件全部 : category / finding_id
 97件     : code_file / test_file / test_command / oracle_source / runner_identity / summary
 95件     : requirement / test_body
 88件     : env_signals
 81件     : evidence / severity / suggested_check
```

**★どの欄も「証拠が足りないから判断できない」と「本質的に裁量」を分ける欄ではない。**
**∴ ★UNKNOWN のまま残す。**（★新しい分類規則を作れば区別できるが、★Taka が禁じた ∴ 作らない）

**★注意（★私が判断してはいけない領域）:** 97件が `test_file` / `test_command` / `test_body` を持つ
＝**証拠は豊富にある**。それでも `category` が test 系でなければ機械処分されない。
**この設計が妥当かは所見の中身を読む判断 ∴ 私は評価しない。**

## 4. ★Taka の方針への当てはめ（★実測値のみ）

Taka 逐語:
> 「私なら現時点では、DISPOSE は Claude の『例外処理』として一旦残します。
>   目標は Claude ゼロではなく『ほとんど使わない』ので、真に判断が必要な数％まで消す必要はありません。」

**★実測はこの方針と整合する:**

```
★処分の 実行回数で 見ると ★機械 91.7% ／ ★Claude 8.3%
   ＝★★既に『ほとんど使わない』が 成立している
★機械が judgment-required に 手を 出した 記録 = ★0
   ＝★境界は 守られている
★いま Claude を 待っている 実数 = ★18 件
```

## 5. していないこと

```
★_TEST_CATEGORIES を 広げていない ／ _MAP を 触っていない ／ disposition 規則を 触っていない
★所見の 正誤を 評価していない ／ 新しい 分類規則 0
★DISPOSE を 実行していない ／ run_next 0
★UPPER_REVIEW に 進んでいない
★「証拠不足 vs 裁量」を ★推測で 埋めていない（★UNKNOWN のまま）
```
