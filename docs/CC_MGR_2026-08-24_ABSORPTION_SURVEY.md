# chart外候補の吸収可能性 全件調査（★読み取り専用・★採用0・★新語ゼロ）

作成: Claude Code (MGR) / 2026-08-24 / ITEM: `ITEM-2DER-EVO-0100`
実装: `twoder/domain_ledger.ledger_absorption_report()`（Ledger Domain の調査口）

Taka 裁定 逐語:
「chart外43件について、既存採択済み科目への吸収可能性を全件調査する。」
「目的は43件をそのまま採用することではなく、既存科目へ吸収可能 / 部分的に吸収可能 /
 本当に新規科目が必要 / 判定不能 に分けること。」
「ただし分類名は新設せず、既存語彙で表現可能か先に全件調査する。」
「名称・意味・authorityは自動確定しない。新規科目採用は候補提示までで止める。」

## 1. ★分類名を新設していない（既存語彙の全件調査の結果）

| 使ったもの | 出所（既存） |
|---|---|
| **`NOT_IN_LIST` / `NOT_DECIDED`** | `account_gate._menu()` ＝ `[採択済みの科目id …] + [NOT_IN_LIST, NOT_DECIDED]`。★front door が LLM に渡す一覧そのもの |
| **既存科目id** | `chart`（`request_thread._load_chart`） |
| **過半数の線 0.5** | `s_ledger_account_tree.INHERIT_MIN_SHARE`（★同一性継承で既に採った規則） |
| **「依頼ではない」5語** | `unverified_diagnosis.CAUSES`(閉じた10語) のうち `task_similarity.eligible_details` が逐語で分類対象外にしている `STATUS_REPORT` / `USER_NOTE` / `MARKER_ONLY` / `HEADING_FRAGMENT` / `EMPTY_OR_TOO_SHORT` |

★**`new_words_introduced: 0`**。4つの分けは `menu_verdict` と `share` の組で表す:

- 既存科目id ＋ share ≥ 0.5 → **吸収可能**（過半数 ∴ 行き先が一意）
- 既存科目id ＋ 0 < share < 0.5 → **部分的に吸収可能**
- `NOT_IN_LIST` → **本当に新規が必要**（既存科目が1件も持たない）
- `NOT_DECIDED` → **判定不能**（材料が引けない）

## 2. ★分母と鍵の違い（先に断る）

```
tree 詳細 88 / chart 63 / ★chart外で対象明細を持つ候補 8件 / ★対象明細 計 59
```

★**59 は「CHART_ABSENT 43件」とは別の鍵**。43＝未割当明細のうち tree の detail_id が chart 外のもの。
59＝候補の members のうち、いま科目が無いもの。**持ち越し(`carried_forward`)の member 集合が重なるため
同じ明細が複数候補に現れ得る**。混ぜてはいけない。

## 3. ★★4つの分け

| verdict | 候補数 | 対象明細 |
|---|---:|---:|
| **`NOT_IN_LIST`**（本当に新規が必要） | **5** | **37** |
| `PARTIAL`（部分的に吸収可能・share < 0.5） | 2 | 18 |
| `EXISTING_ACCOUNT`（吸収可能・share ≥ 0.5） | 1 | 4 |
| `NOT_DECIDED`（判定不能） | **0** | **0** |

## 4. ★★もう一段絞れた ―― 59件のうち **25件は依頼ではない**

| axis_id | verdict | members | 対象 | share | ★依頼 | ★依頼外 | evidence | 診断（既存語） |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `LDET-5d6ea6cf` | NOT_IN_LIST | 18 | 17 | 0.00 | **17** | 0 | 0 | MULTI_KIND_CANDIDATE 14 / MULTI_STATEMENT 3 |
| `LDET-dd12b59f` | NOT_IN_LIST | 16 | 13 | 0.00 | **0** | **13** | 0 | **STATUS_REPORT 13** |
| `LDET-1e6a6ce0` | NOT_IN_LIST | 3 | 3 | 0.00 | **0** | **3** | 0 | **STATUS_REPORT 3** |
| `LDET-60107ae8` | NOT_IN_LIST | 4 | 3 | 0.00 | **3** | 0 | 0 | VOCAB_MISS 3 |
| `LDET-014d9b4d` | NOT_IN_LIST | 12 | 1 | 0.00 | **0** | **1** | 0 | **MARKER_ONLY 1** |
| `LDET-68d67c42` | PARTIAL(`LDET-b654430e`) | 18 | 15 | 0.11 | **7** | **8** | 0 | VOCAB_MISS 7 / **USER_NOTE 8** |
| `LDET-92ff6ce4` | PARTIAL(`LDET-dc8bc11f`) | 6 | 3 | 0.33 | **3** | 0 | 0 | VOCAB_MISS 3 |
| `LDET-9445a9c5` | EXISTING(`LDET-f71e5f63`) | 22 | 4 | 0.50 | **4** | 0 | 0 | VOCAB_MISS 4 |

★**依頼ではない 25件 / 依頼である 34件**。
★`evidence` は **全候補で 0件**（根拠が明細粒度に降りていない ―― 既知の壁）。

## 5. ★★人の裁定へ残すもの ―― 5候補 → **★2候補（対象明細20件）**

`NOT_IN_LIST` 5候補のうち、**3候補（17件）は中身が依頼ではない**（`STATUS_REPORT` 16 / `MARKER_ONLY` 1）。
∴ **科目を付ける対象ではない**。

★**本当に新規科目が要るのは 2候補だけ**:

| axis_id | 対象明細（依頼） | 中身 |
|---|---:|---|
| **`LDET-5d6ea6cf`** | **17** | `load_port(path)` / JSONL 集計 など ―― 実装依頼 |
| **`LDET-60107ae8`** | **3** | `ValueError を送出する` ―― 実装依頼 |

★名称・意味・authority は**自動確定していない**。★**採用していない**（候補提示まで）。

## 6. ★段2の `NOT_DECIDED` がどこまで減る見込みか（再計算）

現状 `NOT_DECIDED 726 / NOT_IN_LIST 4`（提案720行）。少数実走では **10/10 が NOT_DECIDED**。

- 2候補（20件）を採用しても、**chart は 63 → 65**（＋2科目）
- 段2 が選べる一覧が 2件増えるだけ ∴ **`NOT_DECIDED` の大幅な減少は見込めない**
- **★見込みを数字で言えない** ―― 段2 の出力は同じ入力でも揺れる（3-seed 合議）ため、
  ★**実測しないと分からない**。★推測で数字を置かない。

★**測る方法**：2候補を採用した後、**同じ10件を再投入**して `NOT_DECIDED` 率を比べる（before 10/10）。
これなら分母が同じで比較できる。★但し **提案は既に立っている**ので、再投入には別の口が要る（未実装）。

## 7. ★117件の投入可否について（私の見立て）

★**いま投入しても鍵Bは1件も動かない**（少数実走の実測: 提案は付くが科目は付かない・鍵B ±0）。
∴ **投入は止めたまま**を推す。先に **2候補の採用**と、上の**再投入による実測**を通す方が順序として正しい。

## 8. ★やっていないこと（隠さない）

- **採用0**（`admit_ledger_tree_accounts` を1度も呼んでいない）
- **名称・意味・authority を自動確定していない**
- 残り117件を投入していない
- 重複proposal 32行を**この調査に混ぜていない**（別問題）
- `evidence` が全候補0件である理由は**未測**（明細粒度の根拠が無いという既知の壁の再確認まで）
