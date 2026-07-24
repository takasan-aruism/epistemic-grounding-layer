# 設計/監査 → 実装: stage 2a finding F-2 cleanup(冗長 suspense guard 除去)

- 発: 設計/監査(CC-α)/ 2026-07-24 / 対応: `CC_AUDIT_2026-07-24_RTHREAD_STAGE2a_CONSISTENT.md` の F-2
- 別 repo=rri。前提: stage2a 配備済(commit `154be50`)。

## finding(再掲)
`advance_state` の RESOLVED guard に加えた `suspense_balance != 0 → 阻却` は **到達不能(dead code)**。
`suspense_balance`(UNCLASSIFIED 未処分)⊆ `in_flight_count`(全未処分)ゆえ、先行する `in_flight==0` 要求が必ず `suspense==0` を含意する。「見かけ load-bearing だが不動作な guard」を残さない。

## 依頼(最小変更)
1. `request_thread.py` の `advance_state` から **`suspense_balance != 0` 分岐のみ削除**(`check_account_conservation(proj, _load_chart()[1])` の呼出は **残す**=account 保存は load-bearing)。
2. `advance_state` の docstring から suspense に関する「self-report を信じない G-1 修理」相当の文言を、**「suspense 決着は in_flight==0 に包摂される(独立 guard 不要)。account 保存のみ append 前に検査」** へ訂正。
3. `project` の `suspense_balance`(可視 stat)は **不変**(残す)。他関数・定数・例外・テストは無改変。

## 受入
- **17/17 green のまま**(suspense guard を刺すテストは無い=到達不能ゆえ、削除で挙動不変)。
- `git diff` の request_thread.py 変更は §依頼の2点(guard 分岐削除 + docstring 訂正)に限定・byte 精査。
- 監査ハーネス `audit_rthread_stage2a.py` は VERDICT=CONSISTENT のまま(A/B/C/D 不変。設計側で F-2 注記を除去更新する)。

## 完了後
- `CC_IMPL_2026-07-24_RTHREAD_STAGE2a_F2FIX_BUILT.md` を置く → 設計側が再監査(17/17 + guard 除去 + 他 byte 不変)→ CONSISTENT → commit=Taka → DE 起票。
- ハーネスの F-2 注記除去は設計側(CC-α)が再監査時に実施。
