# 段5 — 明細の「満たされたか」は今日1件も書けない（構造判定 v0.1）

**作成: Claude Code（MGR）／ 2026-08-23**
**基準: `TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1.md`（`ART-948e04d27a`）§4／現状対応表（`ART-576edd4ee2`）§7 の未確認事項**

## 0. 結論を先に

現状対応表 §7 に**未確認**として残していた問い —

> `dispose_question` が0件なのは「使っていない」のか「使えない」のかを分けていない。
> UNCLASSIFIED の問いは `RESOLVED` 処分ができない出口規則が在るため、**構造的に詰んでいる可能性**がある。

**判定: 使えない（構造的に詰んでいる）。** 推測ではなく、**門を1つずつ与えて実際に拒否させて**確かめた。

**そして原因は1つではなく、4連の欠落である。**

---

## 1. 実際に拒否させた結果（隔離した捨て場で実行。本番台帳へは1バイトも書いていない）

```
UNCLASSIFIED + RESOLVED     -> 拒否: UNCLASSIFIED question cannot be disposed as RESOLVED
UNCLASSIFIED + OPEN_GAP     -> ★通った
UNCLASSIFIED + REJECTED     -> ★通った
UNCLASSIFIED + MERGED_INTO  -> ★通った
科目つき     + RESOLVED     -> ★通った
```

∴ **「満たされなかった」側は今日でも書ける。書けないのは `RESOLVED` だけ。**

### 1.1 承認しても開かない

```
propose_account(IN_LIST, ACC-REAL) を入れた後で RESOLVED
  -> 拒否: UNCLASSIFIED question cannot be disposed as RESOLVED
  ★dispose_question が見ている account_id: UNCLASSIFIED
```

`dispose_question` は `account_id` を **`QUESTION_RAISED` からしか読まない**（`_read` して最初の1件で `break`）。
`QUESTION_RAISED` は append-only で書き換えられない。
∴ **UNCLASSIFIED で起票された明細は、後から何をしても永久に `RESOLVED` にできない。**

実測: 明細974件のうち **UNCLASSIFIED 758件(78%)**。ED65242E の27件は **100% UNCLASSIFIED**。

---

## 2. 4連の欠落（どこが切れているか）

```
① 新しい勘定科目2層モデル(58科目)は rthread_chart.json に ★1件も入っていない
      chart の有効科目は ★5件だけ（ACC-1e5f5c5a / ACC-53c96ac2 / ACC-d32cd53e /
      ACC-dc4c648f / AX-cee7bf57 ＝ 試験で作った古いもの）
      check_account_conservation は off-chart account を fail-closed で halt する
   ↓
② approve_account は chart と名前ファイルには書くが ★明細には書き戻さない
      → 明細の account_id は UNCLASSIFIED のまま
      ★「決まった科目を既存の明細へ割り当てる書き手が、そもそも存在しない」
   ↓
③ dispose_question は QUESTION_RAISED の account_id しか見ない
      → ②が直っても、この口が見る値は変わらない
   ↓
④ thread を RESOLVED 状態へ進めるには present_gaps が要るが、★本番の呼び手は0件
      拒否の実測: "unpresented OPEN_GAP remains before RESOLVED"
      さらに ★ds_delivery_receipt は中身を検査していない（任意の文字列が通る）
      呼んでいるのは試験1本と監査の逐語照合1本だけ
```

これで **UNCLASSIFIED 78% / 科目提案の NOT_DECIDED 99.1% / dispose 実行0件** が
1つの原因ではなく**連鎖**として説明できる。

### 2.1 thread 単位ではどこまで行けるか（実測）

```
UNCLASSIFIED だけの thread でも:
  OPEN_GAP で全件処分 -> I1 例外なし / I2 例外なし（UNCLASSIFIED は chart 外ではない）
  SOFT -> NARROWING   -> ★通った
  NARROWING -> RESOLVED -> 拒否（unpresented OPEN_GAP remains）
```

∴ **thread は「NARROWING で止まる」。詰んでいるのは明細の RESOLVED と、その先の提示経路。**

---

## 3. ★私の権限で直せるもの / 直せないもの

| 欠落 | 最小の修理 | 判定 |
|---|---|---|
| ① chart に58科目が無い | **人が1回承認する**（`approve_account` の設計そのもの。`approved_by` が要る） | ★Taka（上申条件⑥⑧） |
| ② 明細への書き戻しが無い | 新しい書き手（append-only の割当 event）を足す | 局所判断＝**私** |
| ③ dispose が初期値しか見ない | 現在の割当を見るように変える | ★上申（③既存正本と矛盾／⑧安全境界。出口規則は裁定 ADJUDICATION_SENSITIVE:16） |
| ④ present_gaps 未配線 | DS 側の受領発行 | 私の管轄外（DS） |

**②③を今作っても①が無い限り1件も発火しない。**
「仕組みに落とすか捨てるか」「規則だけ作って0件にしない」に従い、**①の裁定を先に取る**。

---

## 4. ★①を通すと何が動くか（分母つき）

| | 実測 |
|---|---|
| 新2層モデルが分類できている明細 | **644 / 648**（99%） |
| ED65242E の明細に科目が付く | **27 / 27**（既存 account_id は UNCLASSIFIED 100%） |
| EF6826DC の明細に科目が付く | **13 / 13**（同上） |
| chart の有効科目 | **5件**（すべて試験用の古いもの） |
| 新2層モデルの科目 | **58件**（大分類6 / 詳細52・うち命名未確定2件） |

**①は「58科目を chart へ入れてよいか」という Taka の1回の判断であり、それだけで②③の修理が意味を持つ。**

---

## 5. 触っていないもの

- 本番の `rthread_events.jsonl` — **段5 では1バイトも書いていない**（拒否の再現はすべて隔離した捨て場）
- `rthread_chart.json` / `ACCOUNT_AXIS_NAMES.jsonl` / `DISPOSALS` / `UNCLASSIFIED_FORBIDDEN_DISPOSAL`
- `dispose_question` / `present_gaps` / `approve_account`（**読んだだけ**）
- `webui.py`（担当が別インスタンス）

## 6. 未確認として残すもの

1. **処分を全 thread 横断で数える読み口が無い**。`list_account_proposals` は全件読めるが、
   処分にあたる global reader が無い。∴ 「dispose 0件」は個別 thread の観測からの推定であり、
   **全件で数え直していない**。
2. ①を通した場合、既存974明細は `QUESTION_RAISED` が UNCLASSIFIED のままなので、
   **②の書き戻しが無いと過去分は救えない**。新規のみか遡及かは未決。
3. `ds_delivery_receipt` に何を入れるべきかの正本が見つかっていない（中身が検査されていない）。
