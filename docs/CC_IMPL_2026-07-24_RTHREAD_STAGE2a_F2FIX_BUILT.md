# 実装担当 → 設計/監査担当: stage 2a F-2 cleanup 完了（冗長 suspense guard 除去・BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `CC_DESIGN_2026-07-24_RTHREAD_STAGE2a_F2_FIX_HANDOFF.md`
- 別 repo=rri。前提: stage2a 配備済（commit `154be50`）。本 fix はその上の差分。

## 変更（handoff §依頼の2点に厳密に限定）

1. `advance_state` の RESOLVED guard から **`suspense_balance != 0` 分岐のみ削除**（到達不能 dead code。`suspense ⊆ in_flight` で `in_flight==0` に包摂）。**`check_account_conservation(proj, _load_chart()[1])` の呼出は残置**（account 保存は load-bearing）。
2. `advance_state` docstring を訂正: 「suspense 決着は in_flight==0 に包摂される(独立 guard 不要=F-2)。account 保存(check_account_conservation)を append 前に検査。」
3. `project` の `suspense_balance`（可視 stat）は**不変**。他関数・定数・例外・テストは無改変。

## 検証

- `git diff rri/request_thread.py` = **2 insertions / 3 deletions**（guard 分岐削除 + docstring 訂正のみ）。
- **17/17 green のまま**（dead code 除去ゆえ挙動不変。suspense guard を刺すテストは存在しない＝到達不能だったため）。
- 監査ハーネス `audit_rthread_stage2a.py` = **VERDICT: CONSISTENT**（A 骨格保存 / B 17/17 / C1 I1 / C2 account / D1 suspense決着 / D2 chart、全 PASS）。
  - ※ハーネス末尾の F-2 注記はハーネス内ハードコード文字列で、本体はもう dead guard を持たない。**注記除去は handoff §18 どおり設計側（CC-α）担当**。

## ハンドオフ

- 次: **CC 再監査（17/17 + guard 除去 + 他 byte 不変 + ハーネス F-2 注記除去）→ CONSISTENT → commit=Taka → DE 起票（live submit）**。
- 次工程候補: stage 2b（MINING_SPEC v0.1・実 chart 生成）。
