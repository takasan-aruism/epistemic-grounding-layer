# 宛: Taka / 設計 / 監査 ―― 再取得されない理由: **③ done/received 扱い（★確定）**

**runs/manager_done_index.json を直接横読みしていない。既存 API から取得した。修正に入っていない。**

## 0. 結論

```
★★原因 = ③ done / received 扱い（★確定・★推定ではない）
★TASK-2DER-6AC3EA20 は ★manager の 帳簿で「受領済み」に なっており、
  ★自己修復（`_last_task()`）の 除外条件 `tid in done` に 当たって ★拾われない。
```

## 1. 三条件の判定（★すべて正規面から）

| # | 条件 | 判定 | 出所 |
|---|---|---|---|
| ① | queue 在籍 | **★該当しない** | `manager_v0._queue()` = `[]` |
| ② | `_machine_turn(state)` | **★該当しない** | `manager_v0._machine_turn("READY_FOR_UPPER_REVIEW")` = **True**（★手番は在る） |
| ③ | done / received 扱い | **★★該当する** | 下記 |

### ③ の根拠（★既存 API・★横読みではない）

**取得口 = `GET /api/control?include=observed_edges` の `observed_edges.auto_total`**
（`webui.py:1213-1219` が組み立てる欄。★front door の18口の1つ・★新しい口を作っていない）

```
auto_total: submitted = ★59 ／ received = ★37
received_rows（末尾10件）に ★★在る:
   {"task_id": ★"TASK-2DER-6AC3EA20", "length": 4673,
    "sha": "0796d3a7e32b9b52273c25891aa806d2bb99a6ca4efb5fa1fe2647cde3be58da", "at": ".../runs/re…"}
   {"task_id": ★"TASK-2DER-4E2A58F2", "length": 1935,
    "sha": "fe81f28f3c06f1c659b4a425f714403789e02bf407f7201de9f8e741df6a26c6", ...}
submitted_rows にも 両方 在る
   TASK-2DER-6AC3EA20 = CC_DESIGN_2026-08-19_CONTRACT_DISPOSE_DECISION.md
   TASK-2DER-4E2A58F2 = CC_DESIGN_2026-08-19_CONTRACT_TASKS_TO_ENQUEUE.md
```

**★2件とも `received` に在る。∴ `tid in done` が真 ∴ 自己修復が `continue` で飛ばす。**

**★前回 UNKNOWN と書いた欄が、★既存の口で埋まった。**（★「無い」の前に探す範囲を広げたら在った）

## 2. manager の done 判定は何を意味するか（★既存正本から）

**`domain_dw.receive_finished()` の逐語:**

```
「★終わった 案件の 成果物を ★受け取り ★同じ物か 確かめ ★残す
  （★★置く・繋ぐ・使う は しない）。
 ★判定=★2DER が書いた `twoder/check_artifact.py`
  （★★中身と 記録の sha が 一致するか ★だけ）。
 ★★線（★外部助言=★受領と 配置を 分ける）=
  ★★`twoder/` へ 置かない ／ ★commit しない ／ ★配線しない。」
```

**実装が受領と判定する条件（★2つ）:**

```
r["receivable"]（★check_artifact の sha 一致） ★かつ tr["status"] == "PASSED"
   → _append_index("received", item)
   → _queue_write(…)   # ★受領が 済んだ=★並びから 落とす
```

### 三つの問いへの答え

| 問い | 答え |
|---|---|
| **manager の done 判定は何を意味するか** | **★「成果物を受け取った」**（★sha 一致 ＋ 試験 PASSED）。★逐語で「置く・繋ぐ・使うはしない」と明示 |
| **DW の COMPLETE と同じ意味か** | **★★違う。** `receive_finished` は **`dw_state` を条件に使っていない**（★引いてはいるが受領判定には使わない）。DW の COMPLETE は `PROPOSE_COMPLETE` の門を通った状態 |
| **artifact 受領だけで done になるか** | **★なる**（＋試験 PASSED）。★DW が どの state でも 受領は 成立し得る |

## 3. ★食い違いの形（★どちらも壊れていない）

```
manager の 帳簿  : 「成果物は 受け取った」= ★done（★受領の 意味）
DW の 正本      : 「READY_FOR_UPPER_REVIEW」= ★途中（★工程の 意味）

★どちらも 自分の 定義では 正しい。
★★問題は ★自己修復が ★『受領済み』を ★『工程も 終わった』として 使っていること。
   `_last_task()` の 除外: `if not tid or tid in q or tid in done: continue`
   ＝★受領の 帳簿を ★工程の 判定に 流用している。
★★これは ★繰り返し出ている型「鍵が違う」。
```

**★2件とも同じ形で塞がっている**（4E2A58F2 / 6AC3EA20 ―― ★どちらも成果物受領済み・DW は途中）。

## 4. ★完了条件に対する結果

```
★「なぜ再取得されないか」を ★1つの既存条件まで 確定する = ★★成立
   → ★③ `tid in done`（`manager_v0._last_task()` の 自己修復ループ内）
★修正に 入っていない。
```

## 5. していないこと

```
★runs/manager_done_index.json を 直接 横読みしていない（★既存 API から 取得）
★新しい queue / 新しい 状態 / 新しい 判断規則 0
★task を 手で queue へ 戻していない ／ run_next 0 ／ UPPER_REVIEW を 代行していない
★修正していない
```
