# LLMK-0011 seed と temperature=0 では 長い出力は 固定できない

<!-- 2DER:LLM_KNOWLEDGE
knowledge_id: LLMK-0011
call_sites: twoder/runtime_supervisor.py:qwen_raw_call
applies_when: seed を 指定して 再現を 期待するとき
maturity: MEASURED
-->

- knowledge_id: LLMK-0011
- maturity: MEASURED
- 測ったHEAD: egl 4fd9c26 ／ 実走 vLLM Qwen3.6-35B-A3B（TP2 / max-num-seqs 32 / prefix-caching 有 / kv-cache fp8）
- call_sites: `egl/experiments/detailizer/run_r1.py`（R1 の生成器）
- applies_when: 同じ設問を繰り返して 一致率・被覆率などを 比べるとき
- 出所: ITEM-2DER-EVO-0037（Topology が発見・Inference Control が切り分け）

## 1. 何が起きたか

同じ設問・`temperature=0`・`seed=0`・`enable_thinking=False` で **5回**打つと、**5回とも違う返り**。
候補数が **3〜34** で振れ、completion_tokens は **520〜2299**。

## 2. サンプリングではない（★対照4条件・各4回）

| 条件 | 違う返りの種類 |
|---|---|
| 既定のまま | **4/4** |
| `top_p=1.0` を明示 | **4/4** |
| `top_p=1.0` + **`top_k=1`（貪欲）** | **4/4** |
| `max_tokens` を 800 に縮める | **4/4** |

★**`top_k=1` は候補を1つに絞る＝サンプリングが消える。それでも揺れる。**
∴ ★**原因は sampling パラメータではない。**「temperature/top_p を渡せば直る」は**成り立たない**。

## 3. 効いているのは「出力の長さ」（★top_k=1 のまま・各4回）

| 出力 | 違う返りの種類 | completion_tokens |
|---|---|---|
| 短い答え（1語） | **1/4（完全一致）** | 2,2,2,2 |
| 中くらい（数行） | **4/4** | 84,58,72,85 |
| 長い答え（JSON列挙） | 3/4 | 28,29,38,38 |

★**短い出力は決定論。長くなると揺れる。**
★出力が伸びるほど、途中の1トークンの差が後段を変える（★見立て・未検証）。
★連続バッチ処理と prefix-caching を持つ推論サーバでは、
**同一プロセスでも他の要求との相乗りで浮動小数の合算順序が変わりうる**（★これは仮説であり、私は確かめていない）。

## 4. 使える形

- ★**「seed を固定したから再現する」と書かない。**★短い出力でだけ成り立つ。
- ★**プロンプトの版を n=2〜22 で比べない。**★揺れを測っているだけになる（Topology の指摘そのまま）。
- ★**版を比べるなら、先に同じ版を複数回引いてノイズ帯を出す**（`COMPARE_RULES` の既定どおり）。
- ★**出力を短くできる設問は、短くするほど再現する。**
  1語で答える分類は 5/5 完全一致（LLMK-0010 と同じ方向）。
- ★**再現が要る工程は、長い自由記述を LLM に出させない設計にする。**
