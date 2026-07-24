# CC 設計/監査 → 実装: RTHREAD stage 1 v0.1a 再監査 = CONSISTENT

- 発: 設計/監査（CC-α）/ 2026-07-24 / 対応: `CC_IMPL_2026-07-24_RTHREAD_STAGE1_v0.1a_BUILT.md`
- ハーネス: `egl/docs/audit_rthread_stage1.py`（決定論・セルフテスト付き）

## VERDICT: **CONSISTENT**。F-1 解消。commit=Taka gate へ。

self-report を鵜呑みにせず独立再検証した（ハーネス＋直プローブ）:
- **A. 骨格保存 = PASS**（定数/例外/`_mint`/11署名 byte 一致、変更は `project()` FILL のみ）
- **B. 5/5 green**（T14 I1・T14 I2・T18a・T18b・**T14c**）
- **C. 保存則 load-bearing = PASS**。`in_flight` を独立導出（処分イベントを持たない raised 問い数）へ変更したことを直読で確認。実経路で:
  - 二重処分 → `in_flight=0` → I1 `1 != 1+1` → **HALT** ✓
  - 幻処分（未 raise の問いを処分）→ `in_flight=1` → I1 `1 != 1+1` → **HALT** ✓
  - 正常系（raised=2/resolved=1/in_flight=1）は誤検出なし ✓
- selftest C（族A回避）OK: 検出器は空振りしない。

## 設計側で実施した訂正（docstring 整合）
実装が正しく flag した「fixed 区間 docstring が旧文言のまま body と矛盾」を、**設計所有の fixed 区間訂正**として解消:
- `rri/rri/request_thread.py:195` と `SPEC_RTHREAD_STAGE1_v0.1.md:140` の project docstring を
  「`in_flight_count`=処分イベントを持たない raised 問いの数（残差でなく独立導出=I1 load-bearing）」へ更新（両者同一文言）。
- docstring は graded behavior でもオラクルでもないため author≠auditor を侵さない。矛盾 docstring を commit させないための訂正。
- 再監査後も VERDICT CONSISTENT（ハーネス A は docstring 非対象、5/5 維持）。

## 残（設計側・commit 後）
- **I2（科目次元）は stage 1 では partition 恒等式**（account 誤配属を生む経路が無い）。実害ゼロ、v0.2 で account 移動導入時に load-bearing 化。
- 残テスト T15-17 / T25 / T36-40 は v0.2 別成果物。RESOLVED→DISPATCHABLE は `__DEFERRED__`。
- **DE 起票**（F-1 検出→修理→load-bearing 化）は commit 確定後に live submit 経由（開発エビデンス登録マーカー付き）。手で ledger に書かない。

## commit 対象（Taka gate）
- `rri/rri/request_thread.py`（`??` 未追跡）
- `rri/rri/test_request_thread_stage1.py`（`??` 未追跡）
