# A2/A3 — 明細基盤と自動循環の適用拡大 v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**ITEM: `ITEM-2DER-EVO-0094`**
**裁定（逐語・要点）: A1はUNVERIFIEDのまま固定しA2・A3へ進む／A2/A3では「PLAN品質が改善する」ことを前提にしない／
A2は少数実走→保存則・取消/訂正経路確認→母数へ拡大／A3は未記帳候補を軽量抽出しManagerが1件ずつ冪等に処理する。146件を一括で流さない**

**★前提にしていないこと: PLAN 品質の改善（A1 は UNVERIFIED のまま。本記録は品質を1つも主張しない）**

---

## 1. ★before / after

### 1.1 ★鍵を揃える — 分母は3つある

**明細（`QUESTION_RAISED`）と構造化（意味単位）は 1:1 ではない。**
実測の例: ED65242E は明細27に対し構造化33。
∴ 構造化を明細で割ると 113.9% になる（★最初そう出して誤った）。**分母を分けて出す。**

### 1.2 実測

| 指標 | before | after | 差 |
|---|---|---|---|
| 明細総数 | 1,017 | **1,018** | +1 |
| 構造化の行 | 33 | **1,160** | **+1,127** |
| 科目割当 | 27 | **644** | **+617** |
| evidence | 5 | **9** | +4 |
| 処分 | 5 | **5** | ±0 |
| 未記帳run | 146 | **142** | **−4** |
| thread状態 | SOFT 667 / NARROWING 1 | **SOFT 668 / NARROWING 1** | +1（新規投入） |

**分母つき（after）**

```
【明細 1,018 を分母】     科目割当 644 (63.3%) ／ 処分 5 (0.5%)
【thread 669 を分母】     構造化された thread 130 (19.4%) ／ 根拠を持つ thread 6 (0.9%)
【走行を分母】            未記帳の走行を持つ task 142
```

---

## 2. A2 — 明細基盤への適用拡大

### 2.1 作ったもの: `twoder/detail_backfill.py`

- **`dry_run=True` が既定**（1バイトも書かず、何が起きるかだけ返す）
- **`QUESTION_RAISED` を書き換えない**（append-only）
- **処分（verdict）を付けない**（「満たされた」は根拠が要る別の判断）
- **LLM を呼ばない**（種別は `requirement_structure`＝決定論、科目は2層モデルの割当を引くだけ）
- **新 state / event type / ID は 0**（`record_typed` と `assign_account` をそのまま呼ぶ）
- **chart に無い科目は割り当てない**（off-chart は fail-closed）

### 2.2 ★計画の段階で設計の欠陥を1つ直した

最初の計画は **219件**しか割り当てられなかった（母数は644）。
原因は **科目の割当は原文を要らないのに、`goal` が無い thread を丸ごと外していた**こと。
∴ **原文が要るのは構造化だけ**に直した → **219 → 617件**。
封印試験 `test_assignment_does_not_require_the_request_text` で固定した。

### 2.3 少数実走（3 thread）→ 保存則・取消/訂正

```
書いた: threads 3 / typed 1 / assigned 3 / errors 0
★保存則: 3 thread とも I1/I2 例外なし
★raised_total 不変 ／ ★起票時 per_account 不変（QUESTION_RAISED を書き換えていない）
```

**★取消／訂正の経路を実際に通した**

```
いまの科目            LDET-d7526ed4
UNCLASSIFIED へ戻す → UNCLASSIFIED
★履歴は消えない      [('LDET-d7526ed4','LEDGER_ACCOUNT_TREE …'), ('UNCLASSIFIED','取消の実証')]
付け直す             → LDET-d7526ed4
★取消/訂正の後も I1/I2 例外なし
```

### 2.4 母数へ拡大

```
PLAN  60.5秒  対象 370 thread
APPLY  5.2秒  threads 370 / typed 1,126 / assigned 614 / ★errors 0
★保存則 検査 370 thread / ★破れ 0件
```

### 2.5 ★正直に言うこと — 構造化の 562/1,127 は `UNVERIFIED`

書いた構造化行の種別分布:

```
FACT 203 / CHANGE 120 / SPEC 72 / TEST 56 / CONSTRAINT 98 / GOAL 16 / ★UNVERIFIED 562
```

**半分は種別が決まらなかった。** それでも書く理由は、`UNVERIFIED` 行も
**原文・原文中の位置・親request を持つ**（＝メモ §5「原文へ戻れる」を満たす）ため。
**「分類できた」とは主張しない。**

---

## 3. A3 — 自動循環の適用拡大（★146件を一括で流さない）

### 3.1 作ったもの: `manager_v0.feedback_one()`

**1巡回で1件だけ**進める。抽出は `scan_unrecorded(limit=1)`（走行台帳を1回流すだけ＝実測2.0秒）、
書き込みは段4の `record_evidence` をそのまま呼ぶ。`main()` の巡回に繋いだ。

### 3.2 実測

```
未記帳候補 145件
 1周目 -> TASK-2DER-0386DEC8   走行の結果を明細へ戻した
 2周目 -> TASK-2DER-03BA0E33   走行の結果を明細へ戻した
 3周目 -> TASK-2DER-043FFB61   走行の結果を明細へ戻した
★3周後の候補 142件（★減った 3）
★毎回 別の案件を拾った: True
★同じ案件を2回処理しても根拠は 1件 → 1件（増えていない）
★保存則 I1/I2 例外なし
```

常駐（`twoder-manager.service`）を再起動して新しい巡回を読ませた。**`limit=1` は変えていない。**

---

## 4. 触っていないもの

- `dev-workcell` / `webui.py` / `domain_dw.py`
- `EVENT_TYPES` / `DISPOSALS` / `STATES` / `TRANSITIONS` / `UNCLASSIFIED_FORBIDDEN_DISPOSAL`
- `QUESTION_RAISED` の値 ／ `per_account_balances` ／ `suspense_balance`
- **処分（verdict）** ―― 5件のまま。**「満たされた」を機械的に付けていない**

## 5. 未確認・残り

1. **構造化された thread は 130/669（19.4%）** ―― 残りは TRACE に居ないか原文が引けない
2. **科目が付かない 374件（1,018−644）** ―― 2層モデルの corpus 外（提案が立っていない明細）
3. **thread 状態は SOFT 668 のまま** ―― `present_gaps` の本番呼び手が0件で先へ進めない（B1）
4. **未記帳 142件** ―― 常駐が1巡回1件で進める。**一括で流していない**
5. `UNVERIFIED` 562件をどう減らすかは未着手（`requirement_structure` の規則の問題）
6. **A1 は UNVERIFIED のまま固定**。EF6826DC 等での再検証は別途（本記録は品質を主張しない）
