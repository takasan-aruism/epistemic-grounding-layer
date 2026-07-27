# 実装 → 設計/監査: I-5 段3e が候補ゼロを返す件 — **事実のみ**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=STATUS
- 依頼: `CC_DESIGN_2026-07-27_I5_INSTRUCTION_3E_ZERO_CANDIDATE.md`
- **本文書は事実のみを書きます。判定・評価・提案をしません**（責務の切り分け §0 に従う）。

## 0. ★指定された再現手順を実行した結果
```
実行: python3 -c "import sys;sys.path.insert(0,'/home/takasan');import twoder.submit as S;
      t=S.submit('この設計案の得失は？'); print(t.get('INTENT_STRATEGY'))"
```
**観測結果:**
```
{'strategy': 'BOUNDED_MULTI_VIEW', 'candidates': ['BOUNDED_MULTI_VIEW'],
 'status': 'AUTO_CONFIRMED', 'facts_emitted': False, 'fact_trace': ['SELF_CONTAINED_NO_FACTS'],
 'anchoring': 'MEDIUM'}
boundary_failures: [{'system':'DS','gap':'reconstruct_snapshot failed: HTTP Error 400: Bad Request'}, …]
```
**＝ 依頼書に記載された `status: NO_CANDIDATE` / `candidates: []` は、私の実行では再現しませんでした。**
**私の実行では `AUTO_CONFIRMED` / `['BOUNDED_MULTI_VIEW']` が返っています。**
**この差が何によるかは、私の観測だけでは判定材料が不足しています。**

## 1. 段3e が LLM を呼べているか
**呼べています。**
```
ENDPOINT      : http://127.0.0.1:8005/v1/chat/completions
MODEL         : Qwen3.6-35B-A3B
MAX_TOKENS    : 256
応答           : あり（応答長 83 文字）
finish_reason : stop
応答本文       : { "yes": [ "BOUNDED_MULTI_VIEW" ], "reason": "…" }
```

## 2. 3e に渡っているメニューの中身（実際に生成された prompt から抽出）
```
['DIRECT', 'CONTEXT_RESOLVE', 'CHOICE', 'BOUNDED_MULTI_VIEW', 'INTENT_PROBE', 'PREMISE_PROBE', 'DEFER']
```
**7戦略すべてが載っています。空ではありません。**

## 3. 例外・タイムアウトを握り潰している箇所
`rri/rri/intent_strategy.py`:
| 行 | 内容 |
|---|---|
| **139** | `except Exception:` — `_parse()` 内。JSON 解釈に失敗した場合に `(None, "DIVERGE_SCHEMA")` を返す |
| **152–153** | `except Exception as e:` — `_llm()` 呼出を包む。**`status="LLM_UNAVAILABLE"` と `failure` 文字列を返す**（例外型名を含む）。呼び出し側 `submit.py` が `_fail("RRI", …)` で `boundary_failures` に記録する |

**候補を空にして返す経路はいずれも `status` に理由を残しています。** 沈黙して空を返す経路は、上記2箇所の外には見当たりませんでした。

## 4. `candidates=[]` が生成される分岐（file:line と条件）
`rri/rri/intent_strategy.py`:
| 行 | status | そこへ落ちる条件 |
|---|---|---|
| **153** | `LLM_UNAVAILABLE` | `_llm()` が例外を送出（endpoint 不通・タイムアウト等） |
| **158** | `DIVERGE_LENGTH` / `DIVERGE_SCHEMA` | `finish_reason == "length"`、または応答から JSON を取り出せない／`yes` を読めない |
| **160** | `NO_CANDIDATE` | 解釈は成功したが、`yes` に戦略名が1つも含まれない |

**依頼書に記載された観測は `status: "NO_CANDIDATE"` なので、この表では 160 行の分岐に当たります。**

## 5. 研究スクリプトとの差分（引数・設定）
| 項目 | 本番 3e（`rri/intent_strategy.py`） | 研究（`s_intent_role_split*.py`） |
|---|---|---|
| **MAX_TOKENS** | **256** | **200** |
| MODEL | `Qwen3.6-35B-A3B` | `Qwen3.6-35B-A3B`（同一） |
| ENDPOINT | `http://127.0.0.1:8005/…` | `http://localhost:8005/…`（**表記が違う・宛先は同一ホスト**） |
| temperature | 0.7 | 0.7（同一） |
| **seed** | **`submit()` の `seed`（既定 0）の1回のみ** | **seeds `[0, 1, 2]` の3回**（fixture ごとに平均） |
| **選択役（2段目 LLM）** | **呼ばない**（候補が2件以上なら**先頭を採る**） | **呼ぶ**（候補が2件以上のとき選択役 LLM が1つ選ぶ） |
| 候補の絞り込み | 生成メニュー（7戦略）に含まれるもの | `STRAT_NAMES`（7戦略）に含まれるもの |
| 事実ブロック | **あり**（出し分け条件つき） | **なし** |
| 反膨張の文言 | prompt 本文に同文を含む | prompt 本文に同文を含む |

## 6. 観測の限界（事実として）
- **依頼書の観測（`NO_CANDIDATE`）を私は再現できていません。** 同一コマンドで `AUTO_CONFIRMED` が返りました。
- **`seed` が既定 0 の1回のみである**ため、同一入力でも実行ごとに結果が変わり得ます（本計器の `temperature` は 0.7）。**私の1回の実行と、依頼書の1回の実行が、同じ結果になる保証はありません。**
- **この観測だけでは、`NO_CANDIDATE` がどの条件で生じたかを特定する材料が不足しています。**

---
*IMPL STATUS（I-5）。**事実のみ。** 指定手順を実行した結果は `AUTO_CONFIRMED` / `['BOUNDED_MULTI_VIEW']` で、依頼書記載の `NO_CANDIDATE` は再現しなかった。3e は LLM を呼べており（:8005 / 応答長83 / finish_reason=stop）、メニューは7戦略すべてが載っている。候補を空にする分岐は 153/158/160 行の3つで、いずれも status に理由を残す。研究スクリプトとの差分は MAX_TOKENS(256/200)・seed(1回/3回)・選択役(呼ばない/呼ぶ)・事実ブロック(あり/なし)。判定材料は不足している。*
