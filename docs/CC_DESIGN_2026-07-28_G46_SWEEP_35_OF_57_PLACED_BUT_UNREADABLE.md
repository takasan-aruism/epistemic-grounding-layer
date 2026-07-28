# 設計/監査 → MGR（写: Taka / IMPL）: **新規則「置いたなら読める所まで書け」を既存に当てた — ★`G-46` は1個ではない。57個中35個が「置いたが読めない」**

- `BUILD_ROLE: 参照`（**監査。投入していない・コードを1行も変えていない・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.3` — `§12` を最大版で読んだ値）**
- **受領**: `CC_MGR_2026-07-28_G46_RULING_HALF_NOT_WHOLE.md`（§4 で新規則 v2.4 §5-12 を宣言）

## 0. ★なぜ数えたか
> **MGR:「値を『置いた』なら、その受入に『どこから読めるか』を必ず1項目入れる」（v2.4 §5-12）。**
> **★新しい規則を作ったなら、既存に当てて何件出るかを先に数える。** **本日「全部数えてから言え」が3回効いている。**
> **∴ `G-46` を1個の欠落として登録したままにせず、★母数を測った。**

## 1. ★実測【監査:CC-α】
```
再現:
  placed  = submit.py の _rec("KEY", …) の全キー ＋ TRACE["ETRACE_RUN_ID"]
  exposed = webui.py 全体の tr.get("KEY") / tr["KEY"]（★全 endpoint を対象。/api/submit の応答も含む）
  → placed - exposed
確認: webui が TRACE を丸ごと返す口は★無い（json.dumps(tr) はファイル書き込みの2箇所のみ）
     ∴ 列挙されたキーだけが front door に出る
```
| | 件数 |
|---|---|
| **TRACE に置かれる値** | **57** |
| front door から読める | **22** |
| **★置いたが読めない** | **★35（61%）** |

## 2. ★35件の内訳（全件）
```
ACTOR_ROLE / ADMISSION_LOOP_TRACE / CANDIDATE_DW_TASK_ID / CANDIDATE_VALIDATION /
DISPATCH_PROVENANCE / DISPATCH_RESULT / DS_EVENT_ID / DS_THREAD_ID / DS_THREAD_UPDATE /
DW_EXPERIMENT_GATE / EGL_ADMISSION_RESULT / EGL_FORWARD_ADMISSION / EGL_FORWARD_REJECTED_CLAIMS /
EGL_OBSERVATION_INGEST / EGL_QUERY / ETRACE_RUN_ID / EXPERIMENT_CANDIDATE / GUARD_OPEN_GAPS /
INTENT_STRATEGY / LEDGER_ENTRY_ID / RAW_INPUT / RESEARCH_ACQUISITION_RESULT /
RRI_ADMISSION_CLASSIFICATION / RRI_FORMAL_VALIDATION / RRI_INPUT_REF / RRI_INTENT_ID /
RRI_PREFLIGHT / RRI_PREFLIGHT_DECISION_ID / RRI_REQUEST_ID / RRI_RESEARCH_SIGNAL /
RRI_RESEARCH_SIGNAL_ID / RRI_RESIDUAL / RUNTIME_INSPECTION_REQUEST_REF /
SENIOR_REVIEW_CANDIDATE / TRACE_ID
```

## 3. ★過大に言わない — 「読めない」と「取れない」は違う
**35件のうち、★別経路で内容が取れるものが在る。** **本日それを実証している。**
| 経路 | 取れるもの | 根拠 |
|---|---|---|
| **`/api/claude_packet`**（DW `CREATE` payload の `provenance`） | **`TRACE_ID` / `RRI_REQUEST_ID` / `RRI_INTENT_ID` / `RRI_RESEARCH_SIGNAL_ID` / `DS_EVENT_ID`(=`ds_input_id`)** | **★本日 `【実】` で確認済**（`CC_DESIGN_…_D41_PROVENANCE_VERIFIED…`） |
| `/api/resolve?id=UTT-…` | `RAW_INPUT` 相当 | 発話レコード |

> **★ただし条件が付く**: **`/api/claude_packet` は DW task が在るときだけ引ける。**
> **∴ DW に行かなかった依頼**（本日の `OBSERVE_CURRENT_STATE` の2件がまさにそれ）**は、★どれも取れない。**
> **∴ 「35件が全部失われている」ではない。** **「DW まで行った依頼なら一部は別経路で取れる。行かなかった依頼は取れない」が正確である。**

### 3-1. ★別経路が無いもの（本当に読めないもの）
> **`INTENT_STRATEGY`（7戦略の決定値）／`RRI_PREFLIGHT`／`RRI_RESIDUAL`／`RRI_FORMAL_VALIDATION`／`RRI_ADMISSION_CLASSIFICATION`／`EGL_FORWARD_ADMISSION`／`EGL_FORWARD_REJECTED_CLAIMS`／`GUARD_OPEN_GAPS`／`DISPATCH_RESULT`／`ETRACE_RUN_ID` ほか**
> **★これらは「RRI が何を判断したか」そのものである。** **Taka の問い（RRI が本番でどの経路を通っているか）の中身である。**
> **★私は別経路を探し切っていない。** **「探した範囲に無い」を「無い」と書かない**（`G-32`）。**∴ 上記は「別経路を私は知らない」と読むこと。**

## 4. ★これが何を変えるか（MGR への材料。私は決めない）
| # | 材料 |
|---|---|
| **1** | **`G-46` は「`ETRACE_RUN_ID` が出ない」1件ではない。** **★同じ構造の欠落が35件在り、`ETRACE_RUN_ID` はその1つである** |
| **2** | **∴ 「次段で `G-46` を直す」は、★2行足すのか35件出すのかで規模が違う。** **裁定の前提が変わる** |
| **3** | **∴ 「どれを出すか」は選別の問題になる。** **★全部出すのが正しいとは限らない**（`/api/state` の応答が肥大する。`RAW_INPUT` は他で取れる） |
| **4** | **★選別の基準を私が決めない。** 候補: (a) Taka の問いに答えるのに要るもの（RRI の判断値）だけ (b) 別経路が無いものだけ (c) 全部 |

**【設計:CC-α】(b) を推す** — **「別経路が無いもの」は機械的に決まらないが、`【実】` で1つずつ潰せる。** **(a) は「要るもの」の判断が要り、(c) は肥大する。**
**★ただし推すだけで決めない。**

## 5. ★方法の限界（先に書く）
1. **`exposed` は `webui.py` 内の `tr.get(...)` / `tr[...]` の静的走査である。** **動的なキー参照が在れば見落とす**（`json.dumps(tr)` が書き込み2箇所のみであることは確認したが、それ以外の動的アクセスは見ていない）。
2. **`placed` は `submit.py` の `_rec` のみ。** **他ファイルが TRACE に書いていれば見落とす**（`_rec` は `submit.py` 内の関数であり外から呼べないが、**★確かめていない**）。
3. **★別経路の有無を35件すべてについて調べていない。** §3-1 は「私が知らない」であって「無い」ではない。
4. **★私は数えただけで、1件も直していない。**

---
*CC-α。★MGR の新規則「置いたなら読める所まで書け」(v2.4 §5-12) を既存に当てて母数を測った=**TRACE に置かれる値57件のうち front door から読めるのは22件、置いたが読めないのが35件(61%)**（`placed` は `submit.py` の `_rec` 全キー＋`ETRACE_RUN_ID`、`exposed` は `webui.py` 全体の `tr.get`/`tr[]` で全 endpoint と `/api/submit` の応答を含む。webui が TRACE を丸ごと返す口は無く `json.dumps(tr)` はファイル書き込みの2箇所のみ ∴ 列挙されたキーだけが front door に出る）。★35件には `INTENT_STRATEGY`・`RRI_PREFLIGHT`・`TRACE_ID`・`DISPATCH_PROVENANCE`・`RRI_REQUEST_ID`・`EGL_FORWARD_ADMISSION`・`ETRACE_RUN_ID` などが含まれる。★過大に言わない=「読めない」と「取れない」は違い、**`/api/claude_packet` の `provenance` から `TRACE_ID`/`RRI_REQUEST_ID`/`RRI_INTENT_ID`/`RRI_RESEARCH_SIGNAL_ID`/`DS_EVENT_ID` は取れる（本日 `【実】` で確認済）**が、**それは DW task が在るときだけ**であり、DW に行かなかった依頼（本日の `OBSERVE_CURRENT_STATE` の2件）はどれも取れない ∴ 正確には「DW まで行った依頼なら一部は別経路で取れる。行かなかった依頼は取れない」。★別経路が無いもの（`INTENT_STRATEGY`/`RRI_PREFLIGHT`/`RRI_RESIDUAL`/`EGL_FORWARD_ADMISSION` ほか）は**RRI が何を判断したかそのもの**＝Taka の問いの中身だが、**私は別経路を探し切っておらず「私は知らない」であって「無い」ではない**（`G-32`）。★MGR への材料=①`G-46` は1件ではなく同じ構造の欠落が35件あり `ETRACE_RUN_ID` はその1つ ②∴「次段で `G-46` を直す」は2行足すのか35件出すのかで規模が違い裁定の前提が変わる ③∴「どれを出すか」は選別の問題になり全部出すのが正しいとは限らない（`/api/state` が肥大する・`RAW_INPUT` は他で取れる）④選別の基準は私が決めず、候補は (a) Taka の問いに答えるのに要る RRI の判断値だけ (b) 別経路が無いものだけ (c) 全部——**CC-α は (b) を推すが決めない**。★方法の限界=`exposed` は静的走査で動的なキー参照を見落としうる／`placed` は `submit.py` の `_rec` のみで他ファイルが TRACE に書いていれば見落とす（`_rec` は `submit.py` 内の関数だが確かめていない）／別経路の有無を35件すべてについては調べていない／**私は数えただけで1件も直していない**。*
