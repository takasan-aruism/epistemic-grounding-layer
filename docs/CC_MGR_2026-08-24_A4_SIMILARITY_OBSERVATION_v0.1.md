# A4 — 類似群の観測（★テンプレートではない） v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**ITEM: `ITEM-2DER-EVO-0094`**
**裁定（逐語・要点）: いきなり「学習」しない／最初の出力はテンプレートではなく類似群の観測結果／
新しいIDや台帳を先に作らない／LLMだけで「似ている」と決めない／1件や2件の類似でテンプレートを作らない／
最初から必須条件やblocking ruleにしない／kind_vote / LLM分類は確定情報として使用しない**

---

## 1. ★正本入力の母数（5条件・実測）

| | 件数 |
|---|---|
| 構造化の全行（★現在有効version） | 1,159 |
| ③ `UNVERIFIED` で落ちた | −511 |
| ④ 分類対象外の候補で落ちた（STATUS_REPORT / USER_NOTE / 見出し / 原文不足 / マーカー） | −145 |
| ⑤ provenance / task_id が追えず落ちた | −0 |
| **★A4 が使える明細** | **503（43.4%）** |

```
kind別: FACT 193 / CHANGE 125 / CONSTRAINT 115 / SPEC 37 / GOAL 20 / TEST 13
★またがる TASK: 73（1 TASK あたり 中央値 3 / 最大 61）
```

**`proposed_kind` は1件も使っていない。** LLM の答えは正本入力に入れていない。

---

## 2. ★類似判定は既存機構だけ — 全件調査した

| 鍵 | 出所 | 73 TASK での実在 |
|---|---|---|
| `request_type` | TRACE の `RRI_RESOLVED_INTENT.request_type` | **73/73（100%）** |
| 勘定科目（2層・詳細科目） | `LEDGER_ACCOUNT_TREE` | **59/73**（★37種・うち25種が2 TASK 以上） |
| `kind` の分布 | 決定論で確定した6語 | 73/73 |
| `refs` の型 | 段2 の参照 | **★0/73（下記 §4.2）** |
| `REQUEST_KIND_COUNTS` / `REQUEST_GAPS` | TRACE | **5/73（7%）**＝段3 以降の投入のみ |

`request_type` の分布: `MODIFY_EXISTING` 29 / `BUILD_CAPABILITY` 26 / `OBSERVE_CURRENT_STATE` 18。

**★LLM は1回も呼んでいない。** 群の鍵は `(request_type, 詳細科目)` の組で、**どちらも既存機構**。
**新しい ID を作っていない** ―― `cluster_id` は鍵をそのまま連ねた文字列（`BUILD_CAPABILITY|LDET-4e3c2ee6`）。

---

## 3. ★類似群の観測結果（min_tasks=3 ／ 11群）

| cluster_id | TASK | 科目名 | required（その kind が在る TASK の割合） |
|---|---|---|---|
| `BUILD_CAPABILITY\|LDET-4e3c2ee6` | 7 | データ統合ツール | SPEC 0.71 / CHANGE 0.14 / GOAL 0.14 |
| `OBSERVE_CURRENT_STATE\|LDET-2d01f311` | 6 | 分析 | CHANGE 0.67 / SPEC 0.50 / CONSTRAINT 0.50 / FACT 0.17 |
| `BUILD_CAPABILITY\|LDET-b654430e` | 5 | 入力検証 | **FACT 1.00 / CHANGE 1.00** / SPEC 0.40 / CONSTRAINT 0.40 / TEST 0.20 / GOAL 0.20 |
| `MODIFY_EXISTING\|LDET-9fad13bd` | 4 | 完了ワークフロー | **FACT 1.00 / CHANGE 1.00 / CONSTRAINT 1.00** |
| `MODIFY_EXISTING\|LDET-aeb46ac5` | 4 | ルート分析機能記録 | **FACT 1.00 / CONSTRAINT 1.00** / CHANGE 0.75 |
| `MODIFY_EXISTING\|LDET-5e2f8ee4` | 3 | 単機能計画実装 | **CHANGE 1.00 / CONSTRAINT 1.00** |
| `MODIFY_EXISTING\|LDET-04574589` | 3 | タスク状態管理 | **FACT 1.00 / CHANGE 1.00 / CONSTRAINT 1.00** |
| `BUILD_CAPABILITY\|LDET-aeb46ac5` | 3 | ルート分析機能記録 | **FACT 1.00 / CHANGE 1.00 / CONSTRAINT 1.00** |
| `BUILD_CAPABILITY\|LDET-2d01f311` | 3 | 分析 | **CONSTRAINT 1.00** / FACT 0.67 / SPEC 0.33 |
| `BUILD_CAPABILITY\|LDET-26ee37a2` | 3 | ルート検証 | **CHANGE 1.00** / SPEC 0.67 / CONSTRAINT 0.67 / FACT 0.67 / TEST 0.33 / GOAL 0.33 |
| `OBSERVE_CURRENT_STATE\|LDET-d7526ed4` | 3 | 監査 | **FACT 1.00 / CHANGE 1.00** / CONSTRAINT 0.67 / SPEC 0.33 / GOAL 0.33 |

---

## 4. ★頻出 missing — これが A4 の本題

裁定の逐語「**この種類のTASKでは、事前に何を知っていればClaude/DWが余計な発明をしなくて済むか**」への
最初の観測。

### 4.1 全群を横断した不足（`missing >= 0.67` の群を数えた）

```
TEST        10/11 群 (91%)  ← ★どの種類の TASK でも 受入ケースが 書かれていない
GOAL         9/11 群 (82%)  ← ★終わりの条件が 書かれていない
SPEC         5/11 群 (45%)
FACT         3/11 群 (27%)
CHANGE       2/11 群 (18%)
CONSTRAINT   1/11 群 ( 9%)
```

**★`MODIFY_EXISTING` の4群は全部 `SPEC=1.00 / TEST=1.00 / GOAL=1.00` の不足。**
つまり「既存を直す」依頼では、**作る物の形も受入ケースも終わりの条件も一度も書かれていない**。

**これは EF6826DC の事故（SPEC 0 / TEST 0 → worker が発明して2周失敗）と同じ形が
群として繰り返し出ていることを意味する。**

### 4.2 ★共通 refs 型 — 11群すべてで 0件

```
★refs を 1つも持たない群: 11 / 11
```

段2 の参照抽出は**この 503明細のどれにも参照を付けていない**。
ED65242E は 33明細中4件だったが、**73 TASK の母数では 0**。
∴ **「file ref が必要」というテンプレート候補は、いまの材料では作れない。**

---

## 5. ★テンプレートは作っていない

裁定の逐語「1件や2件の類似でテンプレートを作らない」「最初から必須条件や blocking rule にしない」に従い、
**出したのは観測結果だけ**。`min_tasks=3` 未満の群は候補にしていない。

**テンプレート候補として言えること（★候補であって規則ではない）**:

| 群の種類 | 事前に知っていれば発明を減らせそうなもの | 根拠 |
|---|---|---|
| `MODIFY_EXISTING` 全4群 | **SPEC / TEST / GOAL** | 4群すべてで 1.00 不足 |
| `BUILD_CAPABILITY` | **TEST**（5群中5群で不足） | 0.80〜1.00 |
| `OBSERVE_CURRENT_STATE` | **TEST / GOAL** | 2群とも 1.00 |

**★これを次回 TASK 投入時の「不足情報候補」として使うところまでは、まだ配線していない。**

---

## 6. 新しいものを作っていない

- **新しい ID 体系 0**（`cluster_id` は既存の鍵を連ねた文字列）
- **新しい台帳 0 / 新しい state 0 / 新しい event type 0**（返りはその場の観測・台帳へ書かない）
- **LLM 0回**（`proposed_kind` を正本入力に入れていない）
- 既存の `_best_resume_match`（漢字の重なり率 0.3）も**使っていない**（TASK の goal どうしで明細を見ないため）

---

## 7. 未確認・次

1. **embedding を使っていない** ―― `s_account_axes` の density は科目軸の生成に使われており、
   **TASK 間の類似には接続していない**。使えるかは**未調査**
2. **73 TASK は構造化済みのものだけ** ―― 既存1,387 TASK のうち **5.3%**。
   残りは構造化されていないため群に入らない
3. **`refs` が 0件**（§4.2）。段2 の参照抽出がこの母数で働いていない理由は**未調査**
4. **`REQUEST_KIND_COUNTS` / `REQUEST_GAPS` が 5/73** ―― 段3 以降の投入のみ。
   再計算はできるが**まだしていない**
5. **SPEC recall 0.300 の切り分けは別宿題**（裁定どおり本線へ持ち込んでいない）。
   ★ただし §4.1 で `SPEC` 不足が 5/11 群に出ており、**cluster 品質への影響は今のところ観測されていない**
   （群の鍵に `SPEC` を使っていないため）
