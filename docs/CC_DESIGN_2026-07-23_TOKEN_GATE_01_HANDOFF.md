# 設計担当 → 実装担当: CONFORMANCE_PROBE 監査PASS ＋ 3B TOKEN-GATE-01 投下（handoff signal）

- 発: 設計/監査担当 CC-α / 2026-07-23
- 宛: 実装インスタンス（Monitor `b0718vzrg`）

## CONFORMANCE_PROBE（★3(A)）— 完了

- 設計整合監査 = **CONSISTENT**（§5 10/10・骨格保存/verbatim/spy規律 green）。`docs/CC_AUDIT_2026-07-23_CONFORMANCE_PROBE_IMPL_CONSISTENCY.md`
- **`BREAKAGE_LIST` 走行済**（CC が実行・TMPDIR 回避・9 records）＝ ★3(A) 実走痕跡。`docs/BREAKAGE_LIST_2026-07-23.jsonl`
- commit=Taka 待ち（`?? probe/` `?? tests/`）。
- ※監査中に `/tmp` の 2,100万 `tmp*.jsonl`（ext4 htree 上限で `mkdir` 不能）を発見・回避・掃除済。源＝テストの `mkstemp(suffix=".jsonl")` 後始末漏れ（別件・恒久対処キュー）。

## 次 spec = ★3(B) TOKEN-GATE-01（投下済）

- **`SPEC_TOKEN_GATE_01.md` 投下。実装対象 = `twoder/approval_registry.py` ＋ `tests/test_approval_registry.py`。**
- 直す破断: BREAKAGE_LIST の**唯一の DIRECT ＝ `gate1_token`（死因#4＝token が str・`validate_approval` は dict 要求）**。
- `validate_approval_by_id(approval_id: str, ...)` が **authority 台帳の GRANT を引いて照合**・**dict は拒否（族C＝自己申告排除）**・CONSUMED 済み拒否。骨格 FILL×3・不変テスト7本（発注側同梱・worker は触らない）。
- **seam の配線**（`live_worker_runtime`/`generate_via_runner` が `validate_approval` の代わりに `validate_approval_by_id` を呼ぶ変更）は §5 範囲外＝本仕様 DONE は BUILT。配線効果（gate1 の green 化、CONDITIONAL の確定/消滅）は **CONFORMANCE_PROBE 再走行**が測る。

実装 → §3 7/7 green → BUILT signal 投下 → CC 監査（`approval_registry` 版の設計整合ハーネスを用意）→ commit=Taka。

---

## ✅ 監査完了（追記 2026-07-23）

`approval_registry.py` 監査 = **CONSISTENT**（§3 7/7・骨格保存・verbatim・spy 規律 green、`docs/CC_AUDIT_2026-07-23_TOKEN_GATE_01_IMPL_CONSISTENCY.md`）。**BUILT 到達。** commit=Taka（`?? approval_registry.py` `?? tests/`）。

**次工程＝配線（CC-α が設計中・投下まで待機で正常）:** `live_worker_runtime.py:94` の `validate_approval`→`validate_approval_by_id`。ただし呼出元が dict/str 混在（`gate4`/`operator`/`autonomous_git`/`ab_harness`/`command_surface` が既存 dict token）ゆえ単純置換不可。配線範囲（最小1経路 vs §9 全経路統一）は Taka 裁定を仰いでから spec 化します。

---

## ✅ Taka 裁定: B（§9 全経路統一）— 設計確定（追記 2026-07-23）

調査完了：6経路とも **dict の中身は未使用**（validate/consume の運搬のみ）＝低リスク。consume の対＝`gate4`/`live_worker_runtime`/`operator`/`ab_harness`/`command_surface` の5経路。発行源＝`command_surface.issue_approval`（dict）／`generate_via_runner.mint_token`（str）。

**設計＝アダプタ方式:**
- `approval_registry` に `_extract_id`／`validate_by_token(token_or_id, ...)`／`consume_by_token(token_or_id, ts)` を追加（dict でも str でも approval_id を抜いて `validate_approval_by_id`/`consume_approval_by_id` に委譲。**dict の中身は捨てる＝族C 排除と両立、後方互換**）。
- 6経路の `validate_approval`/`consume_approval` を `validate_by_token`/`consume_by_token` に統一。
- 発行側（`issue_approval`）は別途（消費側がアダプタで吸収するため後回し可）。
- probe `gate1`/`gate7` を新経路向けに更新。

**CC-α が配線 SPEC を起草中（投下まで待機で正常）。** 既存6ファイルの修正主体なので SPEC 形式（修正指示＋回帰テスト）を含めて設計します。


