# 宛: Taka / 設計 / 監査 ―― 判定 **B: 部品は在るが本線から呼ばれていない（配置済み・未配線）**

**Claude はコードを書いていない。queue へ手で追加していない。`run_next` 0。UPPER_REVIEW 代行 0。実装 0。**

## 0. 判定

```
★★B. 配置済み・未配線（★確定）
★「存在する／試験に通った／commit された」を ★接続の証拠に していない。
★★根拠は ★呼び手 0（★対照つき）と ★実走記録 0、および ★正本の逐語「★配線しない」。
```

## 1. 五問への回答

### ① `TASK-2DER-2591EF9D` は COMPLETE まで到達したか → **★していない**

```
state = READY_FOR_UPPER_REVIEW（★COMPLETE ではない）
upper_reviews = ★["2der-auto-upper-review"]（★決定論の 自動PASS は 済み）
★次操作 = PROPOSE_COMPLETE ／ who = MACHINE
★かつ ★queue に 居ない（_queue()=[]）／ _last_task()=None
   ＝★★この task も ★6AC3EA20 と 同じ形で 止まった（★受領済み ∴ 自己修復が 拾わない）
```

### ② `requeue_decision` に本線上の呼び手が在るか → **★無い（0件）**

**★2DER 自身の走査器（`route_candidates_v2`）で、★同一 repo の import も含めて数えた:**

```
★requeue_decision  参照 ★0 件
★dispose_decision  参照 ★0 件
★tasks_to_enqueue  参照 ★0 件
―― 対照（★配線済みの 部品）――
★senior_review     参照 ★1 件（'self_import', 'twoder/webui.py' → 'twoder', 'senior_review'）
★disposition       参照 ★3 件（twoder/task_findings.py ／ twoder/webui.py ／ 試験）
```

**★経路表（`route_table_view()` 225行）でも 3部品とも 0件。**
**★但し経路表の静的側は同一 repo の import を外す（`self_import` 778件）∴ ★それだけでは証明にならない。**
**★上の走査器は `self_import` も含めて数えている ∴ ★これが証拠。**

**★実走記録（`observed_edges.handed_edges` 72行）でも 3部品とも 0件。**

### ③ 呼ばれるとしたらどこからか → **★該当なし（呼ばれていない）**

### ④ `_last_task()` の再取得判定が `requeue_decision` を通っているか → **★通っていない**

```
現在の 実装（manager_v0._last_task 内）:
   if not tid or tid in q or ★tid in done: continue
   st = _call("/api/state?task_id=" + tid).get("dw_state")
   if not _machine_turn(st): continue
★`requeue_decision` を import も 呼び出しも していない（★参照 0 件）。
```

### ⑤ `TASK-2DER-6AC3EA20` は自力で再取得され前進したか → **★していない**

```
state = READY_FOR_UPPER_REVIEW（★変化なし・★約50分）
upper_reviews = ★0 ／ queue に 不在 ／ _last_task() = None
```

## 2. ★なぜ「COMPLETE 待ち（C）」ではないか

**★正本が「配線しない」と明記している:**

```
`domain_dw.receive_finished()` 逐語:
 「★★線（★外部助言=★受領と 配置を 分ける）=
   ★★`twoder/` へ 置かない ／ ★commit しない ／ ★★配線しない。」
（★★『置く・commit する』は 2026-08-17 の Taka 許可で 追加された。
   ★★『配線しない』は ★そのまま 残っている）
```

**∴ COMPLETE に到達しても配線は起きない。★①の未 COMPLETE は判定を変えない。**

## 3. ★最小接続1箇所（★実装していない）

```
★★接続先 = `twoder/manager_v0.py::_last_task()` の 自己修復ループ
★★接続する物 = `twoder/requeue_decision.py::requeue_decision(
                   task_id, next_operation, in_queue, already_received)`
★返り = {"requeue", "already_received", "reason"}
★部品の 判定（★docstring 逐語・★DESIGN が 決めた もの）:
   1. task_id が 空          → False / "no_task_id"
   2. in_queue が 真          → False / "already_in_queue"
   3. next_operation が 無い   → False / "unknown_state"
   4. next_operation が NONE / BLOCKED → False / "no_machine_turn"
   5. どれでもない            → ★True
   ★`already_received` は ★判定に 使わず ★写すだけ（＝★Taka の 要件そのもの）
```

**★これ1箇所で ①〜⑤の全部が動く見込み**（★`6AC3EA20` も `2591EF9D` も同じ形で止まっているため）。
**★但し「見込み」であって実測ではない。**

## 4. ★他2部品も同型か（★確認のみ・★修正対象を広げない）

```
★tasks_to_enqueue  = ★同型（配置済み・未配線・参照 0）
★dispose_decision  = ★同型（配置済み・未配線・参照 0）
★★修正対象は ★requeue_decision の 接続 ★1箇所だけ とする（★Taka 指示どおり）。
```

## 5. ★今夜の型（★3回目）

```
「置いてある≠繋がっている」
   ①経路表の 区間が 在る≠通っている
   ②機能表に 口が 在る≠収穫が 在る
   ③★部品が 在り 試験に 通り commit されている≠呼ばれている  ← ★今回
★★機械は ★作る・試す・置く・commit する まで 出来る。★★配線だけ 誰も していない。
```

## 6. 報告

```
★判定 = ★B（配置済み・未配線）
★次の 自走開発対象 = ★`manager_v0._last_task()` ↔ `requeue_decision` の ★接続 1箇所
★Claude 実装 = 0 ／ queue 手動追加 = 0 ／ run_next = 0 ／ UPPER_REVIEW 代行 = 0
★Taka 途中裁定 = 0
```
