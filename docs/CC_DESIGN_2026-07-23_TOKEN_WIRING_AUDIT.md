# 設計/監査担当 → 実装担当: 配線 監査結果＋gate1b は計器欠陥（handoff signal）

- 発: CC-α / 2026-07-23
- 宛: 実装インスタンス（Monitor `b0718vzrg`）
- 対応: `CC_IMPL_2026-07-23_TOKEN_WIRING_BUILT.md`

## 配線 監査 = CONSISTENT

Part A（アダプタ＋既存不変＋骨格保存）/ Part B（6経路 rewire・旧直呼び無し）/ Part C（probe T1–T12）すべて green。再走行で **`gate1_token`=green（死因#4 消滅）**。`docs/CC_AUDIT_2026-07-23_TOKEN_WIRING_IMPL_CONSISTENCY.md`。**配線は達成。**

## ★ ただし「次は death#2」は保留 — gate1b は計器欠陥（族E）

再走行の残 DIRECT `gate1b_ts` を精査した結果、**これは実欠陥ではなく probe の SPEC 逸脱**でした：

- SPEC の gate1b ＝「**実 mint 経路 `mint_token` を2回**通し approval_id 相異」。
- 実装 `_gate1b_ts`（`conformance_probe.py:229-238`）＝ `grant_approval` を**同一引数で直呼び**（`mint = bind_real(…)` を取得するが**未使用**）。
- 検証（実行済）: `mint_token(attempt=1/2)` → approval_id **相異** ＝ **death#2 は実経路で CLOSED**。`grant_approval` 同一引数2回が同一なのは sha1 決定論の自明。

## 次工程（修正の的）

- ❌ `generate_via_runner.py:45` の ts 撤去（death#2 修正）は**不要**。
- ✅ **`probe/conformance_probe.py` の `_gate1b_ts` を SPEC 準拠（`mint_token` を attempt 違いで2回）に修正** → `gate1b` green → 再走行で DIRECT 無し → ★3(B) DONE。
- この修正 spec は CC-α が起草予定（Taka 認識合わせ後）。**それまで待機で正常。**

commit=Taka（配線 M7ファイル＋token-gate `?? approval_registry.py`・tests）。
