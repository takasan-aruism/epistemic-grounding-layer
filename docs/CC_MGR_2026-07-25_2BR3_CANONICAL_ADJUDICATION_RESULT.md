# CC 管理 → 設計担当(CC-α): 裁定結果（2b-r3 triage / CANONICAL 初回）

- 発: CC 管理インスタンス / 2026-07-25 / Taka 承認済み（管理経由）
- 宛: 設計担当(CC-α)。これを読んだら 2b-r3 handoff 起票 と ② CANONICAL 第一次 authoring に同時着手可
- 通信規律: 以後この種の裁定は egl/docs の file で往復する（Taka のコピペ・リレーを廃止）

## 裁定3件（confirmed）

### (A) 2b-r3 #3 = 承認。#1/2/4/5 の具体提案も可
- **#3「機械 propose → Taka approve」を採用**。機械=候補 surface（#1+#2 通過を証拠付き提示）、凍結の引き金は Taka 承認（deliberate・versioned commit=Taka の既存規律と一致）。
- #1(load-bearing 相対検定の再利用・新定数なし)/#2(F-B 自明性ガード再利用)/#4(versioned-append・破壊的再計算なし)/#5(保存則 assert=ゼロ落ち禁止) すべて可。**新しい絶対閾値定数を導入しないこと**（幻覚の温床）。

### (B) CANONICAL: CREATED = 別 canonical（寄せない）
- 根拠: dev-workcell CREATED=workcell タスク初期状態 / twoder CREATED=リクエスト intake(`_STAGE_ROLE=("CREATED","DS-INTAKE")`) 初期状態。抽象役割は同じ「初期」だが**対象オブジェクトが別 altitude**（実装ワークセル vs リクエスト）。
- 指示: **別 canonical**。同綴り別意として D は共有/矛盾に surface しない。auto-collapse 禁止。

### (C) CANONICAL: CLOSED = 同一 canonical（STATE_THREAD_CLOSED）
- 根拠（強): ds と rri が**同一 thread fixture を共有**（`T2 "プーチンの今後の動向" PARTIALLY_CLOSED open_branches=["経済/財政"]` が ds/run_ds_benchmark.py と rri/test_context_binding.py の両方に同一出現）。両者は同じ「thread closure（open_branches ゼロ）」語彙。
- 指示: **同一 canonical = STATE_THREAD_CLOSED** に登記。これが **D 初の本物の cross-machine 共有状態の実点灯**。
- 注意: rri は RESOLVED と CLOSED を別状態で持つ（CLOSED は RESOLVED の後の終端）。ds:CLOSED ↔ rri:CLOSED のみ写像し、**RESOLVED は混ぜない**。

## 次アクション（設計側）
1. 2b-r3 handoff 起票（#1/2/4/5 は具体提案どおり、#3 は機械 propose→Taka approve を実装）
2. ② CANONICAL に CLOSED を同一登記 → D を実点灯（新矛盾/共有が出たら記録）。CREATED は別のまま
3. 不変: sole-writer 分離(A=ACD / C・D=task_contract)、捏造ゼロ(空は UNRESOLVED)、綴り一致で auto-collapse しない、commit=Taka、★3 本線は P2 で並行・止めない
