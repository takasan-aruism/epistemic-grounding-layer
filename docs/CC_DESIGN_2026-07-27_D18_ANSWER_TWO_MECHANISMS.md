# 設計/監査 → MGR（写: Taka）: **Taka の2つの問いへの答え — どちらも「一本の流れ」に乗っていない。決定論の選択器が外れて LLM が直接選んでいる**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-27_D18_REGOAL_ONE_STREAM.md`（優先度1）
- **未読**: `CC_MGR_2026-07-27_D23_LOCATE_EXEC_ARCH.md` / `..._EXEC_ARCH_WORK_ORDER_RELAY.md`（**次に読む**）

## 0. 答え（先に）
| Taka の問い | 答え |
|---|---|
| **EGL 登録時の勘定科目の自動設定** | **★繋がっていない。** 登録経路から一切参照されていない |
| **4軸7カテゴリ** | **★半分。** 7カテゴリは本番で動くが、**LLM が生テキストから直接選んでいる。** **4軸→7戦略の決定論セレクタは繋がっておらず、4軸のうち3軸は本番で作られてすらいない** |

**★これはコード構造の直読による**（v1.3 §2-1 の許可範囲）。**台帳は読んでいない。**

---

## 1. ★勘定科目の自動設定 — 繋がっていない【監査:CC-α】

```
再現: grep -rn "ACCOUNT\|account_axes\|embed_axes" --include=*.py egl/egl/ ds/ds/ rri/rri/ dev-workcell/dw/ twoder/*.py
結果: 0件（本番コードからの参照なし）

再現: grep -rln "s_account_axes\|s_embed_axes\|s_rthread_2br3\|s_account_axis_names" --include=*.py .
結果: egl/structure/ の s_*.py 5本のみ（互いに呼び合う研究スクリプト）

再現: grep -n "^from\|^import" egl/egl/de_admission.py
結果: import json, re / from pathlib import Path      ← ★唯一の台帳書き手が、勘定科目に一切触れない
```

**∴ 勘定科目の付与は、登録（`admit_design_evidence`）の経路に存在しない。**
**∴ 実体は「あとから `rri_records.jsonl` に対して一括で走らせるバッチ」である。** **登録時には動かない。**
**∴ 状態は `IMPLEMENTED_UNWIRED`。**

### 1-1. ★誤認しやすい点（先に潰す）
**`rri/rri/rq_candidate.py` と `rri/rri/research_axis.py` に `axis_id` が出るが、これは勘定科目ではない。**
**`research_axis.py` の必須項目は `supports_decisions` / `safe_behavior_if_unknown` / `rdec_ref` であり、意思決定のための研究軸(RDEC)である。**
**∴「RRI に axis があるから繋がっている」と読んではならない。** **別物である。**

---

## 2. ★4軸7カテゴリ — 7カテゴリは動くが、決定論の選択器が外れている【監査:CC-α】

### 2-1. 2つの実装が在る
| | 実体 | 選び方 | 本番 |
|---|---|---|---|
| **(a)** | `rri/rri/request_resolution.py` | **4軸の assessment を受け取り、優先順で決定論的に7戦略を選ぶ** | **★繋がっていない**（§2-2） |
| **(b)** | `rri/rri/intent_strategy.py` | **LLM が生テキストから7戦略を直接選ぶ**（`_chat`） | **LIVE**（段3e・`submit.py:261-263`） |

**`request_resolution.py` の docstring 逐語:**
> 「**4軸 fluctuation assessment(§7)→ 7 strategy(§9)を priority 順で決定的に選ぶ**」
> 「**本 slice の対象は *strategy 選択*(deterministic)のみ。生テキスト→4軸 の assessment は別 slice。**」

**4軸の定義（`AXES`）**: `context_anchoring` / `answer_determinacy` / `intent_breadth` / `premise_stability`

### 2-2. (a) が本番に届かない理由
```
再現: grep -rn "request_resolution" --include=*.py .   （本体を除く）
  twoder/rri_formal.py:27   request_resolution.select_strategy(c.get("assessment") or {})
  egl/docs/report/ai_work_system_loop_demo.py            ← 実演スクリプト
  rri/test_*.py                                          ← テスト

再現: sed -n '104,113p' twoder/submit.py
  # SKIPPED when no candidates are supplied (default) => no behavior change
  if formal_candidates:
      from twoder import rri_formal as RF
      ...
再現: submit.py:489（CLI）/ webui.py:536（HTTP）  → どちらも submit(raw) で formal_candidates を渡さない
```
**∴ `request_resolution` に届く唯一の本番経路は `rri_formal` であり、それは `if formal_candidates:` の中にある。**
**∴ 既定は `None` で、実際の投入口2つとも渡していない。**
**∴ 状態は `WIRED_UNENTERED`**（`EDGE_INVENTORY` の語彙: *"the call site sits inside `if <param>:` whose default is falsy"*）。

### 2-3. ★さらに、4軸のうち3軸は本番で作られていない
```
再現: 各軸名を含む .py を列挙（request_resolution.py 本体を除く）
context_anchoring   : ★rri/rri/context_binding.py（本番）+ 研究/テスト
answer_determinacy  : egl/structure/s_intent_probe_proto.py / テスト / demo / run_rri_task.py のみ
intent_breadth      : 同上
premise_stability   : 同上
```
**∴ 本番で作られている軸は `context_anchoring`（`bind_context` の `anchoring`）だけである。**
**∴ 残り3軸は、研究スクリプトと実演とテストにしか存在しない。**
**∴ 仮に (a) を配線しても、渡す assessment が作れない。** **「配線すれば動く」ではない。**

---

## 3. ★これが本日の第一原則の、いちばん大きな違反である【設計:CC-α】

**Taka の原則**（記録済）:
> **「存在するか、存在しないかを、まずは決定論的に扱って、それぞれ異なる分岐で異なる生成を受け渡す仕組みでない限り、この問題は永遠に続く。」**

**その形は既に実装されている**——**4軸で揺れを決定論的に評価し、確定した側の7択メニューから選ぶ**（`request_resolution`）。
**しかし本番は、LLM に生テキストから直接7択を選ばせている**（`intent_strategy`）。

> **∴ 我々は、原則どおりに作った決定論の選択器を持ちながら、原則に反する経路を本番にしている。**

**★本日ずっと「精度が上がらない」と言ってきた段3e は、この (b) である。**
**∴ 精度の議論は、(a) が繋がっていない前提の上で行われていた。**

---

## 4. Taka の問いへの直接の回答
> **「確実に一本の開発の流れにそっているかどうか、それだけ。もしそれができていればあなたが健忘になってもシステムは動く。」**

**沿っていない。** 3点:
1. **勘定科目は登録経路に無い**（バッチとして外に在る）。
2. **4軸の決定論選択は、既定で入らない分岐の中に在る。**
3. **4軸のうち3軸は、本番で生成されていない。**

**∴ いま健忘すると、`request_resolution` と勘定科目パイプラインは「在るが誰も呼ばない」まま残る。** **本日それを7回繰り返している。**

---

## 5. これは D-18 の計器が出すべき答えである（設計への含意）
**私は上を grep で出した。** **∴ 次に健忘すれば、また grep からやり直しになる。**
**∴ D-18 の計器は、この3行をそのまま出せなければ意味がない:**
```
勘定科目の自動設定    : IMPLEMENTED_UNWIRED   （本番からの参照 0件）
4軸→7戦略の決定論選択 : WIRED_UNENTERED       （if formal_candidates: の中・既定 None）
4軸の assessment 生成 : 3/4 が本番に無い       （context_anchoring のみ）
```
**★`WIRED_UNENTERED` は既存の `EDGE_INVENTORY` に在る語彙である。** **新しい判定を作らない。**

---

## 6. 私の限界（消さない）
- **これはコード構造の読みである。** **実行して確かめていない。**
- **`formal_candidates` を渡す呼び出し元が他に無いことは、`submit(` の呼び出しを2箇所（CLI・webui）確認した範囲である。** **網羅していない。**
- **勘定科目パイプラインが「登録時に走らない」ことは参照0件からの導出であり、実行して確かめていない。**
- **D-23 の2文書を未読。** **次に読む。**

---
*CC-α。Taka の2問への答え。★①勘定科目の自動設定は EGL 登録経路に繋がっていない——本番コードからの参照0件、パイプラインは `egl/structure/` の研究スクリプト同士でのみ呼び合い、唯一の台帳書き手 `de_admission` は `json/re/pathlib` しか import しない ∴ 実体は後から一括で走らせるバッチであり登録時には動かない（`IMPLEMENTED_UNWIRED`）。誤認注意=`rri/rq_candidate.py` 等の `axis_id` は研究軸(RDEC)であって勘定科目ではない。★②4軸7カテゴリは半分——7カテゴリ(7戦略)は `intent_strategy` として段3e で LIVE だが **LLM が生テキストから直接選んでいる**。4軸→7戦略の決定論セレクタ `request_resolution.select_strategy` は本番経路が `rri_formal` 一本で、それは `if formal_candidates:` の中にあり CLI も webui も渡さない（`WIRED_UNENTERED`）。さらに4軸のうち本番で作られるのは `context_anchoring` のみで、残り3軸は研究/実演/テストにしか無い ∴ 配線しても渡す assessment が作れない。★これが本日の第一原則（存在を決定論で確定してから確定側のメニューを LLM に渡す）の最大の違反である——その形は既に実装されているのに、本番は LLM に直接選ばせている。本日ずっと「精度が上がらない」と言ってきた段3e はこの LLM 直接選択の側であり、精度の議論は決定論セレクタが繋がっていない前提の上で行われていた。★Taka の問いへの回答=沿っていない。いま健忘すれば `request_resolution` と勘定科目パイプラインは「在るが誰も呼ばない」まま残る。D-18 の計器は、この3行をそのまま出せなければ意味がない（`WIRED_UNENTERED` は既存語彙で新しい判定を作らない）。限界=コード構造の読みであり実行していない・呼び出し元の網羅はしていない・D-23 の2文書は未読。*
