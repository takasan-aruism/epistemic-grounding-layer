# CC-α → 実装担当: RTHREAD stage1 成果物3 投下（handoff signal）

- 発: CC-α / 2026-07-24
- 宛: 実装インスタンス（Monitor `b0718vzrg`）
- 正本: `SPEC_RTHREAD_STAGE1_v0.1.md` ＋ `RRI_IMPL_SPEC_v0.1.md`（複式保存則 I1/I2 は Taka 訂正 2026-07-24）

## 実装対象（**別 repo = rri**・twoder ではない）

- `rri/rri/request_thread.py`（§2 骨格の `<<<FILL>>>`×11 を実装。定数 TRANSITIONS/EVENT_TYPES・例外・`_mint`・docstring は 1 バイト不変）
- `rri/rri/test_request_thread_stage1.py`（§3 発注側同梱を **verbatim 配置**・触らない）
- event stream `rri/rri/rthread_events.jsonl`（**追跡下**・裁定21 達成前提）

## 受入（§4）

- `test_request_thread_stage1.py` **4/4 green**（T14 I1・T14 I2・T18a in_flight==0・T18b UNCLASSIFIED-RESOLVED 不可）
- 骨格 FILL 以外 bytes 不変。**mutation check（G-T1）は T14 内で実証**（resolved 握り潰し→halt / account 二重計上→halt の両方）
- 複式: I1 `raised == resolved+open_gap+rejected+merged+in_flight_count` / I2 `Σ per_account == raised`

## 流れ

実装 → 4/4 green → BUILT signal → CC 監査（4/4＋mutation halt＋骨格保存）→ commit=Taka。

## 要 Taka レビュー（着手は妨げない）

- `ADJUDICATION_SENSITIVE: 16`（UNCLASSIFIED 出口 = OPEN_GAP/REJECTED/MERGED_INTO のみ・RESOLVED 不可）
- account_id **default=`DEFAULT`**（stage1 で RESOLVED を可能にするため。UNCLASSIFIED は分類保留特殊値）＝ CC-α の設計判断
