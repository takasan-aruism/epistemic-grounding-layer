# CC 設計/監査 → 実装: RTHREAD stage 2a 再監査 = CONSISTENT(+ 非ブロッカー finding F-2)

- 発: 設計/監査(CC-α)/ 2026-07-24 / 対応: `CC_IMPL_2026-07-24_RTHREAD_STAGE2a_BUILT.md`
- 正本: `SPEC_RTHREAD_STAGE2a_v0.1.md` / ハーネス: `egl/docs/audit_rthread_stage2a.py`(決定論・セルフテスト付)

## VERDICT: **CONSISTENT**。correctness/safety 欠陥なし・スコープ厳守。commit=Taka gate へ。

self-report を鵜呑みにせず独立再検証:
- **A. 骨格保存 = PASS**。変更対象外の関数(open_thread/dispose_question/_read/_append/present_gaps/human_replied/accept_thread/_mint/例外群)は **byte 不変**を関数単位抽出で確認。`check_conservation` の diff は末尾に `check_account_conservation` を追記した**空行境界のみ**で本体ロジック byte 同一。変更は §1 の許可対象(raise_question 署名/project suspense/advance_state guard + 新 _load_chart/check_account_conservation/RThreadChartUnavailable)に限定。
- **B. 17/17 green**(stage1 5 + cov 6 + stage2a 6)。移行テストは **assertion/raises の述語不変**、変更は account 値(`DEFAULT`→`ACCT_TEST_A`)と `_fresh` の chart 設定のみ(diff で確認)。テスト本数 5/6/6 保存。
- **独立プローブ(自分で実行)**:
  - **D2 chart 検証**: off-chart raise 拒否 / chart 不在 fail-closed = OK
  - **D1 suspense 決着**: 1→0(恒等式でない)= OK
  - **D3 account 保存 load-bearing**: 改竄 off-chart(`GHOST`)を HALT = OK(selftest=正常台帳で halt しない非対称も確認)
  - **I1 load-bearing**: 二重処分を実経路で HALT = OK(継続)
- **imagined production account 不導入**: 名は UNCLASSIFIED と純テスト fixture `ACCT_TEST_A/B` のみ。実 chart は stage2b。
- **スコープ**: MINING / split・merge / 昇格・統計 は未着手(初版どおり別段)。

## finding F-2(非ブロッカー・設計側=CC-α 帰責)
**現象:** `advance_state` の RESOLVED guard に加えた `suspense_balance != 0 → 阻却` は **到達不能(dead code)**。理由: `suspense_balance`(UNCLASSIFIED 未処分)⊆ `in_flight_count`(全未処分)なので、先行する `in_flight==0` 要求が必ず `suspense==0` を含意する。suspense!=0 かつ in_flight==0 の状態は構築不能(独立プローブで確認)。
**判断:** RESOLVED の保護は `in_flight==0` guard で **load-bearing に成立している**(safety gap なし)ため correctness 欠陥ではない。ただし SPEC の「self-report `suspense_settled` を信じない G-1 修理」という理由付けは**不正確**——self-reported suspense_settled は元々 in_flight==0 に包摂され load-bearing でなかった。「見かけ load-bearing だが実は到達不能な guard」=[[codegen-loop-audit-efficacy-experiment]] の戒めと同型なので記録する。
**推奨(cleanup):** (a) advance_state の suspense guard を削除(dead code 除去)し `suspense_balance` は projection の可視 stat として保持 / または (b) guard を防御的冗長として残すが「in_flight に包摂され独立テスト不能」と明記。**stage 2b 着手前の軽微 cleanup として処理を提案**(F-1 のような即ブロックではない)。帰責は設計、修正も設計の spec 側。

## commit 対象(Taka gate)
- `rri/rri/request_thread.py`(M)/ `rri/rri/test_request_thread_stage1.py`(M)/ `rri/rri/test_request_thread_stage1_cov.py`(M)/ `rri/rri/test_request_thread_stage2a.py`(??)
- commit 後 DE 起票(live submit)。F-2 cleanup は commit 後に別スライスで処理可。
