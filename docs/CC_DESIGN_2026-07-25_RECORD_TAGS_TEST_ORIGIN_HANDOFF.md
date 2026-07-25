# 設計/監査 → 実装: test-origin タグ台帳（egl 側 overlay・rri 無改変）HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用
- 正本: `CC_MGR_2026-07-25_TEST_TAG_SCOPE_ADJRESULT.md`（(Y) egl タグ台帳・rri無改変・登記必須・overlay）+ 本 handoff
- 位置づけ: P2（bounded・帳簿の弧の後始末）。★3 本線は止めない。scope creep 禁止。

## 0. 絶対規律
- **rri_records.jsonl は無改変**（append-only provenance 源・非侵入原則）。読むだけ。
- タグは **overlay**（分離・除外・物理排除しない）。後から include/除外/重み付けを選べる状態にするだけ。
- **判定不能は tag しない**（unique content かつマーカーなし＝未分類のまま・捏造ゼロ）。

## 1. 新台帳 `structure/RECORD_TAGS.jsonl`（決定論生成）
- 生成器 `structure/s_record_tags.py`。`/home/takasan/rri/rri_records.jsonl` を read-only 走査。
- 1 行 = `{rri_record_id, origin:"test", reason, criterion}`（tag された record のみ・参照リンク＝rri_record_id）。
- **決定論タグ基準（この2つのみ）**:
  1. **explicit_test_marker**: `content` に部分文字列 `adj-live-` を含む → `reason="explicit_test_marker"`（実測6件: RREQ-00065..00070）。
  2. **repeated_fixture**: その record の `content_hash` が corpus 内で **2回以上出現** → `reason="repeated_fixture"`（実測: 15 hash / 482 records。同一 content の再投入＝benchmark 反復）。
  - 両方該当は reason を配列 or 優先（explicit_test_marker 優先）で可。**ts batch は基準に採らない**（bulk import と区別不能ゆえ false-tag 回避）。
  - 上記いずれにも該当しない record は **tag しない**（RECORD_TAGS に出さない＝未分類）。

## 2. LEDGER_REGISTRY(s10) に登記（必須・台帳を増やすな＝登記せよ）
- `RECORD_TAGS.jsonl` を s10 の登記簿に登録: **purpose**（test-origin overlay タグ）/ **genesis**（本 DE）/ **作成 prog**（s_record_tags.py）/ **sole-writer**（s_record_tags.py）/ **書き手・読み手** を明記。
- s10 の既存作法（`s10_ledger_registry.py`）に従う。s10 `--check` に載せる。

## 3. ゲート `structure/s_record_tags.py --check`
- **byte一致再生成**（決定論）。
- **基準 load-bearing（陰性対照）**: adj-live-* を含む record が必ず explicit_test_marker で tag される（漏れたら RED）。content_hash 重複判定の陰性対照（重複を1件に崩すと repeated_fixture が消える＝真の重複を見ている）。
- **rri 無改変**: `rri_records.jsonl` が読み取り専用（書込なし）をコードで担保。
- **overlay 不変**: RECORD_TAGS は corpus を物理変更しない（2b パイプラインの入力・membership に影響しないことを確認。account 棚は soft/advisory ゆえ既に gate しない）。

## 4. 受入（設計が独立再検証）
- 私が fresh 再実行して RECORD_TAGS byte一致・adj-live 6件 explicit・repeated_fixture が content_hash 重複と一致・**未該当は未 tag**（捏造ゼロ）。
- rri_records 無改変（git 上も rri repo に diff なし）。
- s10 登記済み・s10/s_record_tags 両 --check GREEN。
- タグが 2b membership/軸/その他 を一切変えない（overlay 実証）。

## 5. 完了後
- `CC_IMPL_2026-07-25_RECORD_TAGS_TEST_ORIGIN_BUILT.md`（宛 AUDIT/DESIGN）→ 設計再監査 → CONSISTENT → **commit=Taka**（egl のみ・rri 触らない）→ DE 起票（P2）。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。overlay・rri無改変・登記必須・判定不能は未tag。★3 本線・止めない。*
