# LLMK-0014 「schema 在り」は「出力が閉じている」ではない ── 形が閉じても 値は 自由

- knowledge_id: LLMK-0014
- maturity: MEASURED
- 測ったHEAD: egl 562be13
- call_sites: `egl/structure/s2_extract.py:call`
- applies_when: `schema_enforced=EXISTS` を根拠に「決定論に寄せられる」「安定している」と言うとき
- 出所: ITEM-2DER-EVO-0020（T2）／★私自身の誤りの訂正

<!-- 2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0014
call_sites: egl/structure/s2_extract.py:call
applies_when: schema_enforced=EXISTS
maturity: MEASURED
-->

## 0. 失敗の型（1行）

★**`schema_enforced=EXISTS` を「出力が閉じている」と読むと、分母を取り違える。**
schema が縛るのは ★**欄の名前と型**であって、★**値ではない**。

## 1. 私が実際にやった取り違え（★逐語で残す）

前の記帳で私はこう書いた：

> ★T2 出力が閉じている（schema 在り）★5件（13%）… ★決定論に寄せられる可能性が在る

★**間違い。**欄まで見ていなかった。

## 2. 実物を欄で数える（`s2_extract.py` の SCHEMA）

| 欄 | 型 | 値は閉じているか |
|---|---|---|
| `lifecycle_signal` | `enum` 5値 | ★**閉じている** |
| `purpose_1line` / `declared_responsibility` | `string` | 自由 |
| `actual_capabilities` ほか 8欄 | 文字列の配列 | 自由 |

★**11欄のうち、値が閉じているのは 1欄だけ（1/11）。**
∴ ★「schema 在り」を根拠に 5件すべてを候補と数えたのは、★**5倍ではなく、欄で見れば 1/11 の話だった。**

## 3. さらに worker で分かれる（★T2 5件の内訳）

| 呼出点 | worker | 決定論に寄せる対象か |
|---|---|---|
| `twoder/question_review.py:ask_one` | CLAUDE_P | ★対象外（判断そのものを頼んでいる） |
| `twoder/senior_review.py:fn` | CLAUDE_P | ★対象外 |
| `twoder/webui.py:consult_view` | CLAUDE_P | ★対象外 |
| `twoder/webui.py:scout_view` | CLAUDE_P | ★対象外 |
| `egl/structure/s2_extract.py:call` | **VLLM** | ★**これだけ測れる** |

★**5件と書いたが、Qwen に効く話は 1件。**

## 4. ★対策

1. ★`schema_enforced` を見たら、★**次に schema の中を開いて欄を数える。**
   数えるのは ★**「enum か / 有限の選択肢か」**の 1点だけ。
2. ★**欄ごとに分母を書く**（「schema 在り 5件」ではなく「値が閉じた欄 1/11・対象の呼出点 1/5」）。
3. ★`worker` を必ず併記する。★**CLAUDE_P と VLLM を同じ表に混ぜない。**
4. ★計器に足すなら `schema_enforced` の隣に ★**「値が閉じた欄の数／全欄数」**を持たせる
   （★いまは持っていない ∴ ★私が毎回 手で開くことになる）。

## 5. 測っていないこと

- 他の呼出点の schema を欄で数えること ── ★未測定（本件は 1件だけ開いた）。
- 計器への欄追加 ── ★していない（★提案のみ）。
- CLAUDE_P 4件を「対象外」と判断したこと自体 ── ★未検証。

## 6. 関連

- LLMK-0013（依頼文が自分と矛盾する）── ★本件で欄を開いたから見つかった。
- 「数には鍵を添える」── 食い違いはほぼ常に鍵の違い。本件の鍵は ★**件数か欄数か**。
