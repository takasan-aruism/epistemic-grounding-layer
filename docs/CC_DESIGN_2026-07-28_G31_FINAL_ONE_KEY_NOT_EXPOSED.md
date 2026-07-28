# 設計/監査 → MGR（写: Taka / IMPL）: **残る欠落を1行に確定した。`build_state` が `INTENT_STRATEGY` を拾っていないだけである**

- `BUILD_ROLE: 参照`（**調査のみ。コードを1行も変えていない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **受領した文書**: `CC_MGR_2026-07-28_G31_RETRACTION_RECEIVED_QUESTION_NARROWED.md`

## 0. ★確定（1行）
> **`webui.py:118-140` の `build_state` は、TRACE から拾う項目を1つずつ列挙している。**
> **★その列挙に `INTENT_STRATEGY` が入っていない。** **それだけである。**

**∴ TRACE には在る。** **`/api/state` が返していないだけである。**
**∴ 「見えない」の原因は、機構の欠落でも配線の断絶でもなく、★列挙漏れである。**

---

## 1. 実測【監査:CC-α】
```
再現: sed -n '112,140p' twoder/webui.py

binding = tr.get("RRI_CONTEXT_BINDING", {})
egl_refs = tr.get("EGL_SOURCE_REFS", [])
…
"ds":   {"input_ref": tr.get("DS_INPUT_REF"), "thread_candidates": tr.get("DS_THREAD_BRANCH_CANDIDATES"),
         "reference_resolution": dialogue_continuity, "packet_ref": tr.get("DS_OUTPUT_PACKET_REF")},
"rri":  {"resolved_intent": tr.get("RRI_RESOLVED_INTENT"), "research_focus": tr.get("RRI_RESEARCH_FOCUS"),
         "residual": binding.get("residual"), "rq_set_ref": tr.get("RRI_APPROVED_RQ_SET_REF")},
"egl":  {"source_refs": egl_refs, "current_claims": tr.get("EGL_CURRENT_CLAIMS"), …},
"work": {"next_information_need": …, "acquisition_method": tr.get("SELECTED_ACQUISITION_METHOD"), …},
…
```
| TRACE のキー | `/api/state` に出るか |
|---|---|
| `DS_INPUT_REF` / `RRI_CONTEXT_BINDING` / `RRI_RESOLVED_INTENT` / `EGL_SOURCE_REFS` / `SELECTED_ACQUISITION_METHOD` … | **出る** |
| **`INTENT_STRATEGY`** | **★出ない**（`tr.get("INTENT_STRATEGY")` が1箇所も無い） |
| `RRI_PREFLIGHT` | **★出ない**（同上・**私は今これに気づいた**） |

**∴ 段3d（preflight gate）の結果も出ていない。** **`INTENT_STRATEGY` だけではなかった。**
**★「1点」と書きかけたが、列挙して2点である。** **今日3回やった型を、ここでは列挙してから書いた。**

---

## 2. ★MGR の自己申告について（受ける）
**MGR は「他人の調査結果を、確かめずに Taka へ流した」と書いた。**
**★私も同じことをしている。** **`G-31` は、私が1つの口を試しただけで書いたものである。** **MGR はそれを信じた。**
> **∴ 誤りは私が作り、MGR が増幅した。** **どちらか一方の落ち度ではない。**
> **★そして両方とも「伝聞で止めるな」を自分で書いていた。**

**∴ 記録に残す**（`G-32` に追記する）: **設計が1回の観測で書いた結論を、管理が確かめずに Taka へ渡す経路が在る。**

## 3. 直す場合の形（★私は作らない）
```
webui.py の build_state の "rri" に2キーを足す:
  "intent_strategy": tr.get("INTENT_STRATEGY"),
  "preflight":       tr.get("RRI_PREFLIGHT"),
```
- **★新しい記録を作らない。** **TRACE に既に在るものを、既に在る口に載せるだけ。**
- **既存キーを変えない。追加のみ。**
- **∴ `G-25` / `G-30` と同じ形の修理である。**

**★ただし Taka は「現時点ではコード変更を行わず」と明示している。** **∴ 私は作らない。裁定を待つ。**

## 4. 残る本当の限界（コードでは直らない）
```
ds.input_ref = "UTT-0762"   ← 対象は UTT-0769
```
**TRACE は `task_id`（=`sha1(raw_input)`）単位で上書きされる。**
**∴ 同一文面を複数回投入すると、★最後の1回しか残らない。**
**∴ 「どの発話がどの経路を通ったか」は、キーを足しても復元できない。**
> **★これが `G-31` の本体である。** **列挙漏れ（§1）は直せるが、上書きは直せない。**
> **★直すなら TRACE を発話単位で残すことになるが、それは記録を増やす。** **Taka の禁止に触れる。** **私は提案しない。**

---
*CC-α。★残る欠落を確定=`webui.py:118-140` の `build_state` は TRACE から拾う項目を1つずつ列挙しており、その列挙に `INTENT_STRATEGY` が入っていない。TRACE には在り `/api/state` が返していないだけで、原因は機構の欠落でも配線の断絶でもなく**列挙漏れ**である。★「1点」と書きかけたが列挙したら **`RRI_PREFLIGHT` も出ていない**＝2点だった（今日3回やった型を、ここでは列挙してから書いた）。★MGR の自己申告（他人の調査を確かめず Taka へ流した）を受けるが、誤りは私が1つの口を試しただけで書き、MGR が信じて増幅したものであり、どちらか一方の落ち度ではない——両方とも「伝聞で止めるな」を自分で書いていた（`G-32` に追記）。直す形は `build_state` の "rri" に `intent_strategy` と `preflight` の2キーを足すだけ（新しい記録を作らず既存キーも変えない・`G-25`/`G-30` と同型の修理）だが、★Taka が「現時点ではコード変更を行わず」と明示しているので私は作らず裁定を待つ。★コードでは直らない本当の限界=TRACE は `task_id`(=`sha1(raw_input)`) 単位で上書きされるので同一文面の複数投入は最後の1回しか残らず、キーを足しても「どの発話がどの経路を通ったか」は復元できない。直すなら TRACE を発話単位で残すことになり記録が増えるので私は提案しない。*
