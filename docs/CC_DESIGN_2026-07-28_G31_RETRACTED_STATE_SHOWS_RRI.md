# 設計/監査 → MGR（写: Taka / IMPL）: **★`G-31` を撤回する。`/api/state` で段2〜3e は引けた。私はまた「探した範囲に無い」を「無い」と書いた**

- `BUILD_ROLE: 参照`（**調査のみ。コードを1行も変えていない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **★緊急度**: **MGR が (a) を Taka に上げようとしている。** **その前提が崩れた。**

## 0. ★結論（先に）
> **`GET /api/state?task_id=…` は、`rri` / `ds` / `egl` を返す。**
> **∴ 段2〜3e の結果は front door から引ける。**
> **∴ `G-31`（front door から中間結果を引く手段が無い）は★誤りである。撤回する。**
> **∴ MGR が Taka に上げようとしている (a)（`TRACE-…` を解決できるようにする）は、★不要である可能性が高い。**

---

## 1. 実測【監査:CC-α】
```
再現: GET /api/state?task_id=TASK-2DER-B9B4DA3B  （Basic 認証）
返りキー: actor_role / block_source_refs / claude_barrier / dispatch_status / ds / ds_limitation /
          dw_state / egl / failure_memory_match / goal / guard_block / last_completed_op /
          next_operation / rri

rri.resolved_intent.request_type = "BUILD_CAPABILITY"        ← ★段3b の結果
rri.resolved_intent.blockage.classification = "implementation"
rri.research_focus = ["rid から接頭辞を抽出するための明確なルールまたは定義", …]
ds.input_ref = "UTT-0762"  / ds.reference_resolution = "UNRESOLVED HISTORICAL REFERENCE …"
egl.source_refs = ["DE-0557"] / egl.current_claims = [ … ]   ← ★段3a の結果
```
**根拠（コード）**: `webui.py:112` の `build_state` が `tr = _trace(task_id)` で TRACE を読んでいる。

## 2. ★私の誤り
**私は `/api/resolve?id=TRACE-0769` を1回試し、`resolved:false` を得て「front door から知る手段が存在しない」と書いた。**
- **`/api/state` を試していない。**
- **`webui.py` の `/api/` の口を列挙していれば、12個あることが分かった**（今回列挙した）。
> **★「探した範囲に無い」を「無い」と書いた。** **本日3回目である。**
> **★しかも私は D-40b の直前に、同じ型で `G-01` を撤回している。** **警戒しながら同じことをした。**

## 3. ★ただし、引けるものには限界がある（正確に書く）
```
ds.input_ref = "UTT-0762"      ← ★UTT-0769 ではない
```
**`_trace(task_id)` は `twoder/runs/<task_id>.trace.json` を読む。** **このファイルは submit のたびに上書きされる**（`webui.py:542-543`）。
**`task_id` は `sha1(raw_input)` なので、同じ文面の投入はすべて同じファイルを指す。**

> **∴ `/api/state` が返すのは「その依頼文に対する★最新の submit の結果」である。**
> **∴ `UTT-0769` に固有の結果ではない。** **同一文面が `UTT-0762 / 0768 / 0769` と複数在るため、発話単位の帰属はできない。**

**∴ `G-31` は「手段が無い」ではなく、★次に置き換える:**
| id | 差し替え後 |
|---|---|
| **`G-31`** | **`/api/state` で段2〜3e は引けるが、TRACE は `task_id` 単位で上書きされるため★発話単位の帰属ができない**（同一文面の再投入で上書きされる） |

## 4. D-40b の13項目の訂正（★該当分のみ）
| # | 旧 | **新** | 根拠 |
|---|---|---|---|
| **2** `request_type` | 未確認 | **★実行確認済み（ただし発話単位でない）** | `rri.resolved_intent.request_type = BUILD_CAPABILITY` |
| **3** `context_binding` | 未確認 | **★一部 実行確認済み** | `ds.reference_resolution` が返る（`anchoring` そのものは返りに無い＝**未確認**） |
| **4** `intent_strategy` | 未確認 | **★未確認のまま** | 返りに `INTENT_STRATEGY` が無い。**`build_state` が拾っていない** |
| **8** 7戦略の決定値 | 未確認 | **★未確認のまま** | 同上 |
| **10** EGL に何が書かれたか | 未確認 | **★実行確認済み** | `egl.source_refs = ["DE-0557"]`・`current_claims` が返る |

**∴ 残る真の欠落は「`INTENT_STRATEGY` が `/api/state` に出ない」の1点である。** **段2〜3e 全体ではない。**

## 5. MGR への依頼（★急ぐ）
- **Taka へ上げる前に、本文書を読んでください。** **(a) の必要性が変わります。**
- **もし既に上げていたら、★訂正してください。** **私の `G-31` が誤りだったためです。**

## 6. 私が変えること
- **★「無い」と書く前に、その種類の口を列挙する。** **1つ試して無かったで済ませない。**
- **本日3回同じ型をやった。** **`G-32` として登録する**（私の作法の欠陥として）。

---
*CC-α。★`G-31` を撤回する——`GET /api/state?task_id=…` が `rri`/`ds`/`egl` を返し、段3b の `request_type`(BUILD_CAPABILITY)、`ds.reference_resolution`、段3a の `egl.source_refs`(DE-0557)/`current_claims` が front door から引けた（`webui.py:112` の `build_state` が TRACE を読んでいる）。∴「front door から中間結果を引く手段が無い」は誤りで、MGR が Taka に上げようとしている (a) は不要な可能性が高い。★私の誤り=`/api/resolve?id=TRACE-0769` を1回試して `resolved:false` を得ただけで「手段が存在しない」と書いた。`/api/` の口は12個あり列挙していなかった。**「探した範囲に無い」を「無い」と書いた本日3回目で、しかも直前に同じ型で `G-01` を撤回したばかりだった。** ★ただし限界がある=`_trace` は `twoder/runs/<task_id>.trace.json` を読み submit のたびに上書きされ、`task_id` は `sha1(raw_input)` なので同一文面の投入は同じファイルを指す ∴ 返るのは「その依頼文に対する最新 submit の結果」で `UTT-0769` 固有ではなく、発話単位の帰属はできない（`ds.input_ref` は `UTT-0762`）。∴ `G-31` を「発話単位の帰属ができない」に差し替える。D-40b の13項目を訂正: #2 実行確認済み・#3 一部確認・#10 実行確認済み／#4 と #8 は**未確認のまま**（`INTENT_STRATEGY` が `/api/state` に出ない＝`build_state` が拾っていない）∴ **残る真の欠落は1点**であって段2〜3e 全体ではない。MGR は Taka へ上げる前に本文書を読み、既に上げていれば訂正してほしい。私が変えること=「無い」と書く前にその種類の口を列挙する（`G-32` として登録）。*
