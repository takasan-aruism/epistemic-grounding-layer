# LLMK-0013 依頼文が 自分と 矛盾する ── 事実を 渡しておいて「与えていない」と 禁じる

- knowledge_id: LLMK-0013
- maturity: MEASURED
- 測ったHEAD: egl 562be13 ／ 材料= 3 seed 分の実出力（seed 7 / 23 / 47）
- call_sites: `egl/structure/s2_extract.py:call`
- applies_when: LLM の答えに UNKNOWN・保留・「判断できない」が多いとき／同じ入力で答えが揺れるとき
- 出所: ITEM-2DER-EVO-0020（T2「決定論に寄せられるか」）

<!-- 2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0013
call_sites: egl/structure/s2_extract.py:call
applies_when: schema_enforced=EXISTS worker=VLLM
maturity: MEASURED
-->

## 0. 失敗の型（1行）

★**依頼文が、答えに必要な事実を渡しておきながら、同じ依頼文の中で「その情報は与えられていない」と禁じている。**
LLM は禁止に正しく従い、**答えられる問いに UNKNOWN を返す**。

## 1. 実物（`s2_extract.py`）

前半（AST FACTS として渡している）:

```
"imported_by": [...], "imported_by_count": 12
```

後半（HARD PROHIBITIONS の 5）:

> 5. NEVER judge whether this file is wired into the live path.
>    **You have not been given the information to decide that**, and it is computed elsewhere.

★**渡している。そして「与えていない」と言っている。**

## 2. 実害（分母つき・3 seed 共通の 218 ファイル）

| | 実測 |
|---|---|
| `lifecycle_signal` の 3 seed 一致 | **106/218 = 48.6%** |
| 　2対1に割れた／3つとも違う | 101 ／ 11 |
| LLM(seed 7) が `UNKNOWN` と答えた | **112/218 = 51%** |
| 　うち **実際に import されている** | **27件**（`dev-workcell/dw/workcell.py` は呼び手 **12本**） |

★不一致は**片方向にだけ偏る**（LLM=UNKNOWN／規則=ACTIVE が 37件で最多）。
∴ ★**禁止5の効き方と一致する＝偶然の揺れではない。**

## 3. ★対策（この順で当てる）

1. ★**欄ごとに「その欄を答えるのに要る事実」を書き出す。**
2. ★その事実が **prompt の中で禁じられていないか**を照合する。
   （★禁止条項と FACTS 欄は**別々に書かれるので、書いた本人が気づかない**）
3. 矛盾していたら、**どちらかを消す**。
   - 事実を使わせたいなら → 禁止を、その欄に限って解く。
   - 判断させたくないなら → ★**その欄を LLM から外し、機械が決める。**
4. ★**LLM を疑う前に依頼文を読む。**本件で LLM は 1つも間違えていない。

## 4. この件で採った手（★決定論に寄せた）

`lifecycle_signal` は **import 図から機械が決められる**（5行の規則）。

| | LLM | 決定論の規則 |
|---|---|---|
| 自己一致 | 48.6% | **100%**（作りで保証） |
| その情報を使えるか | ★**禁じられている** | ★持っている |

★LLM が割れた 112件のうち **95件（84.8%）**で、規則は 3 seed のどれかと一致した。

## 5. 測っていないこと

- 禁止5を**その欄に限って解いた場合**の成績 ── ★未測定（回していない）。
- 残り10欄（自由記述）の妥当性 ── ★未測定。
- 規則の**本番配線** ── ★していない（決めるのは Structure と MGR）。

## 6. 関連

- LLMK-0014（schema 在り ≠ 出力が閉じている）── 本件を見つける前段。
- LLMK-0011（長い出力は seed でも再現しない）── 揺れの別要因。本件は**それとは別に**依頼文で説明がつく。
