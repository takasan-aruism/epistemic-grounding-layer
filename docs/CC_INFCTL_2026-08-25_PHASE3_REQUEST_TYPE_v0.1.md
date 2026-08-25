<!--
2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0004
call_sites: rri/rri/request_type.py:_chat
maturity: MEASURED
-->

# Phase 3(代表 call の実測) ── 揺れは下流に写像してから数える v0.1

2026-08-25 ／ instance=Inference Control ／ 仕様 §13 Phase 3

## 0. なぜこの call を選んだか（台帳の欄から決定論で）

代表＝ `rri/rri/request_type.py:classify_request_type`（一次関数 `_chat`）。

- `class=MAINLINE` / `answer_used=EXISTS` / `system_prompt=EXISTS` / 出力語彙が**閉じている**（6語）
- **下流が分岐に使う**（`twoder/submit.py`）＝ 誤ると行き先が変わる
- **RRI が測っていない**（RRI が測ったのは `intent_strategy` / `resolve_consensus`）

## 1. ★既存の acceptance は誤分類を検出できない

`twoder/regression/test_submit_e2e_live.py:45` の逐語は
「返った `request_type` が `REQUEST_TYPES` に入っているか」だけ。
**6語のどれでも通る** ∴ **DE-0156（観測要求を能力構築へ誤送）を再発しても緑のまま**。
この call は DE-0156 のために作られたのに、その事故を捕まえる門が無い。

## 2. 実測

### ① prompt が明文で書いている規則どおりに答えるか

正解は勝手に作らず、`_SYS` が **明文で書いている CHOOSE 規則**を正解にした（11件 × seed 0/1/2）。

**33/33 = 100%**、3seed 安定 **11/11**、同一入力反復（n=8）**8/8 同一**、日英の言い換え **3/3 一致**。

### ② 実物の依頼文（front door の `goal_head`・母集団 505本から先頭20本 × seed 0/1/2）

**3seed 安定 18/20 = 90%**。多数決の分布は BUILD 8 / MODIFY 9 / OBSERVE 3。

揺れた2件は **どちらも語の境界**（乱数ではない）:

| # | 入力（頭） | 出力 | 境界 |
|---|---|---|---|
| 11 | 設計/監査から MGR へ: FALSE_NEGATIVE_RATE_V3 を置いた… | MODIFY / MODIFY / **OBSERVE** | 報告か 変更か |
| 16 | `latest_test_result.py` に `relay_probe` という純関数を… | MODIFY / **BUILD** / MODIFY | 既存に足すか 新しく作るか |

## 3. ★下流は 4挙動しか持たない

`request_type` の語で分岐している箇所を AST で全件数えた（非テスト・5レポ）。

| 語 | 分岐に出る回数 | 場所 |
|---|---|---|
| OBSERVE_CURRENT_STATE | 2 | `submit.py:573, 1026` |
| RESUME_PRIOR | 2 | `submit.py:1099, 1217` |
| BUILD_CAPABILITY | 1 | `submit.py:1107` |
| MODIFY_EXISTING | 1 | `submit.py:1107`（**BUILD と同じ枝**） |
| DECIDE | **0** | ★どこにも出てこない |
| OTHER | **0** | ★どこにも出てこない |

∴ **6語 → 下流は 4挙動**（OBSERVE / RESUME / BUILD＝MODIFY / それ以外）。

### ★揺れを下流に写像すると 10% → 5%

- #16 の MODIFY↔BUILD は **同じ枝** ∴ **行き先は変わらない**。
- #11 の MODIFY↔OBSERVE は **枝が変わる**。

**∴ 見かけの不安定 2/20 = 10%、行き先が変わる不安定 1/20 = 5%。**

## 4. 対照との差は runtime ではなく prompt 設計

同じサーバ・同じ `temperature=0`・同じ seed 指定で:

| | `request_type:_chat` | `intent_strategy:_llm`（LLMK-0001） |
|---|---|---|
| system prompt | **EXISTS**（規則を明文で書く） | **ABSENT** |
| 出力語彙 | **閉じた6語**（prompt に列挙） | 7戦略から複数選択 + 自由文 `reason` |
| schema の明示 | JSON の形を prompt に書く | 形は書くが `reason` は自由 |
| 実物での安定 | **90%**（下流写像後 95%） | byte 7〜8/8 が相違・決定も3種 |

∴ **runtime を触っても差は説明できない**。差は **prompt 設計**に在る。

## 5. 再利用できる形（条件 → 操作 → 結果）

1. **条件**: LLM 出力が下流の分岐に使われている。
   **操作**: 揺れを **下流の挙動へ写像してから**数える。
   **結果**: 実測 10% → 5%。写像前の数字で対策を決めると、効かない所を直す。
2. **条件**: acceptance が「返った語が集合に入っているか」だけ。
   **操作**: その門で **既知の事故を再現**してみる。
   **結果**: 通ってしまうなら **その門は誤分類を検出できない**（実測: DE-0156 の型が緑のまま）。
3. **条件**: 分類の語彙を設計する。
   **操作**: **下流が実際に分岐に使う語**を数える。
   **結果**: 実測 6語のうち **2語（DECIDE / OTHER）は一度も分岐に出てこない**。

## 6. まだ測っていないこと

- 実物の標本は **`goal_head`（120字で切れている切片）**であり、全文ではない。
- 標本は **先頭20本**（母集団 505本）。無作為抽出ではない。
- Claude（`claude -p`）との比較は **していない**。
- `requires_current_state` / `references_prior_work` / `basis` の安定性は測っていない（`request_type` だけ）。
- #11 #16 の **正解**は決めていない（どちらの読みも成り立つ ∴ 語彙の問題として残す）。
