# 実装担当 → 設計/監査担当: RTHREAD stage 2a 実装完了（accounts 機械核・BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `SPEC_RTHREAD_STAGE2a_v0.1.md` / `CC_DESIGN_2026-07-24_RTHREAD_STAGE2a_HANDOFF.md`
- 別 repo=rri。前提: stage1 v0.2（commit `a4e97d6`）配備済。

## 成果物（working tree・未commit）

- `rri/rri/request_thread.py`（**§1 の変更のみ**・他関数/定数/例外は byte 不変）:
  - (0) 新例外 `RThreadChartUnavailable(RThreadError)`
  - (1) chart 定数 `_CHART`（`RTHREAD_CHART` env）＋ `_load_chart()`（fail-closed・不在/破損は `RThreadChartUnavailable`）
  - (2) `raise_question` 署名 `account_id=UNCLASSIFIED`（旧 `"DEFAULT"` 廃止）＋ **chart 検証**（off-chart は `ValueError`・D2）
  - (3) `project` の `suspense_balance` を **「UNCLASSIFIED かつ未dispose の問い数」** に再定義（決着可能・恒等式でない・D1）。他フィールドは byte 同一
  - (4) `check_account_conservation(projection, valid_accounts)` 新設（off-chart/総和不一致で `RThreadConservationError`・D3 load-bearing）
  - (5) `advance_state` RESOLVED guard に **machine 検査追加**（`suspense_balance!=0` で阻却＝self-report を信じない G-1 修理／`check_account_conservation` を append 前に通す）
- テスト: `test_request_thread_stage1.py`・`_cov.py` を移行（`_fresh` に fixture chart `ACCT_TEST_A/B`＋RESOLVED 経路 account を `ACCT_TEST_A` へ。**契約の述語は不変**）。`test_request_thread_stage2a.py`（SPEC §3 verbatim・6本）を新規配置。

## 検証（決定論・隔離下）

- **全 17/17 green**（stage1 5 ＋ cov 6 ＋ stage2a 6）。移行後も stage1/cov の述語不変で green。
- **mutation check（G-T1）実証**: D1 revert（suspense を raise数へ）→ `test_suspense_settles` 赤 ／ D3 revert（off-chart 検査除去）→ `test_account_conservation_load_bearing` 赤。復元で 17/17 green。両テストは load-bearing。
- **非FILL/他関数 byte 不変**（変更は §1 の4点＋例外＋chart ローダに限定・各置換 count==1 検証）。
- **imagined production account を導入していない**（2a の名は UNCLASSIFIED と純テスト fixture `ACCT_TEST_A/B` のみ。実 chart は stage2b）。スコープ厳守（MINING/split・merge/昇格・統計は未着手）。

## 監査ハーネスについて

- handoff §20 どおり `audit_rthread_stage1.py` は `raise_question` 署名を stage1 版で照合するため A が想定内の赤になる。**ハーネスの stage2a 対応更新は設計側（CC-α）担当**なので、私は実行していません（§4 受入＝全green＋非FILL byte不変＋mutation check を満たすまで）。

## ハンドオフ

- 次: **CC 再監査（stage2a 対応ハーネスで A/B/C＋17/17＋byte不変）→ CONSISTENT → commit=Taka → DE 起票（live submit）**。
- 次工程候補: stage 2b（MINING_SPEC v0.1・実 chart 生成）。
