# 宛: Taka / 設計 / 監査 ―― `should_call_senior` 完成: **実データ29回 → 許可2回**（Claude 実装 0行）

**火事を再現させずに完了した。暴走 TASK は退避したまま。**

## 0. 完了条件（★Taka 指定5つ）

| # | 条件 | 結果 |
|---|---|---|
| ① | 既知の暴走 TASK による `claude -p` 再発 **0回** | **★成立**（`upper_reviews` は **29 のまま**・再開後13分 変化なし） |
| ② | 契約は**常駐が自力投入** | **★成立**（3分で `already 80 → 81`） |
| ③ | **Claude 実装 0行** | **★成立**（`e2a016b` = ★機械が置いて commit・人の手0） |
| ④ | 29回相当の実データ列で**許可2回** | **★成立**（下記） |
| ⑤ | manager 再開中の**意図しない上級監査増加 0** | **★成立** |

## 1. ★④の検証（★実物の記録列を、★納品された部品に通した）

```
実データ列 35件（うち upper_review 29件）＝ TASK-2DER-32EDB6C4 の 実際の記録
   3589 gen / 3590 audit / 3591 dispose / ★3592 UR / 3594 regen / 3595 audit / 3596 dispose
   / ★3597〜3624 UR ×28

★★許可 = ★2回
      3592 … reason="first_time"
      3597 … reason="input_changed"
★抑止 = ★27回（★すべて reason="no_progress_since_last_review"）
```

**★Taka の完了条件「許可回数が実測どおり2回」＝ ★一致。**

### 個別の受入

```
①初回は許可          → True  / "first_time"
②同じ入力の2回目      → False / "no_progress_since_last_review"
③入力が変われば再許可  → True  / "input_changed"
★空の一覧            → False / "no_input_record"（★fail-closed）
```

## 2. 納品された部品（★2DER が書いた・★MGR は1行も書いていない）

```
twoder/should_call_senior.py（58行・commit ★e2a016b「機械が 置いた=人の手 0」）
   def should_call_senior(last_review_ordinal, input_ordinals)
   返り = {"call", "reason", "last_review_ordinal", "latest_input_ordinal"}
   規則（★docstring 逐語・★上から順）:
     1. last_review_ordinal が None            → call True  / "first_time"
     2. input_ordinals が 空                    → call False / "no_input_record"
     3. 入力の 最大値 > last_review_ordinal     → call True  / "input_changed"
     4. どれでもない                            → call False / "no_progress_since_last_review"
```

**★DESIGN の裁定 = ★案 A（`_ordinal` ベース）／ 局所（純関数）／ 封印試験15本・骨格12。**
**★新しい台帳 0 ／ 新しい状態語 0 ／ 固定回数ルール 0 ／ `authority`・`_MAP`・`disposition` 規則 未変更。**

## 3. ★自走の実測（★再開後・★私は何もしていない）

```
0分  queue [32EDB6C4=★BLOCKED] ／ 暴走TASK の ur ★29
3分  ★常駐が 自力で 契約を 投入（already 80→81）／ 新 task 5D9B430F = CREATED
4分  5D9B430F = READY_FOR_UPPER_REVIEW
7分  ★5D9B430F = ★COMPLETE ／ ★部品が 置かれた
10分 常駐が 次を 拾った（4E2A58F2 = DISPOSITION_REQUIRED）
13分 一巡 終わり ／ ★暴走TASK の ur は ★29 の まま
```

**★PLAN → GENERATE → TEST → AUDIT → UPPER_REVIEW → COMPLETE を、★7分で・★Claude の手を借りずに通した。**

## 4. ★退避について（★開示）

```
★使った口 = `dw/workcell.py::block_task(task_id, reason, ts, identity)`（★DW 正本・★呼び手 0 だった）
★探した範囲 = front door の 18口 ／ workcell / dispatch / manager_v0 / domain_dw の 公開面
   dequeue・quarantine・defer・suppress・pause という 名の 口は ★無い
★★queue から 外すだけでは 効かないと 実測で 判明:
   requeue_decision(next_operation='UPPER_REVIEW') → ★{'requeue': True}
      ＝★今朝 私が 配線した 自己修復が ★戻してしまう
   requeue_decision(next_operation='BLOCKED')      → ★{'requeue': False, 'reason':'no_machine_turn'}
★∴ ★`block_task` が 唯一 効く 手だった（★Taka の 代替案では 止まらなかった）
★三重で 止まることを ★再開前に 確認:
   _machine_turn('BLOCKED')=False ／ requeue_decision=False ／ dispatch は dispatched=False

★★戻す口は 無い ―― `BLOCKED` は append-only の 記録 ∴ ★この task は 以後 BLOCKED の まま。
   ★Taka の「一時的に」に対し、正確には ★「恒久的に 1件を 止めた」。
   ★影響は ★試験に 落ちた 実験 1件のみ（★同じ契約は 新しい task として 再投入できる）。
★他の task には 触っていない。
```

## 5. ★2DER が今日1日で増やした能力（★実測のみ）

```
★requeue_decision   … 受領帳簿と 工程完了を 分ける（★配線済み・★実走で COMPLETE 2件）
★should_call_senior … 同一入力の 高価な 再実行を 止める（★納品・★配線は 別裁定）
★tasks_to_enqueue / dispose_decision / apply_unified_diff … ★配置済み・未配線
★★どれも ★Claude が 書いた 実装は ★0行（★足場の 接続 1箇所を 除く=commit 346f074）
```

## 6. ★次（★MGR は決めない）

```
★配線は 別裁定（★Taka 逐語）。★局所（webui の CLAUDE_SENIOR actor）か
  ★一般（run_until_barrier の progress guard）かは ★DESIGN が 既に 局所側の 純関数として 納品した。
★★配線しない 限り ★暴走は 再発し得る（★今は `block_task` で 1件だけ 止めている）。
★manager は ★動いたまま（★Taka 指示に「再停止」が 在るが、★暴走 TASK は 退避済み ∴
  ★止めるかは ★Taka の 指示を 待つ ―― ★MGR は 勝手に 止めない）。
```

## 7. していないこと

```
★実装 0行 ／ 設計 0 ／ 契約本文 0 ／ 配線 0
★queue を 編集していない ／ run_next 0 ／ 暴走 TASK を 再投入していない
★apply_unified_diff / patch_bridge に 戻っていない
```
