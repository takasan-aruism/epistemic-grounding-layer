# 設計担当 → 実装担当: 配線 SPEC 投下（TOKEN-WIRING・handoff signal）

- 発: CC-α / 2026-07-23
- 宛: 実装インスタンス（Monitor `b0718vzrg`）
- 正本: `SPEC_TOKEN_WIRING_v0_1.md`（Taka 裁定 B＝§9 全経路統一）

## 実装対象（3 パート）

- **Part A**: `twoder/approval_registry.py` の**末尾にアダプタ3関数を追加**（`_extract_approval_id`/`validate_by_token`/`consume_by_token`・§2 骨格 FILL×3）。**既存3関数は 1 バイトも変えない。** ＋ `tests/test_token_wiring.py`（§2 不変テスト6本・発注側同梱・worker は触らない）。
- **Part B**: 6ファイル（`live_worker_runtime`/`gate4`/`operator`/`ab_harness`/`command_surface`/`autonomous_git`）の `validate_approval`/`consume_approval` を `validate_by_token`/`consume_by_token` に置換（§3 表・各ファイルに `from twoder import approval_registry as AR`）。引数は変えない。
- **Part C**: `probe/conformance_probe.py` の `gate1`/`gate7` を新経路向けに更新（§4）。骨格（`bind_real`/`run_ladder` 等）は不変。

## 受入（§5）

- Part A: `tests/test_token_wiring.py` **6/6 green**（`test_forged_dict_rejected`・`test_dict_content_is_ignored` が族C の心臓）。既存3関数 bytes 不変。
- Part B: 既存回帰テスト（`regression/test_live_worker_runtime.py` 等）が **green 維持**（dict token 経路が台帳照合で動く）。
- Part C: **CONFORMANCE_PROBE 再走行で `gate1_token` が green**（DIRECT 破断消滅）。probe T1–T12 green 維持。

## 流れ

実装（A→B→C）→ BUILT signal 投下 → CC 監査（wiring 版の設計整合ハーネス：アダプタ骨格保存＋Part A 6/6＋既存回帰 green＋probe 再走行 gate1 green）→ commit=Taka。**投下まで待機で正常。**

※発行側（`issue_approval` の dict token）は §6 範囲外＝別途。本配線は消費側6経路のみ。
