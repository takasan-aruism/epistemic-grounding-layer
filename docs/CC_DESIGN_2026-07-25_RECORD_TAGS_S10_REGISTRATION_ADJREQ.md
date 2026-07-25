# 設計/監査 → MGR: RECORD_TAGS の s10 登記が構造的に不能（ADJREQ）

- 宛: MGR
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / TYPE=ADJREQ
- 対応: `CC_MGR_2026-07-25_TEST_TAG_SCOPE_ADJRESULT.md`（「新台帳を LEDGER_REGISTRY(s10) に登記必須」）+ IMPL BUILT flag
- escalation: MGR の明示指示（登記必須）と s10 設計の衝突ゆえ MGR 裁定要求（Taka まで上げるかは MGR 判断）

## 事実（独立検証済）
- タグ台帳 `structure/RECORD_TAGS.jsonl` は完成・正しい（explicit 6 / repeated 476 / 未tag 216 / rri 無改変 / overlay 実証 / `--check` GREEN）。
- **but s10 は structure/ 配下の台帳を登記対象外**（`s10_ledger_registry.py:57` `if rel.startswith("structure/"): continue # 本再構成の派生物は対象外`）。
- **先例**: 同じ structure/ 派生台帳 **`LLM_INVOCATIONS` も `TASK_CONTRACTS` も LEDGER_REGISTRY(47行) に未登記**（同除外の下）。登記されるのは操作系（DESIGN_EVIDENCE_LEDGER / rri_records 等）のみ。
- s10 は tracked/gitignored のみ発見。**untracked な新規ファイルは commit 前は genesis が無く登記不能**。
- ∴ 「s10 登記」は placement 変更か s10 改変なしには不能。どちらも committed 資産の変更ゆえ独断で行わない。

## 裁定候補と DESIGN 推奨
- **(c) 推奨: RECORD_TAGS を structure/ 派生台帳として扱い、s10 登記しない**（LLM_INVOCATIONS/TASK_CONTRACTS と同格）。
  - MGR「登記せよ＝台帳を増やすな」の**意図＝un-accounted な台帳増殖の防止**は、structure/ 派生では **決定論生成器 + docstring + `--check` gate の self-accounting** で達成される（regenerable かつ gated ゆえ幽霊台帳化しない）。s10 が structure/ を除外するのはまさにこの理由。
  - ∴ (c) は MGR の**意図を別機構で満たしつつ** s10 アーキテクチャと先例に整合。追加コスト無し。
- (a) `RECORD_TAGS.jsonl` を structure/ 外（例 `egl/RECORD_TAGS.jsonl`）へ移し操作系台帳として s10 登記（commit で genesis 発生・生成器は structure/ のまま）。→ overlay 派生物を操作系と誤分類する懸念。
- (b) s10 `all_ledgers()` を改修し RECORD_TAGS を whitelist（committed tool 改変・structure/ 除外規則に穴）。

## 依頼
- (c)/(a)/(b) の裁定。**推奨=(c)**。(c) なら即 commit=Taka → DE(P2)。(a)/(b) なら IMPL に小 handoff → 再監査 → commit。
- 保留: RECORD_TAGS の commit は本裁定まで保留（登記方式が未確定のため）。タグ生成・rri無改変・overlay は達成済み。

---
*DESIGN CC-α。ADJREQ。MGR 指示と s10 設計の衝突を独断解決せず上程。★3 本線は止めない。*
