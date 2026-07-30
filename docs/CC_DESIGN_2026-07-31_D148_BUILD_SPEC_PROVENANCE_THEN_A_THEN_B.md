# 【BUILD SPEC】観測経路に provenance を入れる（1箇所）→ **★A（同じ文）→ B（別項目）の順で各1回**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-31 02:2x / TYPE=BUILD_SPEC
- **運用方針 確認済（版: v2.8）** ／ **正典**: `TAKA_2026-07-31_RUNTIME_INSPECTION_COMMON_BASE_ORDER.md` ／ **裁定**: `CC_MGR_2026-07-31_D147_…` `D-148`
- **★これは何に対して発火するのか**: **★`OBSERVE_CURRENT_STATE` / `RUNTIME_INSPECTION` に分類された投入。★GPU に限らない。**
- **★2DER 優先原則の例外**（正典で IMPL が書くと明示）。**★2DER の担当工程に数えない。★1/8 は動かない。**

---

# 1. ★修正（★1箇所だけ。★A・B の前に済ませる）

```
★観測経路の knowledge_packet の provenance に、★不足3件を入れる:
   trace_id / rri_request_id / rri_intent_id
```
| | |
|---|---|
| **★流用するもの** | **★BUILD 経路が既にやっている形をそのまま**: `submit.py:449` の `trace_id = "TRACE-" + sha1((utterance_id + ts))[:10]` ／ **`rri.intent_record.mint`**（`IR.mint("REQUEST"…)` / `IR.mint("INTENT"…)`）。**★`submit.py:435-437` と `449-450` が見本である** |
| **★検査側の要求（逐語）** | `dispatch_provenance.py:24` **`REQUIRED_RESOLVABLE = ("dw_task_id","ds_input_id","rri_request_id","rri_intent_id")`** ／ `:26` **`REQUIRED_PRESENT = ("trace_id",)`**。**★`dw_task_id`・`ds_input_id` は既に入っている**（実測） |
| **★作らないもの** | **新しい ID 族／新しい台帳／新しい API／新しい採番方式** |
| **★触らないもの** | `BUILD_CAPABILITY`/`MODIFY_EXISTING` 経路の provenance ／ A-3（trace_key の prefix）／ 生出力（blob）／ GPU 取得コマンド ／ `_CATALOG` ／ `build_request` の全件要求 |
| **★語の禁止** | **★diff に `gpu` / `nvidia` を0件**（大小無視・打ち切り無しで走査して示す） |

---

# 2. ★A（同じ依頼文で1回）— **★予告を先に固定した。★測ってから書かない**

## 2-1. 投入
```
★第2試行の指示書から機械で抜く（★sha1 が 0c458f38… / 54字 と一致するか確認。違えば止める）
★POST /api/submit ★1回 → ★直後に GET /api/receipt（★他の口を叩く前に）→ run_next ★1回
```
## 2-2. ★予告（★MGR `D-148` §2 が固定。★外れたら「外れた」と書く）
```
★同じ task_id（TASK-2DER-0C458F38）に当たり、★CREATE は作り直されない
★provenance は {ds_input_id, etrace_run_id, dw_task_id} のまま
★run_next を押すと★同じ3件（trace_id / rri_request_id / rri_intent_id）で fail-closed する
★★特に「CREATE が作り直された」なら、★設計（私）の読みが誤っていたことになる。★そう書くこと
```
> **★A は「届かない」を★観測で示すために行う。★いまはコードを読んだ結果でしかない。**

---

# 3. ★B（別項目で1回）— **★文は MGR が固定した。★1文字も変えない**

```
現在の待ち受けポートの状況を取得し、ポートごとの待ち受けアドレス、ポート番号、待ち受けているプロセスを確認して要約してください。
```
**★`CC_MGR_2026-07-31_D148_…md` の §3 から機械で抜くこと**（★打ち直さない）。**★64字 / sha1 `67fe6548003f2ecc1a209198e224c291eddc0f9d`**（★設計が事前に計算した。★一致を確認してから投入する）。

## 3-1. ★予告（★決定論。★設計が事前に計算した）
```
★生まれる task_id は ★TASK-2DER-67FE6548 である（★task_id = 依頼文 sha1 の先頭8桁 大文字）
★★違う id が出たら、★採番の理解が誤っていたことになる。★そう書くこと
```
## 3-2. 手順
```
★POST /api/submit ★1回 → ★直後に GET /api/receipt → 新 trace_key を resolve → run_next ★1回
```

---

# 4. ★受入（★1条件に1つの印。★まとめない）

| # | 受入 | ★示し方 |
|---|---|---|
| **F-1** | 修正は1箇所 | 変更ファイル・hunk 数・挿入/削除行数 |
| **F-2** | GPU 固有語が無い | **diff に `gpu`/`nvidia` が0件**（大小無視・打ち切り無し） |
| **F-3** | 後方互換（既存 ID） | **★下の基準値を修正後に取り直し、1件ずつ突き合わせる** |
| **F-4** | 後方互換（既存経路） | **`BUILD_CAPABILITY`/`MODIFY_EXISTING` 経路に diff が無い**（★投入して確かめない。diff で示す） |
| **A-1** | A の予告どおりか | `task_id` / `DW_TASK_CREATE_RESULT` / provenance の中身 / `run_next` の `planner_outcome` |
| **A-2** | A で新しい観測が生まれたか | **★`ARUN-00966` / `OBS-00967` が `resolved` になったか**（★基準は下記） |
| **B-1** | B の task_id が予告どおりか | **★`TASK-2DER-67FE6548` か**（違えば書く） |
| **B-2** | **★B で provenance が載ったか（★核心）** | **★`GET /api/claude_packet?task_id=` の `knowledge_packet.provenance` に★`trace_id`/`rri_request_id`/`rri_intent_id` が在るか** |
| **B-3** | **★B で PLAN が動いたか（★核心）** | `run_next` の返り値全文 ／ `planner_outcome` ／ `implementation_packet_ref` の有無 ／ 在れば **`plan_source`** と **`runtime_recovery`** |
| **B-4** | B で新しい観測が生まれたか | **★`ARUN-` / `OBS-` の番号が基準から増えたか** |
| **B-5** | 副作用 | `tasks` の件数（★基準 157） |

## 4-1. ★基準値（★設計が修正前に取った・2026-07-31 02:16:40）
```
★ARUN-00966 = resolved:false（未生成）  ★OBS-00967 = resolved:false（未生成）
★TASK-2DER-0C458F38 = resolved:true     ★tasks = 157
★後方互換の10件は `D-144 SPEC §3-1` の値をそのまま使う（★ARUN-00954 / OBS-00955 / DE-0525 /
  TASK-2DER-B11764B3 / ETR-fdf52322e5bf / UTT-1010 / SUBMIT-zOlryQ / SUBMIT-_ayfew / UTT-1012 / NO-SUCH-ID-XYZ）
```

---

# 5. ★報告に必ず書く1行（★MGR `D-148` §4）
> **★「B は同じ検査ではない」**（★比較の母数が変わるため）

# 6. ★止まってよい場所
```
★依頼文の sha1 が予告と違った → 止める（★打ち直さない）
★後方互換の基準値が1件でも変わった → 止める
★B の task_id が TASK-2DER-67FE6548 でない → ★止めずに書く（★採番の理解の誤りとして記録する）
★PLAN が動いたら → ★そこで止めて返す。★GENERATE へ進まない
★`claude_barrier` で止まったら → ★押し破らない
★2通りに読めたら → ★止めて設計へ聞く（★前回それで事故を防いだ）
```

# 7. ★やってはいけないこと
```
★A と B を同時に投入しない（★A を終えてから B）  ★各1回だけ・再投入しない
★止まった所を直さない・迂回しない  ★他の task を押さない
★GPU 取得・生出力・A-3・選別を触らない  ★commit しない  ★61本の非回帰は走らせない
★:8005 を自分で叩かない（★2DER が内部で呼ぶのは可。★呼ばれたら1行 書く）
```

# 8. ★報告の形
```
★正典の5行（Last PASS / First FAIL / 原因 / 修正内容 / 次回確認箇所）
★受入 F-1〜B-5 は別表で1つずつ  ★予告の当否を A・B それぞれに書く
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①修正は1箇所——観測経路の provenance に既存の `trace_id` 生成と `IR.mint` で3件を入れる（新しい ID 族も台帳も作らない・`gpu`/`nvidia` は diff に0件） ②A（同じ文）は「届かない」を観測で示すために行い、予告（同じ3件で fail-closed・CREATE は作り直されない）を投入前に固定した ③B の文は MGR が固定し、設計が事前に sha1 と task_id（`TASK-2DER-67FE6548`）を計算して予告した——核心は B-2（provenance が載ったか）と B-3（PLAN が動いたか）。**
