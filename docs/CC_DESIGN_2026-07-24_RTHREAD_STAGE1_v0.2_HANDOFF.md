# 設計/監査 → 実装: RTHREAD stage 1 v0.2 handoff（被覆テスト完成・production 変更なし）

- 発: 設計/監査（CC-α）/ 2026-07-24 / 正本: `SPEC_RTHREAD_STAGE1_v0.2.md`
- **別 repo=rri**。前提: v0.1a 配備済(commit `02bb767`・監査 CONSISTENT)。

## 依頼（テスト追加のみ・本体無改変）
1. `rri/rri/test_request_thread_stage1_cov.py` を SPEC §2 **verbatim** で新規配置（既存 `test_request_thread_stage1.py` は触らない）。
2. `python -m pytest rri/test_request_thread_stage1.py rri/test_request_thread_stage1_cov.py -q` = **11/11 green** を確認。
3. `git diff` で `rri/rri/request_thread.py` が **0 行**（production 変更ゼロ）を確認。
4. 監査ハーネス `python /home/takasan/egl/docs/audit_rthread_stage1.py` が **CONSISTENT** のままを確認。
5. `CC_IMPL_2026-07-24_RTHREAD_STAGE1_v0.2_BUILT.md` を `egl/docs` に置く。

## 拘束
- **`request_thread.py` を 1 バイトも変えない**。v0.2 は被覆テストのみ（6本は現行コードに green と設計側で実測済み）。もし green にするために本体変更が要ると判明したら **halt**（乖離台帳スキーマで報告）＝それは v0.2 の前提崩れ。
- スコープ厳守: I2 load-bearing化 / merge・split(T16/T17) / T39 re-raise は **v0.2 に含めない**（初版 rollout の stage②④・別 increment）。

## 完了後
- 設計側が再監査 → CONSISTENT → commit=Taka → DE 起票(live submit)。
