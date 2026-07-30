# 【BUILT】D-148 — provenance を1箇所 入れ、A（同じ文）→ B（別項目）を各1回。**★B で PLAN が動いた**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 02:4x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）** ／ **実装源**: `CC_DESIGN_2026-07-31_D148_BUILD_SPEC_PROVENANCE_THEN_A_THEN_B.md`
- **受領した MGR 文書**: **無し**（B の依頼文のみ `CC_MGR_2026-07-31_D148_…md` §3 から**機械で抽出**）
- **★2DER 優先原則の例外**（正典で IMPL が書くと明示）。**★2DER の担当工程に数えない。★1/8 は動かない**
- **`:8005` が呼ばれた**（★私は0件。**★B の `run_next` で 2DER が2回 呼んだ**）

> ### ★必ず書く1行（MGR `D-148` §4）
> **★B は同じ検査ではない**（★比較の母数が変わるため）。

---

# 0. ★5行（正典の形）
```
Last PASS   : ★B で PLAN が動いた。dispatched=true / CREATED → READY_FOR_IMPLEMENTATION /
              plan_source=QWEN_BUILD_PLANNER / runtime_recovery={attempts:2, final_max_tokens:4096, RECOVERED}
First FAIL  : ★A の run_next は同じ3件で fail-closed のまま（★予告どおり。★新しい失敗ではない）
原因        : A は CREATE が既に在り `create_task` が弾かれるので、★古い packet のまま更新されない。
              B は新しい task なので、★今回入れた provenance が CREATE に載った
修正内容    : `twoder/submit.py` ★1箇所（2 hunk・7挿入1削除／`gpu`・`nvidia` は diff に0件）
次回確認箇所: ★GENERATE を1回だけ押すか（＝worker まで流れるか）★1件。★私は押していない
```

---

# 1. ★受入（★1条件に1つの印）

| # | 受入 | 印 | 実測 |
|---|---|---|---|
| **F-1** | 修正は1箇所 | **○** | `twoder/submit.py` のみ／hunk **2**（`@@ -380,0 +381,5` と `@@ -382 +387,2`・**★どちらも観測分岐の中**）／**7挿入・1削除** |
| **F-2** | GPU 固有語が無い | **○** | diff を大小無視・打ち切り無しで走査 → **`gpu`／`nvidia` は0件** |
| **F-3** | 後方互換（既存 ID） | **○** | **13件すべて期待どおり**（10件の基準値＋`ARUN-00966`/`OBS-00967` の未生成＋`TASK-2DER-0C458F38`）。`tasks` も 157 |
| **F-4** | 後方互換（既存経路） | **○** | diff の hunk は 381・387 行のみ。**`DW_IMPLEMENTATION` 経路（439行以降）に diff 無し**（★投入して確かめていない・diff で示した） |
| **A-1** | A の予告どおりか | **○（3点とも的中）** | `task_id=TASK-2DER-0C458F38`（同じ）／**★`events=1` のまま＝CREATE は作り直されていない**／provenance は **`{ds_input_id: UTT-1013, etrace_run_id, dw_task_id}` のまま**／`run_next` は **同じ3件**（`trace_id`・`rri_request_id`・`rri_intent_id`）で fail-closed |
| **A-2** | A で新しい観測が生まれたか | **★生まれた。★ただし PLAN 由来ではない** | `ARUN-00966`・`OBS-00967` は **`resolved=true` になった**。**★出所は投入時の runtime inspection**（`OBS-00967〜00970` は **`run_next` を押す前の submit 応答に既に載っている**）。**★`run_next` は `dispatched=false`・PLAN 未記録** |
| **B-1** | B の task_id が予告どおりか | **○** | **`TASK-2DER-67FE6548`**（予告と一致）。依頼文は **64字 / sha1 `67fe6548…`**（一致を確認してから投入） |
| **B-2** | **B で provenance が載ったか** | **○** | `trace_id=TRACE-1428eabad7` ／ `rri_request_id=RREQ-00248` ／ `rri_intent_id=RINT-00341` ／ `ds_input_id=UTT-1015` ／ `dw_task_id=TASK-2DER-67FE6548`（**★不足3件がすべて載った**） |
| **B-3** | **B で PLAN が動いたか** | **○** | `dispatched=true`／`refused` なし／`state: CREATED → READY_FOR_IMPLEMENTATION`・`last_completed_op=PLAN`・`next_operation=GENERATE`・`actor_role=QWEN_LIVECODER`／**`plan_source=QWEN_BUILD_PLANNER`**／**`runtime_recovery={attempts:2, final_max_tokens:4096, outcome:RECOVERED}`** |
| **B-4** | B で新しい観測が生まれたか | **★増えていない（PLAN 由来は0）** | `ARUN-00973`・`OBS-00974` までは在る（**★B の投入時 inspection 由来**）。**`ARUN-00974`・`OBS-00975` は `resolved=false`＝PLAN では観測は増えない** |
| **B-5** | 副作用 | **★+1** | `tasks` **157 → 158** |

---

# 2. ★予告の当否（★測ってから書いていない）

| | 予告 | 実測 | |
|---|---|---|---|
| **A** | 同じ task_id に当たる | `TASK-2DER-0C458F38` | **★当たり** |
| **A** | CREATE は作り直されない | `events=1` のまま | **★当たり** |
| **A** | provenance は3件のまま | `{ds_input_id, etrace_run_id, dw_task_id}` | **★当たり** |
| **A** | 同じ3件で fail-closed | 同じ3件 | **★当たり** |
| **B** | `TASK-2DER-67FE6548` が生まれる | 一致 | **★当たり** |

**★設計（CC-α）の読みが誤っていた点は無い。**（「CREATE が作り直された」は起きていない）

---

# 3. ★PLAN の中身（★事実のみ。★評価しない）
```
plan_source        : QWEN_BUILD_PLANNER
runtime_recovery   : attempts=2 / final_max_tokens=4096 / outcome=RECOVERED
requirement(冒頭)  : "Implement a Python script named 'port_checker.py' … 'ss -tulnp' … retrieve listen…"
test_command       : ["python3", "test_port_checker.py"]
prohibited_actions : sudo/root ・ ネットワーク ・ commit/push ・ 作業領域外の変更 ・ 第三者パッケージ導入
cites_source_ids   : []   ← ★空である（★観測 OBS- を引用していない）
```
**★依頼は「待ち受けポート」で、★PLAN も port の話になっている**＝**★GPU 専用の経路ではない**ことの、実行による1例。

## 3-1. ★`:8005` の実測（★押した区間 JST 02:33:35〜02:34:05）
```
17:33:47.639Z  200 OK      17:34:02.973Z  200 OK      → ★2件
★`runtime_recovery.attempts=2` と件数が一致する（★同一区間・他に呼び手なし）
```
**★参考（断定しない）**: D-133 で「窓に2件、どちらが PLAN か名指しできない」と書いた形と**同じ並び**である。**★今回のは attempts と一致したが、★D-133 の2件を遡って説明するものではない。**

---

# 4. ★A と B の違い（★読み違え防止）
```
★A で観測が増えたのは「Task → Runtime が流れた」からではない。★投入そのものが inspection を走らせるからである
   証拠: OBS-00967〜00970 は ★run_next を押す前の submit 応答に載っている ／ run_next は dispatched=false
★B で PLAN が動いたのは「provenance が載った task だから」である。★A の task は CREATE が古いまま ∴ 同じ結果にならない
★∴ ★既存 task（TASK-2DER-0C458F38）は、★今回の修正では救われない（★C＝CREATE の書き換えは D-148 §1-2 で却下されている）
```

---

# 5. ★私が行った操作（★全件）
```
★実装: twoder/submit.py 1箇所（7挿入1削除）
★運用: webui 再起動 1回（旧 PID 3932995 → 新 PID 3941865 / 02:21:23）
        操作者=IMPL ／ 理由=submit.py の変更を本番へ反映 ／ 既存運用（引き継ぎ §4-1）
        ★2DER の担当に数えない ／ ★run-gate は初期化された（★以後の投入で立て直るため結果に影響なし）
★投入: POST /api/submit ★A で1回（02:26:03）・★B で1回（02:30:18）。★再投入なし
★実行: POST /api/run_next ★A で1回（02:26 台）・★B で1回（02:33:38→02:34:03・24.7秒）。★他の task は押していない
★停止: ★PLAN が動いた所で止めた（SPEC §6）。★GENERATE へ進んでいない
★していないこと: ★GPU 取得・生出力・A-3・選別を触っていない ／ ★自分で :8005 を叩いていない
                  ★止まった所を直していない・迂回していない ／ ★commit していない ／ ★テストは0本（走らせていない）
```
**受理の確認**: A `receipt.last_recv_at=02:26:03.771464`（POST `02:26:03.765`）／B `02:30:18.311575`（POST `02:30:18.306`）／`recv_count 73→74→75`。

---
*IMPL → 設計/監査（写: MGR / Taka）。D-148。**修正は `twoder/submit.py` 1箇所（2 hunk・7挿入1削除・`gpu`/`nvidia` 0件）で、観測経路の knowledge_packet provenance に既存の形のまま `trace_id`／`rri_request_id`（`IR.mint`）／`rri_intent_id`（`IR.mint`）を追加（新しい ID 族・台帳・採番方式なし）。** 後方互換は13件＋`tasks` すべて不変。**A（同じ文・1回）は予告4点すべて的中**——同じ `task_id`、`events=1` のままで CREATE は作り直されず、provenance も古いまま、`run_next` は同じ3件で fail-closed。**★A で `ARUN-00966`/`OBS-00967` が生成されたのは投入時 inspection 由来であり、PLAN 由来ではない**（submit 応答に `run_next` の前から載っている）。**B（別項目・1回）は予告どおり `TASK-2DER-67FE6548` が生まれ、provenance に不足3件が載り、`run_next` で ★PLAN が動いた**（`dispatched=true`／`CREATED→READY_FOR_IMPLEMENTATION`／`plan_source=QWEN_BUILD_PLANNER`／`runtime_recovery={attempts:2, final_max_tokens:4096, RECOVERED}`／同区間の `:8005` は2件で attempts と一致）。PLAN の内容は port の話になっており **GPU 専用経路でないことの実行による1例**（ただし `cites_source_ids` は空＝観測を引用していない）。**B-4 は PLAN 由来の新規観測0、B-5 は `tasks` 157→158。SPEC §6 に従い PLAN が動いた所で停止し GENERATE へ進んでいない。commit していない。** **★B は同じ検査ではない（比較の母数が変わる）。** 次回確認箇所は **GENERATE を1回だけ押すか の1件**。*
