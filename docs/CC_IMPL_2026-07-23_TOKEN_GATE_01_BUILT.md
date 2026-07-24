# 実装担当 → 設計/監査担当: TOKEN-GATE-01 実装完了（BUILT・handoff signal）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-23
- 対応: `SPEC_TOKEN_GATE_01.md`（★3(B)・死因#4 の DIRECT 破断 `gate1_token` を直す）

## 成果物（working tree・未commit）

- `twoder/approval_registry.py`（骨格 FILL×3 実装。`validate_approval_by_id`/`_load_grant`/`consume_approval_by_id`）
- `twoder/tests/test_approval_registry.py`（発注側同梱を verbatim 配置）

## 検証（決定論）

- **§3 不変テスト 7/7 green**（binding_is_real / granted_id_passes / unknown_rejected / dict_rejected / action_from_ledger / task_scope_from_ledger / consumed_rejected）
- **冪等**: 隔離を替えて 2 回走行 → 7/7 再現
- 骨格保存 `verify_skeleton_preserved` = True（固定3区間 byte 一致）
- **実 DS 台帳 無改変**: 走行前後で `ds_events.jsonl` 同一（`*_DATA_DIR` を throwaway 隔離）
- **CC-α 整合監査 = CONSISTENT**（C1–C4 green・7/7、ハーネスも DS/EGL/DW/RRI 隔離+TMPDIR）

## 設計反映（要点）

- `validate_approval_by_id(approval_id: str, ...)`: **str のみ受理**、dict は自己申告として拒否（族C）。台帳 GRANT（`_AUTH._ds()` の `AUTHORITY_APPROVAL_GRANT` 事象）を引き、action_type/task_id/operation_class を**台帳値**と照合。`_AUTH.approval_consumed` で CONSUMED 済みを single_use 無関係に拒否。
- `_AUTH` は骨格 import 束縛（`from twoder import authority as _AUTH`）で `test_authority_binding_is_real` を満たす。既存 `authority.validate_approval` は無改変。

## 注意（発注側 test infra）

`test_approval_registry.py` は固定 ts/task で **approval_id が決定論的**なため、**台帳を隔離せず走らせると非冪等**（消費済みが持ち越し `consumed` テストが赤化）。現状は私の走行も CC-α 監査も `*_DATA_DIR` 隔離で回避済み。casual run を堅牢化するなら **conftest（発注側）で自動隔離**を推奨（実装担当は tests/conftest を書かない規律のため flag のみ）。

## ハンドオフ

- 次: **commit=Taka**（人間の扉2枚目、現状 `?? approval_registry.py` `?? tests/test_approval_registry.py`）。
- 本仕様の DONE は **BUILT**。seam 配線（`validate_approval` → `validate_approval_by_id`）は §5 範囲外。配線効果（gate1 green 化・CONDITIONAL 確定/消滅）は **CONFORMANCE_PROBE 再走行**が測る。
