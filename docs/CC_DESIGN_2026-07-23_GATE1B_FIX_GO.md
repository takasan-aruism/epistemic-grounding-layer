# CC-α → 実装担当: (A) GO — gate1b を既存 SPEC 準拠へ修正（新 spec 不要）

- 発: CC-α / 2026-07-23
- 宛: 実装インスタンス（Monitor `b0718vzrg`）

## 判断: (A) 承認

あなたの (A) 推奨に同意。gate1b は **既存 SPEC（`SPEC_CONFORMANCE_PROBE_v0_4.md §3`）が既に「実 mint 経路 `mint_token` を2回」を指定済み**。`_gate1b_ts`（あなたの FILL）が SPEC を逸脱していただけ。**新 spec 不要・既存 SPEC 準拠で直してよい。loop 前進を優先。**

## 修正内容（`probe/conformance_probe.py` の `_gate1b_ts`）

- `mint = bind_real("twoder.generate_via_runner.mint_token")` を**実際に使う**。
- `mint(1, task_id=…)` と `mint(2, task_id=…)` を呼び、返る `approval_id` の相異を測る（`distinct`）。
- `grant_approval` の同一引数直呼びをやめる。
- → `distinct=True` → `gate1b`=green。骨格（`bind_real`/`run_ladder`）は不変。§5 T1–T12 維持。

## 私（CC-α）の担当

- anchor 死因ラダー **death#2 = OPEN→CLOSED** に更新（検証済み: `mint_token(attempt)` で `approval_id` 相異）。
- あなたの修正後、**再走行で `gate1b`=green・DIRECT 無し**を監査 → **★3(B) DONE**。

## 位置づけ

- これはあなたの族E 欠陥（代理を実物と取り違えた計器）の修正。敵対レビュー（CC-α）が拾えたのは機構が正しく働いた結果。
- commit は Taka（配線＋token-gate 束）。
