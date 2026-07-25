# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): test-origin タグ台帳（BUILT・P2）+ s10 登記コンフリクト flag

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用
- 対応: `CC_DESIGN_2026-07-25_RECORD_TAGS_TEST_ORIGIN_HANDOFF.md`（MGR TEST_TAG_SCOPE 裁定）

## 成果物（working tree・未commit）
- `structure/s_record_tags.py`（決定論タグ生成器 + `--check`）
- `structure/RECORD_TAGS.jsonl`（overlay タグ台帳・tagged=482 / 698 records）

## 実装（handoff §0-1・overlay・rri無改変・判定不能は未tag）
- `/home/takasan/rri/rri_records.jsonl` を **read-only** 走査（`content_hash` は既存フィールドを利用・計算しない）。
- 決定論タグ基準（この2つのみ）:
  1. **explicit_test_marker**: content に `adj-live-` を含む → **6件（RREQ-00065..00070）**（期待一致）。
  2. **repeated_fixture**: `content_hash` が corpus 内 2回以上出現 → **476件**（15 dup hash・期待「15 hash/482 records」一致。うち 6 は explicit と重複ゆえ explicit 優先で 482=6+476）。
  - 両該当は **explicit 優先**（`also` 欄に repeated を残し後から重み付け可能に）。**ts batch は基準にしない**（bulk import と区別不能=false-tag 回避）。
  - いずれも非該当は **未 tag（216件・未分類=捏造ゼロ）**。

## 検証（全 gate load-bearing・実測）
- **byte一致再生成** GREEN。
- **基準 load-bearing（陰性対照）**: adj-live-* record が必ず explicit で tag される（漏れ検出）。**content_hash を全一意化すると repeated_fixture が消える**（真の重複を見ている証拠・非load-bearingなら RED）。両基準の空振り検出も。
- **rri 無改変（実証）**: build 前後で `rri_records.jsonl` の sha256 不変を assert。**rri repo に diff なし**（`git status` clean・非侵入原則）。
- **overlay 不変（実証）**: 2b パイプライン（s_embed_axes/account/rthread_2br3/mine）が `RECORD_TAGS` を参照しないことをコードで担保（corpus/membership に影響しない）。

## ★ flag（handoff §2 と s10 アーキテクチャの構造的コンフリクト・独断で解決しない）
handoff §2 は `structure/RECORD_TAGS.jsonl` を **LEDGER_REGISTRY(s10) に登記必須**ですが、**s10 は登記不能**です:
- `s10_ledger_registry.py:57` = **`structure/` 配下の台帳を登記対象から除外**（「本再構成の派生物は対象外」）。
- 実測: `LEDGER_REGISTRY.jsonl` 47行中 **structure/ は0件**。既存の structure/ 派生台帳 **`LLM_INVOCATIONS`/`TASK_CONTRACTS` も未登記**（同じ除外の下）。操作系（`DESIGN_EVIDENCE_LEDGER`/`rri_records`）のみ登記。
- 加えて s10 は **tracked または gitignored** の台帳しか発見しない。新規 untracked ファイルは **commit 前は登記不能**（genesis=初出コミットが無いため）。
- ∴ `structure/RECORD_TAGS.jsonl` を s10 に登記するには placement か s10 自体の変更が要る。**committed の s10 改変も §1 の structure/ 指定変更も独断で行わず flag します。**

### 裁定候補（DESIGN/MGR 判断）
- **(c) 推奨: RECORD_TAGS を structure/ 派生台帳として扱う**（LLM_INVOCATIONS/TASK_CONTRACTS と同格）。「登記せよ＝台帳を増やすな」の意図は、**決定論生成器 + docstring + `--check` gate による self-accounting** で既に満たされる（regenerable かつ gated ゆえ untracked 増殖の危険がない=登記の目的が別手段で達成）。structure/ 除外はまさにこの理由。
- (a) RECORD_TAGS.jsonl を **structure/ 外**（例 `egl/RECORD_TAGS.jsonl`）へ移し操作系台帳として s10 登記（要 commit で genesis 発生。生成器は structure/ のまま）。
- (b) s10 の `all_ledgers()` を改修して RECORD_TAGS を whitelist（committed tool 改変）。

## 受入状況
- RECORD_TAGS byte一致 / adj-live 6件 explicit / repeated が content_hash 重複と一致 / 未該当は未tag（捏造ゼロ）/ rri 無改変 / overlay 実証 — **すべて達成**。
- **「s10 登記済み」のみ上記コンフリクトで保留**（裁定待ち）。`s_record_tags --check` GREEN。

## ハンドオフ
- 次: 登記方式の裁定（(c)推奨 / (a) / (b)）→ 私が (a)/(b) なら実装。→ 設計再監査 → commit=Taka（egl のみ・rri 触らない）→ DE 起票（P2）。
- 想定（s10 登記）と実測（structure/ 除外で登記不能）のズレを silently 合わせず記録しました。★3 本線は止めていません。

---
*実装(IMPL)。overlay・rri無改変・判定不能は未tag を厳守。登記コンフリクトは独断解決せず flag。*
