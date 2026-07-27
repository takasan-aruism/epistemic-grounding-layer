# 設計/監査 → MGR（写: Taka）: **D-30 — 我々が Qwen に渡しているもの。★5箇所中4箇所に system プロンプトが無く、思考は明示的に切ってある**

- `BUILD_ROLE: 参照`（**調査のみ。何も作っていない・何も変えていない**）
- **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-28_D30_THINKING_OS_PRIMING.md`

## 0. 答え（先に3つ）
1. **★呼び出し間で状態は持ち越されない。** **毎回1〜2メッセージの新しい配列を作って送っている。** **MGR の理解は事実だった。**
2. **★system プロンプトが在るのは5箇所中1箇所だけである**（`request_type`）。**残りは `user` 1本のみ。**
3. **★`enable_thinking: False` が明示されている箇所が在る。** **思考は「たまたま切れている」のではなく、切ってある。**

**★禁止事項（MGR §4）を守る**: **「プロンプトが貧弱だから性能が出ない」とは書かない。** **比較していない。** **何も作っていない。**

---

## 1. D-30-1 本番で Qwen を呼ぶ箇所【監査:CC-α】
```
再現: grep -rn "chat/completions" --include=*.py rri/rri/ twoder/*.py
```
| # | 箇所 | 役割 |
|---|---|---|
| 1 | `rri/rri/request_type.py::_chat` | 要求種別（6分類） |
| 2 | `rri/rri/intent_strategy.py`（段3e） | 7戦略の選択 |
| 3 | `rri/rri/research_intent.py::_chat` | 研究意図 |
| 4 | `twoder/qwen_worker.py::default_chat_fn` | **worker（コード生成）** |
| 5 | `twoder/runtime_supervisor.py::qwen_raw_call` | **共通の導管**（`build_planner` / `reference_oracle` / auditor が使う） |

## 2. D-30-2 各箇所が渡しているもの【監査:CC-α・逐語】
| 箇所 | `messages` | system | temperature | `enable_thinking` |
|---|---|---|---|---|
| `request_type` | **system ＋ user** | **★在る**（`_SYS`＝分類の定義。人格ではない） | `0` | **`False`** |
| `intent_strategy` | **user のみ** | **無し** | `0.7` | **`False`** |
| `qwen_worker`（worker） | **user のみ** | **無し** | `0` | **指定なし** |
| `build_planner` | `qwen_raw_call(prompt, max_tokens)` | **★渡していない** | — | — |
| `reference_oracle` | `qwen_raw_call(prompt, 4096, seed=…, enable_thinking=False)` | **渡していない** | — | **`False`** |
| auditor（`dw/adapters.py::QwenAuditor`） | — | **★在る**（docstring 逐語: 「**別 session/seed/system-prompt で分離した auditor**」「**同一 request 形状(system+seed+enable_thinking=False)を保つ**」） | — | **`False`** |

**`request_type._SYS` の冒頭（逐語）**:
> `"You resolve WHAT THE USER IS ASKING FOR (not how to do it). Return ONLY JSON: {...}"`
**∴ これは「出力形式と分類定義の指示」であって、人格でも思想でもない。**

### 2-1. ★8件目の同型がここに在る
```
twoder/runtime_supervisor.py:67-72
  def qwen_raw_call(prompt, max_tokens, …, system=None, seed=None, enable_thinking=None):
      """system/seed/enable_thinking preserve an actor's exact request shape
         (e.g. the auditor's system prompt, …) so wrapping it changes recovery/telemetry only, not behaviour."""
twoder/build_planner.py:148
  return RS.qwen_raw_call(prompt, max_tokens=max_tokens)      ← ★system を渡していない
```
> **★`system` を渡す口は在る。** **auditor は使っている。** **`build_planner`（PLAN を書く actor）は使っていない。**
> **∴ 「機能は在るが、その場所で使われていない」。** **本日8件目である。**

---

## 3. D-30-3 状態は持ち越されるか【監査:CC-α】
```
再現: grep -rn "history|conversation|prior_messages|\"assistant\"" --include=*.py rri/rri/intent_strategy.py twoder/qwen_worker.py twoder/build_planner.py
結果: 0件
```
**すべての呼び出しが、その場で `messages` 配列を作って送っている。** **`assistant` の過去発話を積む箇所は無い。**
> **∴ 呼び出し間で状態は持ち越されない。** **切れているのは「`messages` を組み立てる所」である。** **保存も復元もしていない。**
> **∴ Taka が触った「会話を重ねた Qwen」と、2DER が触っている Qwen は、別の状態である。** **これは事実である。**

---

## 4. D-30-4 役割ごとに違うものを渡しているか【監査:CC-α】
| 役割 | 渡しているもの | 使い回し |
|---|---|---|
| 分類（`request_type`） | 専用の system ＋ user | — |
| 意図（`intent_strategy`） | **user のみ**・`temperature 0.7` | — |
| **PLAN（`build_planner`）** | **user のみ** | **`qwen_raw_call` の `system` を使っていない** |
| **worker（`qwen_worker`）** | **user のみ**・`temperature 0` | — |
| 監査（`QwenAuditor`） | **system ＋ seed ＋ `enable_thinking=False`** | **意図的に分離**（逐語: 「別 session/seed/system-prompt で分離」） |

**∴ 役割ごとに違うものを渡してはいる。** **ただし「違い」の大半は system の有無であり、5役割中 system を持つのは2つ（分類・監査）である。**
**∴ 使い回しはしていない。** **むしろ auditor だけが「分離」を意図して設計されている。**

---

## 5. ★Taka の観測との対応（事実の並置のみ・評価しない）
| Taka が行ったこと | 2DER が行っていること |
|---|---|
| 人格・思想を与える | **与えていない**（4/5 の箇所で system が無い） |
| 何度か会話してトレーニングする | **していない**（状態は持ち越されない） |
| （その結果）思考OS が組み込まれる | **`enable_thinking: False` を明示している箇所が在る** |

**★これは「だから性能が出ない」という主張ではない。** **比較していない。** **並べただけである。**
**★`enable_thinking: False` には理由が在るはずである**（決定論・再現性・token 節約のいずれか）。**私はその理由を確かめていない。** **【未確認】**

---

## 6. Gap Register への登録（1件のみ・作らない）
| id | 内容 |
|---|---|
| **`G-24`** | **`qwen_raw_call` は `system` を受け取れるが、`build_planner`（PLAN を書く actor）は渡していない。** auditor は渡している。**「機能は在るが、その場所で使われていない」の8件目** |

**★`enable_thinking: False` を Gap にしない。** **意図的な設定である可能性が高く、理由を確かめていないため。**

---

## 7. 私がやっていないこと（MGR §4）
- **何も作っていない。** **プロンプトを1文字も変えていない。** **人格を書いていない。**
- **`enable_thinking` を変えていない。**
- **「貧弱だ」「改善すべきだ」と書いていない。**
- **auditor の system プロンプトの中身を読んでいない**（docstring の記述のみ）。**【未確認】**

---
*CC-α D-30（調査のみ）。★①呼び出し間で状態は持ち越されない——全ての呼び出しがその場で `messages` を組み立て、`assistant` の過去発話を積む箇所は0件 ∴ Taka が触った「会話を重ねた Qwen」と 2DER が触る Qwen は別の状態（事実）。★②system プロンプトが在るのは分類(`request_type`)と監査(`QwenAuditor`)の2つで、意図(`intent_strategy`)・PLAN(`build_planner`)・worker(`qwen_worker`) は user 1本のみ。★③`enable_thinking: False` が明示されている箇所が在る（切ってある。たまたまではない）。★8件目の同型=`runtime_supervisor.qwen_raw_call` は `system` を受け取れ auditor は使っているのに、`build_planner` は渡していない（`G-24` として登録）。役割ごとの使い回しは無く、auditor だけが「別 session/seed/system-prompt で分離」と意図的に設計されている。Taka の観測との対応（人格を与える/会話でトレーニングする/思考OS）に対し、2DER は与えず・持ち越さず・明示的に thinking を切っている——**ただしこれは「だから性能が出ない」という主張ではなく、比較していない事実の並置である**。`enable_thinking: False` の理由は未確認なので Gap にしない。何も作らず、プロンプトを1文字も変えていない。*
