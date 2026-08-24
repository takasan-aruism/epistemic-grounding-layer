# 未割当明細の原因分解 ―― 保存則が成立する排他分類（★読み取り専用）

作成: Claude Code (MGR) / 2026-08-24 / ITEM: `ITEM-2DER-EVO-0100`
実装: `twoder/domain_ledger.ledger_unassigned_report()`（★General ではなく **Ledger Domain の調査口**）

Taka 裁定 逐語:
「未割当422件を全件調査し、同じ鍵で原因を保存則が成立する排他的な分類に分解する。」
「実コードの条件から確定すること。」「422 = 各原因件数の総和を必ず成立させる。」
「分類名は実装前に既存語彙・既存条件を全件調査し、上記名称をそのまま新語として採用しない。」
「読み取り専用。名称・意味・authority・科目採用・identity操作は変更しない。」
「最終的に『422件を減らすには、どの上流工程を直せば何件動くのか』を件数付きで出す。」

## 0. 分母（★裁定時 422 → 実測時 **428**）

明細は常駐が回るたび増える。**同じ鍵**で測り直した時点の値が 428。

分母の定義（★実コード）:
- `ledger_rates` 逐語 `unassigned_num = total - assigned`
- `request_thread.count_questions` 逐語 `assigned` = **`QUESTION_ACCOUNT_ASSIGNED` が1件以上ある明細**

∴ **未割当 = 割当 event が1件も無い明細**。

## 1. 分類名の出所（★新語を作っていない）

裁定文の6語を**そのまま新語にしていない**。2つの既存語彙から採った。

**①区分** ＝ `twoder/gap_report.py` の逐語:

| 語 | 逐語の定義 |
|---|---|
| `NO_RECORD` | 記録が無い — そもそも書かれていない |
| `NOT_WIRED` | 記録は在るが繋がっていない — 機構は在り動かせるのに使われていない |
| `BROKEN` | 記録が壊れている — 書かれてはいるが中身が信用できない |
| `NOT_MEASURED` | 未測 |

**②原因名** ＝ **その条件を定義しているコードの識別子そのもの**:
`PROPOSE_ACCOUNT`(`request_thread.ACTOR_ACTIONS`) / `_ledger_records`(`s_ledger_account_axes`) /
`_by_question`(`account_tree`) / `_load_chart` / `list_threads` / `effective_account_of`(`request_thread`)

## 2. ★保存則 ―― 成立

```
unassigned_total 428  ==  sum_of_causes 428   holds: true
```

| 原因 | 区分 | 件数 | 直す上流工程 |
|---|---|---:|---|
| `THREAD_NOT_IN_LIST_THREADS` | BROKEN | **0** | `open_thread` / THREAD_OPENED |
| **`PROPOSE_ACCOUNT_ABSENT`** | **NO_RECORD** | **★385** | **`propose_account`（科目の提案を出す工程）** |
| `LEDGER_RECORDS_TEXT_EMPTY` | BROKEN | **0** | `raise_question` の memo |
| `BY_QUESTION_ABSENT` | NOT_WIRED | **0** | `s_ledger_account_tree`（★今日直したので0） |
| **`CHART_ABSENT`** | **NOT_WIRED** | **★43** | **`admit_ledger_tree_accounts`（科目の採用・人の裁定）** |
| `EFFECTIVE_ALREADY_EQUALS_TREE` | NOT_WIRED | **0** | W1 の条件 |
| **`NOT_MEASURED`** | NOT_MEASURED | **★0** | ★未測 |

★**説明できない件数は 0** ＝ 428件すべてが実コードの条件で説明できた。

## 3. ★各段で閉じていることの算術

```
明細総数 1,077
 ├─ 提案あり  692  ←★tree members 692 と ★完全一致
 │    ├─ 割当済み          649
 │    └─ chart 外(未割当)   43    →  649 + 43 = 692 ✓
 └─ 提案なし(未割当)  385

★未割当 = 43 + 385 = 428 ✓
```

## 4. ★★数には鍵を添える ―― 「未割当」は「科目が無い」ではない

`twoder/submit.py:623` は逐語 `if _c.get("account_id") in ("NOT_IN_LIST", "NOT_DECIDED")` の時**だけ**
提案を残す。∴ **LLM が既存科目を選べた明細は、起票（`raise_question`）の時点で科目が付き、
割当 event を経ずに科目を持つ**。

| 鍵 | 件数 |
|---|---:|
| **A** 割当 event が無い（`count_questions` の定義） | **428** |
| **B** ★実際に科目が付いていない（`effective` が UNCLASSIFIED/None） | **★179** |
| 差＝起票時に科目が付いた（A だが科目は在る） | **249** |

原因 × 鍵:

| 原因 | 件数 | ★科目が無い | 科目は在る |
|---|---:|---:|---:|
| `PROPOSE_ACCOUNT_ABSENT` | 385 | **136** | **249** |
| `CHART_ABSENT` | 43 | **43** | 0 |

★∴ **「未割当 428件」のうち 249件（58.2%）は既に科目が付いている**。
★数字を動かしたいのが「科目を付けること」なら分母は **179**、
「割当 event を残すこと」なら **428**。**混ぜてはいけない。**

## 5. ★★どの上流工程を直せば何件動くのか

| 上流工程 | 動く件数（鍵A） | ★動く件数（鍵B＝科目が無い） |
|---|---:|---:|
| **`propose_account`（科目の提案を出す工程）** | **385** | **★136** |
| **`admit_ledger_tree_accounts`（科目の採用・★人の裁定）** | **43** | **★43** |
| 他5工程 | 0 | 0 |

**`propose_account` の非試験の呼び手は `twoder/submit.py:623` の1箇所だけ**（5repo走査）。
∴ ★front door を通らずに立った明細（実測 direct 80%）は**提案が付く機会が無い**。

## 6. ★やっていないこと（隠さない）

- **読み取り専用** ―― 名称・意味・authority・科目採用・identity操作を**1つも変えていない**
- 385件に提案を付けていない / 43件を採用していない
- `propose_account` の呼び手を増やしていない（★これは設計変更 ∴ 裁定事項）
- 249件（起票時に科目が付いた分）に割当 event を後付けしていない
