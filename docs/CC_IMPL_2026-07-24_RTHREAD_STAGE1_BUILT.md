# 実装担当 → 設計/監査担当: RRI RTHREAD stage 1 実装完了（BUILT・handoff signal）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `SPEC_RTHREAD_STAGE1_v0.1.md`（成果物3）/ 正本 `RRI_IMPL_SPEC_v0.1.md`
- 注: **別 repo = rri**（twoder でない）。新フロー初の RRI 実装。

## 成果物（working tree・未commit）

- `rri/rri/request_thread.py`（骨格 FILL×11 実装。`_append`/`_read`/`open_thread`/`raise_question`/`dispose_question`/`present_gaps`/`human_replied`/`advance_state`/`accept_thread`/`project`/`check_conservation`）
- `rri/rri/test_request_thread_stage1.py`（発注側同梱を verbatim 配置・実装インスタンスは触っていない）

## 検証（決定論・隔離下）

- **§3 不変テスト 4/4 green**（T14 I1 処分次元・T14 I2 科目次元・T18a RESOLVED は in_flight==0 要求・T18b UNCLASSIFIED は RESOLVED 不可）
- 骨格保存 `verify_skeleton_preserved` = True（固定11区間 byte 一致。定数 TRANSITIONS/EVENT_TYPES・例外・`_mint`・docstring 不変）
- **mutation check（G-T1）実証**: 保存則を壊す2 mutation（I1=resolved 握り潰し／I2=account 二重計上）で `check_conservation` が halt する（テスト内 `pytest.raises` で確認＝空振りしない）
- 台帳隔離: テストは `RTHREAD_EVENTS` env で throwaway。実 `rri_records.jsonl`/`rthread_events.jsonl` 無改変（working tree = 新規2ファイルのみ）
- stdlib のみ import。

## 設計反映（要点）

- 複式保存則: **I1(処分次元)** `raised == resolved+open_gap+rejected+merged+in_flight`、**I2(科目次元)** `Σ per_account_balances == raised`。両方を `check_conservation` で検査、`advance_state` が STATE_ADVANCED append 前に通す。
- 出口規則: `account_id=="UNCLASSIFIED"` の問いは RESOLVED 処分不可（ValueError）。default account="DEFAULT"（RESOLVED 可）。
- RTHREAD は projection（`project` が events を畳んで DERIVED 再構成・fat record なし=#25）。sole writer / `sealed_by` は関数が刻む（G-1、caller 自己申告なし）。
- RESOLVED 遷移 guard は projection 由来（in_flight==0・全 OPEN_GAP presented・THREAD_ACCEPTED）で、guard_evidence の自己申告キーだけでは通さない。

## claim ceiling / 残

- v0.1 = 保存則核＋T14/T18 のみ。残テスト T15-17/25/36-40 は v0.2（別成果物）。RESOLVED→DISPATCHABLE は `__DEFERRED__` で後段（RThreadError）。
- 次: **CC 設計整合監査 → CONSISTENT 確定 → commit=Taka**（`?? rri/rri/request_thread.py` `?? rri/rri/test_request_thread_stage1.py`）。
