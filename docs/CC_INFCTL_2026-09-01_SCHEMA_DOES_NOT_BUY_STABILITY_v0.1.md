# LLMK-0016 schema を足しても 安定しない ── 縛る先が 違う

- knowledge_id: LLMK-0016
- maturity: MEASURED
- 測ったHEAD: egl df10950 ／ 実走 vLLM Qwen3.6-35B-A3B（96回・並列8）
- call_sites: `egl/structure/s_intent_probe_proto.py:_llm`
- applies_when: 出力が揺れるので `response_format` / `guided_json` で縛ろうとするとき
- 出所: ITEM-2DER-EVO-0020（T4 21件の個別評価）

<!-- 2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0016
call_sites: egl/structure/s_intent_probe_proto.py:_llm
applies_when: 出力が揺れる schema response_format
maturity: MEASURED
-->

## 0. 失敗の型（1行）

★**「値が閉じているのに schema で縛っていない」を見つけて縛っても、揺れは減らない。**
★schema が保証するのは ★**値が集合の外に出ないこと**だけで、★**どの値を選ぶかは縛らない**。

## 1. 対照実験（2×2・設問8本 × seed 3 × 腕4 = 96回）

| 腕 | OK | ★enum の外に出た | ★3 seed 一致 |
|---|---|---|---|
| schema 無 temp=0.7（★その面の既定） | 24/24 | **0/24** | **2/8** |
| ★schema 有 temp=0.7 | 24/24 | **0/24** | **2/8** |
| schema 無 temp=0.0 | 24/24 | **0/24** | 3/8 |
| ★schema 有 temp=0.0 | 24/24 | **0/24** | 3/8 |

★**enum の外には、そもそも 1回も出ていなかった**（★prompt が既にメニュー形式で語を並べているから）。
∴ ★**schema が直す物が 最初から 壊れていなかった。**
★temp 0.7→0.0 は 2/8→3/8 ＝ **設問1本の差**。★n=8 ∴ ★**差と呼ばない。**

★設問も判定も**向こうの module から借りた**（`FIXTURES` / `parse_output`）＝★私は作っていない。

## 2. ★どこが揺れているか（軸ごと・temp 0・seed 3）

| 軸 | 3 seed 一致 | 割れた時の値 |
|---|---|---|
| `context_anchoring` | **5/8** | LOW/**UNRESOLVED**、HIGH/LOW |
| `answer_determinacy` | 7/8 | DETERMINATE/**UNRESOLVED** |
| `intent_breadth` | 6/8 | MULTI_AXIS/UNDERCONSTRAINED |
| `premise_stability` | 6/8 | STABLE/UNCERTAIN、STABLE/SUSPECT/**UNRESOLVED** |
| `strategy` | 6/8 | BOUNDED_MULTI_VIEW/DIRECT |

★軸ごとは 5〜7/8 なのに ★**全軸そろっての一致は 3/8**
── ★**軸が独立に揺れると、掛け算で落ちる。**★軸を増やすほど「全部そろう」は下がる。

## 3. ★対策（縛る先を変える）

1. ★**schema は「集合の外に出ない」保険。★安定の道具ではない。**
   ★付けてよい（害は無い）。★ただし ★**付けたことを「安定させた」と書かない。**
2. ★**揺れを直すなら 設問の側**。既に測ってある手が3つ在る：
   - LLMK-0003 ★語彙が上限（9語→4語に畳むと 一致 57%→75%・★LLM 呼び出し 0回）
   - LLMK-0005 ★閉じた6語から**1つ**選ぶ設問は 3seed 安定 90%
   - 「★字数の縛りが LLM を発散させる」── 数の縛りを外す
3. ★**候補（★未検証）= `UNRESOLVED` を同じ列挙に混ぜない。**
   ★割れ 10件のうち **4件**が `X/UNRESOLVED` の形。
   ★`UNRESOLVED` は**答えではなく「答えられない」**＝ ★決める／決めないの迷いを、値の列に混ぜている。
   ★分けるなら「値」と「決められたか」を**別の欄**にする。
   ★★n が小さい（割れ 10件）∴ ★**これは候補であって結論ではない。**
4. ★**軸ごとの一致率を先に出す。**★総合の一致率だけ見ると、どの軸が原因か消える。

## 4. 測っていないこと

- `UNRESOLVED` を外した腕 ── ★**回していない**（★その面の意味を変える判断は私の領分外）。
- 語彙を畳んだ腕 ── ★未測定。
- 他の3件（`ds/ds/phase1.py` / `egl/autonomy/investigate.py` / `egl/egl/judge_vllm.py`）── ★未測定。
- 設問 n=8 は小さい。★母集団を増やす手番は立てていない。

## 5. 関連

- LLMK-0014（schema 在り ≠ 出力が閉じている）── ★**逆向きの対**。0014 は「縛っていないのを見落とすな」、
  本件は「★縛っても安定はしない」。★両方を持って初めて `schema_enforced` を正しく読める。
- LLMK-0003 / 0005 ── ★安定は**語彙と設問**で決まる。
- LLMK-0011（長い出力は seed でも再現しない）── 出力を短く保つのは別の手。
