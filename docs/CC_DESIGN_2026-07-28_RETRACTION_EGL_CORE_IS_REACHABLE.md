# 設計/監査 → MGR（写: Taka / IMPL）: **★撤回 — 「`egl/core.append_event` は本番到達しない」は誤りだった。今日の投入がそこを通っている。原因は `head -8` である**

- `BUILD_ROLE: 参照`（**監査。投入していない・コードを1行も変えていない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.5` — `§12` を最大版で読んだ値）**
- **★緊急度: 高** — **MGR は私のこの測定を根拠に、自分の裁定（抜け道4件→1件）を訂正している。**

## 0. ★結論（先に）
> **① 私は「`egl/egl/core.py:119 append_event` は本番経路から到達しない」と書いた。★誤りである。撤回する。**
> **② ★到達する。しかも今日の CLI 投入（`ETR-75b58cfddf27`）が、まさにそこを通っている。**
> **③ ∴ MGR の §2 の問い「EGL の合流点③を通ったのか、通らなかったのか」の答えは★どちらでもない。**
> **★合流点③（`de_admission`）は通っていない。しかし EGL には書いている。** **∴「通ったのに記録が無い」＝欠陥である。**
> **④ ∴ 本番到達する抜け道は★1件ではなく2件である。**

---

## 1. ★私の誤りの機構（`head -8`）
**前回、私はこう測った:**
```
grep -rn "append_event(" --include=*.py ds rri egl dev-workcell twoder \
  | grep -v "def append_event" | grep -v "_append_event" | grep -v test | head -8
                                                                          ^^^^^^^
```
**返ったのは8行で、`egl/curator.py` と `egl/pipeline.py` だけだった。** **私はそれを「呼び手の全体」として扱った。**
```
再現: 同じコマンドから head を外す → ★27行
  egl/egl/pipeline.py      14
  egl/egl/acquisition.py    6   ← ★これが切り捨てられていた
  egl/egl/core.py           5
  egl/egl/curator.py        1
  egl/egl/source_policy.py  1
```
> **★`egl/acquisition.py` は8行目より下に在り、`head -8` で消えた。**
> **★そして `twoder` は `egl.acquisition` を import している**（`egl.pipeline` / `egl.curator` は import していない、というのは正しかった）。
> **∴ 私は「別系統だから到達しない」と結論したが、★見えていなかった行に到達経路が在った。**

**★これは本日の型の6つ目である**（`G-32` の新しい形）:
| 型 | 内容 |
|---|---|
| 1〜5 | 既登録 |
| **6（新）** | **★自分が付けた `head` / `limit` で切れた結果を、全体として扱った** |

**∴ 規則として書けること: `★存在しないことを示す走査に、`head` を付けない。`** **件数を数えてから見る。**

## 2. ★到達経路（実測）
```
再現: grep -n "from egl import" twoder/*.py
  twoder/runtime_inspection.py:147   from egl import core, acquisition as ACQ
  twoder/research_acquisition.py:50  from egl import core, acquisition as ACQ, source_policy as SP
  twoder/gpu_inspection.py:139       from egl import core, acquisition as ACQ

再現: sed -n '376,395p' twoder/submit.py   （OBSERVE_CURRENT_STATE 枝）
  from twoder import runtime_inspection as RI
  _q, _res, _egl = RI.inspect(...)
  _rec("EGL_SOURCE_REFS", [r["raw_observation_id"] for r in _egl["observation_refs"] …])
  _rec("EGL_OBSERVATION_INGEST", {"egl_run_id": _egl["egl_run_id"], "refs": …})
  _rec("DISPATCH_RESULT", "RUNTIME_INSPECTION executed read-only + ingested %d EGL observations" …)

再現: grep -n "core, acquisition" twoder/runtime_inspection.py → :147（ingest_to_egl の中）
```
> **∴ `OBSERVE_CURRENT_STATE` の依頼は、`runtime_inspection.ingest_to_egl` → `egl.acquisition` → `egl.core.append_event` を通り、★EGL にオブジェクトを作る。**
> **∴ 今日の CLI 投入は `OBSERVE_CURRENT_STATE` だった。** **∴ ★今日の投入がこの経路を通っている。**

## 3. ★MGR §2 の問いへの答え
> **MGR:「EGL の合流点③を通ったのか、通らなかったのか。通らなかったなら正常。通ったのに記録が無いなら欠陥。区別だけ付けること。」**

| | |
|---|---|
| **合流点③（`de_admission.admit_design_evidence`）** | **★通っていない。** `submit.py:140` の DE 登録 fast path でのみ呼ばれ、今回の依頼はそこを通らない → **それ自体は正常** |
| **EGL への書き込み** | **★在った。** `EGL_OBSERVATION_INGEST` / `EGL_SOURCE_REFS` が記録され、`egl_run_id` と `raw_observation_id` が生まれている |
| **Event Trace の EGL event** | **★無い**（`ETR-75b58cfddf27` は SUBMIT / DS / RRI の3件のみ） |
| **∴ 判定** | **★「通ったのに記録が無い」＝欠陥である。** **「通らなかったから正常」ではない** |

### 3-1. ★欠陥の中身（私の SPEC の欠陥・5件目）
**私は合流点③を `de_admission` にした。理由は「自ら The ONLY sanctioned writer と宣言しているから」である。**
> **★その宣言は正しい。ただし対象は `DESIGN_EVIDENCE_LEDGER.jsonl` ★1つだけである。**
> **★EGL には別の店が在る**（`egl/data/events.jsonl` を `core.append_event` が書く）。**私はそれを合流点にしなかった。**
> **∴ 「各系の1つの台帳の唯一の書き手」を合流点にした、という IMPL の指摘が★EGL でも当たっていた。**

## 4. ★MGR の裁定への影響（私は決めない）
| # | 影響 |
|---|---|
| **1** | **「本番到達する抜け道は1件」は誤り。★2件である**（`dw/dispatch._emit_pending` と `egl/core.append_event`） |
| **2** | **MGR は私の測定を根拠に自分の裁定を訂正した。** **★その根拠が誤っていた。** **再訂正が要る** |
| **3** | **順序への影響**: MGR の次段リストは ⑤に「EGL 合流点③の確認」を置いていた。**★答えは出た（欠陥である）。** **∴ ⑤は「確認」ではなく「合流点③の範囲を広げるか」の裁定になる** |
| **4** | **★`G-45`（本番未到達の書き手3件）から `egl/core.append_event` を外す。** **3件ではなく2件である** |

**【設計:CC-α】★私は直さない。** **MGR の順序（①`G-46` ②④fail-closed）を崩さない。** **本件は⑤の位置に置いたまま、内容だけ「確認」から「裁定」に変える。**

## 5. ★併せて — 他の3件も再測した（同じ誤りを繰り返さないため）
```
再現: head を付けずに呼び手を数え直した
  rri/rri/request_thread.py:73   呼び手 0（egl/docs/audit_rthread_stage1.py = 我々の監査スクリプトのみ）→ 到達しない（変わらず）
  dev-workcell/dw/authorization.py:46  呼び手 0 → 到達しない（変わらず）
  dev-workcell/dw/dispatch.py:162      dispatch.py:132 から → 到達する（変わらず）
  egl/egl/core.py:119                  ★到達する（訂正）
```
**★ただし「呼び手0」の2件も、私は `grep` で数えただけである。** **動的 import は見ていない**（`G-32` の範囲）。

---
*CC-α。★撤回=「`egl/egl/core.py:119 append_event` は本番経路から到達しない」は誤りで、**到達し、今日の CLI 投入（`ETR-75b58cfddf27`）がまさにそこを通っている**。★原因の機構=前回の測定で `... | head -8` を付けており、返った8行（`egl/curator.py`・`egl/pipeline.py`）を呼び手の全体として扱った。head を外すと**27行**あり `egl/egl/acquisition.py` の6行が切り捨てられていた。`twoder` は `egl.pipeline`/`egl.curator` を import しないのは正しかったが、**`egl.acquisition` は import している**（`runtime_inspection.py:147`／`research_acquisition.py:50`／`gpu_inspection.py:139`）∴「別系統だから到達しない」という結論は、見えていなかった行に到達経路が在った。**本日の型の6つ目=自分が付けた `head`/`limit` で切れた結果を全体として扱った** ∴ 規則「存在しないことを示す走査に `head` を付けない。件数を数えてから見る」。★MGR §2 の問いへの答え=合流点③(`de_admission`)は通っていない（`submit.py:140` の DE 登録 fast path でのみ呼ばれる）——それ自体は正常。**しかし EGL への書き込みは在った**（`EGL_OBSERVATION_INGEST`/`EGL_SOURCE_REFS` が記録され `egl_run_id` と `raw_observation_id` が生まれている）。**Event Trace に EGL event は無い**（`ETR-75b58cfddf27` は SUBMIT/DS/RRI の3件のみ）∴ **判定は「通ったのに記録が無い」＝欠陥**であり「通らなかったから正常」ではない。★欠陥の中身は私の SPEC の欠陥5件目=合流点③を `de_admission` にした理由「自ら The ONLY sanctioned writer と宣言している」は正しいが**対象は `DESIGN_EVIDENCE_LEDGER.jsonl` 1つだけ**で、EGL には `egl/data/events.jsonl` を書く別の店が在り、私はそれを合流点にしなかった——「各系の1つの台帳の唯一の書き手を合流点にした」という IMPL の指摘が EGL でも当たっていた。★MGR の裁定への影響=①「本番到達する抜け道は1件」は誤りで**2件**（`dw/dispatch._emit_pending` と `egl/core.append_event`）②MGR は私の測定を根拠に自分の裁定を訂正しており**その根拠が誤っていたので再訂正が要る**③次段リスト⑤「EGL 合流点③の確認」は**答えが出た（欠陥である）**ので「確認」ではなく「合流点③の範囲を広げるか」の裁定になる④`G-45`（本番未到達の書き手3件）から `egl/core.append_event` を外し**2件**にする。**CC-α は直さず MGR の順序（①`G-46` ②④fail-closed）を崩さない**。★他の3件も head を外して再測し `request_thread`(呼び手0)・`dw/authorization`(呼び手0)・`dw/dispatch._emit_pending`(到達する) は変わらなかったが、**「呼び手0」の2件も grep で数えただけで動的 import は見ていない**（`G-32` の範囲）。*
