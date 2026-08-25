<!--
2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0002
applies_when: prompt_source=PARAM
maturity: MEASURED
-->

# Phase 2(分類) ── 用途は呼出点に無い v0.1

2026-08-25 ／ instance=Inference Control ／ 仕様 §13 Phase 2。**分類語彙は実物を調べる前に固定しない**（逐語）に従い、
38 呼出点の docstring と prompt literal を先に集めてから決めた。

## 1. 既存語彙は使えるか(★先に調べた)

**「LLM 呼出の用途」を表す閉じた語彙は 2DER に無い。**
探した範囲＝ ds / rri / egl / dev-workcell / twoder の `*.py` で module 直下に定義された
tuple・set・dict の全件、および個別に読んだ次の6本:

| 既存語彙 | 場所 | 何を表すか | 用途分類に使えるか |
|---|---|---|---|
| `STAGES`(8語) | progress_seal.py:19 | 進捗の段 | 使えない(段であって用途でない) |
| `PHASE_MENU`(6語) | annotate_gate.py:40 | 2DER の作業相 | 使えない(同上) |
| `ROLE_OUTPUT_SCHEMA`(9役) | role_schema.py:17 | 並行運用の役 | 使えない(誰であって何でない) |
| `WORK_KINDS`(2語) | handoff_contract.py:26 | IMPLEMENT / INVESTIGATE | 粗すぎる |
| `BASIS_KINDS` | answer_evidence.py:12 | 証拠の出所 | 別軸 |
| `VERDICTS` / `_LADDER` | handoff_contract:44 / egl_integration:17 | 在否 / 成熟度 | 別軸(v0.3-v0.4 で既に使用) |

∴ 分類は実物から導いた。**ただし新しい語を台帳へは入れていない**（下記のとおり、入れる必要が無くなった）。

## 2. ★測って分かったこと: 用途を持つ呼出点は 0/38

呼出点ごとに、決定論で2つ測った（v0.5 で台帳の欄になった）。

- `prompt_source` = user メッセージ本文の出所。**PARAM = 呼び手が渡す**
- `answer_used` = 返答の本文を読むか。**ABSENT = 到達性/待ち時間の測定であって推論ではない**

| 区分 | 件数 | 根拠 |
|---|---|---|
| **ADAPTER**(prompt/messages ごと呼び手から来る) | **28** | `prompt_source` = PARAM 27 / PARAM_MIXED 1 |
| **PROBE**(返答の本文を読まない) | **7** | `answer_used` = ABSENT |
| **PROBE**(本文は読むが `"reply OK"` / `"Reply with exactly: hello world"`・max_tokens 8〜20) | **3** | `prompt_source` = LITERAL |
| **用途を持つ呼出点** | **0** | ― |
| 合計 | **38** | 保存則 28+7+3 = 38 |

## 2b. ★上の表を訂正する（同日・自分の実測の誤り）

上の 28/7/3/0 は **誤り**。原因は2つとも私の計器側:

1. **CLAUDE_P の `prompt_source` を PARAM と決め打ちしていた。**
   実際は 4件とも関数内で prompt を組んでいた（`webui.py` の2件は本文に直書き、
   `senior_review` / `question_review` は `cmd[2] = build_prompt(...)`）。
   決め打ちを外して argv の穴を辿るようにした。
2. **`PARAM_MIXED` が2つの意味を混ぜていた** ――
   「引数から組んだ（＝渡すだけ）」と「この場で指示文を書いた（＝用途を持つ）」。

∴ **閾値を持たない measure に置き換えた**: `prompt_literal_chars`
＝ **この呼出点に書かれている指示文の字数**（dict の鍵は数えない・局所代入を1段たどる）。

| 指示文の字数 | 件数 | 中身 |
|---|---|---|
| **0字** | **32** | 渡すだけ、または指示文が**別の関数**に在る（例 `senior_review` は `build_prompt` 側） |
| 8〜31字 | **3** | `"reply OK"` / `"Reply with exactly: hello world"` = **PROBE** |
| **164〜347字** | **3** | `webui:scout_view` 347 / `webui:consult_view` 167 / `autonomy/ingest:_worker_infer_objective` 164 |

**∴ 訂正後の結論**: 用途を持つ呼出点は **0 ではなく 3件**。
ただし **32/38 は依然として「渡すだけ」** であり、**用途は1段上（呼び手）に在る**という主旨は変わらない。
★「0件」と書いた最初の版を消さずに残す（[[絶対に0件を根拠にしない]]の実例として）。

## 3. Phase 2 の単位 = 呼び手 77件

一次関数の呼び手を **解決して**数えた（名前一致では数えない）。

- 解決済みの呼び手 = **77件**
- 呼び手 0 の一次関数 = **2件**（`twoder/qwen_worker.py:default_chat_fn` / `twoder/senior_review.py:fn`）
  ★どちらも **注入で使われる**（`chat_fn` 既定値 / `make_actor` が返す callable）
  ∴ **静的な呼び手数 0 を「使われていない」と読んではいけない**。
- レポを跨ぐ呼び手が1件在る: `rri/rri/intent_strategy.py:_llm` ← `twoder/menu_vote.py`

### ★測定の失敗も残す

最初の計数は **名前一致**で数え、`get` が **5474件**（`dict.get`）、`chat` / `fn` / `post` も全レポで衝突した。
import と定義を解決して数え直して 77件。**名前で数えた数を分母にしてはいけない。**

## 4. v0.1 の既知限界が実測になった

`CC_AUDIT_2026-07-24_LLM_INVOCATION_MAP_CONSISTENT.md` は
「`:8005` health(/v1/models)チェックも CALL_SITE に入る（TEST クラスは v0.2）」を**申告**していた。
本測定で **10件（PROBE 7 + LITERAL 3）** と**数が付いた**。宣言 → 実測へ上がった。

## 5. まだ測っていないこと

- 77件の呼び手を **用途別に分類していない**（本 doc は単位を確定させただけ）。
- `prompt_source=UNRESOLVED` が **7件** 残る（payload dict を辿れない形）。0件と書かない。
- 呼び手の**実行回数**は測っていない（静的な呼び手数であって走行数ではない）。
