# 【BUILD SPEC】`Task` の配線を1箇所だけ繋ぐ — **★観測の経路でも DW task を作る**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-31 01:0x / TYPE=BUILD_SPEC
- **運用方針 確認済（版: v2.8）** ／ **正典**: `TAKA_2026-07-31_RUNTIME_INSPECTION_COMMON_BASE_ORDER.md`（逐語）／**裁定**: `CC_MGR_2026-07-31_D144_…md`
- **★これは何に対して発火するのか**: **★`OBSERVE_CURRENT_STATE` / `RUNTIME_INSPECTION` に分類された投入。★GPU に限らない。**
- **★2DER 優先原則の例外**（正典 §Claude Code の役割 で IMPL が書くと明示）。**★この修正を 2DER の担当工程に数えない。★1/8 は動かない。**

---

# 1. ★設計の調査（★私が読んだ。★あなたは確かめ直してよい）

| # | 調べたこと | ★現状 | 根拠 |
|---|---|---|---|
| 1 | **どこで task を作らないと決めているか** | **★`_rec("DW_TASK_ID", None)`**（コメント `do NOT resume the old task; no capability-build task`） | **`twoder/submit.py:377`** |
| 2 | 既存の task 生成 | **★`create_task(task_id, project_id, goal, knowledge_packet, ts, manager_identity, contract=None)`** | **`dev-workcell/dw/workcell.py:347`** |
| 3 | **共通入口は既に在るか** | **★在る。★GPU 専用ではない。** `_CATALOG` は4種＝`gpu_memory` / `running_containers` / **`top_memory_processes`（Process）** / **`listening_ports`（Network）** | **`twoder/runtime_inspection.py:28-34`** |
| 4 | 選別は効いているか | **★効いていない。`build_request` が `list(_CATALOG.keys())` で★毎回 全件を要求する** | `runtime_inspection.py:46` |

> **★4 は今回 直さない。★記録するだけである**（正典「一度に一箇所」「能力追加は禁止」）。
> **★3 は正典の問い「GPU 専用ではなく共通入口になっているか」への答えの半分である。★残り半分（Task の下流に載るか）が今回の対象。**

---

# 2. ★直すのは1箇所だけ

```
★`twoder/submit.py` の OBSERVE_CURRENT_STATE / RUNTIME_INSPECTION 分岐で、
★`DW_TASK_ID` を None にする代わりに、★既存の create_task で task を1件 作り、その id を入れる。
```
| 条件 | |
|---|---|
| **★流用するもの** | **`dev-workcell/dw/workcell.py::create_task`**（★BUILD 経路が使っている既存関数）。**★新しい生成方式を作らない** |
| **★GPU 固有を書かない** | **★追加する分岐・定数・語彙・文字列に `gpu` / `nvidia` を含めない**（D-144 §3-1）。**★観測の経路一般に対する修正である** |
| **★作らないもの** | 新しい台帳／新しい API／新しいアーキテクチャ／今回専用の分岐 |
| **★触らないもの** | GPU 取得コマンド／`utilization.gpu`／プロセスの GPU 紐付け／`_CATALOG` の中身／`build_request` の全件要求／`BUILD_CAPABILITY`・`MODIFY_EXISTING` 経路 |

## 2-1. ★先に言う副作用（★feasibility-first。★あなたに隠さない）
```
★観測の依頼ごとに DW task が1件 増える。★その task は CREATED（PLAN 待ち）で残る。
★∴ 依頼一覧の件数と deferred の数え方に影響する。
★★これは「直す」対象ではない。★観測して記録すること（★件数の前後を書く）。
★もし増え方が明らかに異常なら（例: 1投入で2件以上）★そこで止めて設計へ聞く。
```

---

# 3. ★受入（★1条件に1つの印。★まとめない）

| # | 受入 | ★示し方 |
|---|---|---|
| **A-1** | task が1件 作られる | 応答の `task_id` が `null` でない |
| **A-2** | その task が引ける | `GET /api/resolve?id=<task_id>` が `resolved=true` |
| **A-3** | **★trace から task へ辿れる** | `GET /api/resolve?id=<新 trace_key>` の **`dw_task_ref`** が **その task_id と一致** |
| **A-4** | **★task から観測へ辿れる**（★今回いちばん大事） | **★同一 task から `ARUN-` / `OBS-` へ到達できるか。★できなければ「できない」と書く**（★次の切断点になる） |
| **B-1** | **★GPU 固有を書いていない** | **★diff 全体に `gpu` / `nvidia` が0件**（★大文字小文字を無視して走査・打ち切り無し） |
| **B-2** | **★1箇所だけ** | **★変更ファイルと変更行を全部 書く。★`submit.py` 以外に触ったら理由を書く** |
| **C-1** | **★後方互換（既存 ID）** | **★下の基準値10件を修正後に取り直し、★1件ずつ突き合わせる**（★`SUBMIT-` の2件は★もう「変わってよい」側ではない。★不変が期待） |
| **C-2** | **★後方互換（既存経路）** | **★`BUILD_CAPABILITY`/`MODIFY_EXISTING` 分岐に diff が無いこと**（★投入して確かめない。★diff で示す） |
| **D-1** | **★再利用できることを GPU 以外の1語で示す** | **★`listening_ports`（Network）を名指し、★同じ `_CATALOG` の同じ経路に載っていることを★コードで示す。★実装しない・実行しない**（能力追加は禁止） |

## 3-1. ★後方互換 基準値（★修正前・2026-07-31 00:52:50・設計が取得）
```
ARUN-00954 true/13   OBS-00955 true/10   DE-0525 true/10   TASK-2DER-B11764B3 true/3
ETR-fdf52322e5bf true/5   UTT-1010 true/12   SUBMIT-zOlryQ true/14   SUBMIT-_ayfew true/14
UTT-1012 true/12   NO-SUCH-ID-XYZ false/0
★依頼一覧の件数: tasks 156   ← ★修正後は「1件 増えて 157」が期待値（★2件以上 増えたら止める）
```

---

# 4. ★再検査（★修正後に必ず。正典「修正後は必ず同じ検査を再実行」）
```
① 正典（第2試行の指示書）から依頼文を機械で抜く（★sha1 が 0c458f38… と一致するか確認。違えば止める）
② POST /api/submit ★1回だけ
③ ★直後に GET /api/receipt（★他の口を叩く前に）
④ 新しい trace_key を resolve → A-1〜A-4 を1つずつ
⑤ 基準値10件を取り直す（C-1）＋ tasks 件数
```
**★`run_next` は押さない。** **理由: 今回の修正対象は `Task` の生成までである。★押すと PLAN（別の枝）に入り、★今回 直した配線の話とずれる。★押さなかったことを報告に書く。**
**★webui 再起動が要るなら、★全件 記録する**（操作内容/操作者/理由/既存運用か/主体判定への影響＋run-gate 初期化）。

---

# 5. ★やってはいけないこと
```
★GPU 取得処理を改善しない ★設計変更をしない ★能力を追加しない ★新しい帳票を作らない
★途中で別の改善を実装しない ★止まったらそこで終了（直さない・迂回しない・再投入しない）
★第1試行・第2試行の報告書を1文字も変えない ★commit しない（MGR）
★61本の非回帰は走らせない
```

# 6. ★止まってよい場所
```
★基準値10件が1件でも変わった → 止める（★今回は `SUBMIT-` も不変が期待である）
★tasks が2件以上 増えた → 止める
★`submit.py` 以外に触る必要が出た → 止めて設計へ聞く
★diff に `gpu`/`nvidia` が入りそう → 止める（★書き方を変えれば避けられるはず）
```

# 7. ★報告（★正典の形だけ。★増やさない）
```
★止まった場合: Last PASS / First FAIL / 原因 / 修正内容 / 次回確認箇所 ★の5行のみ
★通った場合  : 接続できた配線 / まだ切れている配線 / 次回修正すべき箇所(1件) /
               ★Runtime Inspection を他の監視項目へ再利用できる状態か
★受入 A-1〜D-1 の印は★別表で1つずつ（★内部の判定用。★6区分は使ってよい）
★宛: 設計/監査(CC-α)。TYPE=BUILT。★:8005 を使ったら1行 書く
```

---
**決めたこと**: **①直すのは `twoder/submit.py:377` の1箇所——観測の経路でも既存の `dw/workcell.py::create_task` で task を作り `DW_TASK_ID` に入れる（新しい生成方式を作らない・`gpu`/`nvidia` を diff に入れない） ②受入は A-1〜A-4（task 生成・resolve・trace から task・★task から観測へ辿れるか）＋ B（1箇所・GPU 固有なし）＋ C（基準値10件と既存経路の不変）＋ D（`listening_ports` で再利用可能性をコードで示す・実装しない） ③再検査は同一依頼文を1回だけ、`run_next` は押さない（今回の対象は Task の生成まで）。**
