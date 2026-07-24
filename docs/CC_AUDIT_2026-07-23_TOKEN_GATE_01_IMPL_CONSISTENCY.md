# CC 設計整合監査 — TOKEN-GATE-01 / approval_registry.py

- 監査者: Claude Code（CC-α）/ 2026-07-23
- 対象: `twoder/approval_registry.py`（59行）＋ `tests/test_approval_registry.py`
- 正本: `SPEC_TOKEN_GATE_01.md` / ハーネス: `egl/docs/audit_approval_registry.py`（DS/EGL/DW/RRI throwaway 隔離＋TMPDIR）
- **verdict: CONSISTENT**

## 監査結果

| チェック | 結果 |
|---|---|
| C1 骨格保存（bytes） | green |
| C2 §3 不変テスト 7/7 | green（passed=7 / failed=0・隔離下で実台帳無汚染） |
| C3 テスト verbatim | green |
| C4 spy 規律（spy/fake/mock 非import＋authority binding） | green |

## 設計反映（目視）

- `validate_approval_by_id`: **dict 拒否**（`:27` `isinstance(approval_id, str)`）＝族C自己申告排除／台帳 GRANT 照合（`_load_grant` → `_AUTH._ds().load_events()`）／action_type・task_id・scope・expiry 照合／**CONSUMED 拒否**（`:48` `_AUTH.approval_consumed`）。
- `_AUTH` 経由（台帳アクセスを自作しない＝導管）。既存 `authority.validate_approval` は無改変。

## claim ceiling

- **言える**: approval_registry が SPEC を反映＝**gate1_token（死因#4＝str/dict型不一致）を直す台帳照合 API が BUILT**。
- **言えない**: seam の配線（`live_worker_runtime`/`generate_via_runner` が `validate_approval` の代わりに `validate_approval_by_id` を呼ぶ変更）は §5 範囲外＝**未**。`gate1_token` の green 化と CONDITIONAL（`gate1b_ts`＝死因#2 等）の確定/消滅は**配線後の CONFORMANCE_PROBE 再走行**が測る。

## 次工程

- 人間の扉2枚目: **commit=Taka**（`?? approval_registry.py` `?? tests/`）。
- **配線 spec**（seam → `validate_approval_by_id`）を起草 → 実装 → 監査 → **CONFORMANCE_PROBE 再走行**で gate1 green・CONDITIONAL 確定/消滅 → ★3(B) 実走痕跡で DONE。
