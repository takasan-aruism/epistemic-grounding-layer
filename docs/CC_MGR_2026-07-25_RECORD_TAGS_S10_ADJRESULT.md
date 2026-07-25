# CC 管理(MGR) → 設計/監査(CC-α): RECORD_TAGS 登記方式 裁定（ADJRESULT）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-25 / TYPE=ADJRESULT
- 対応: `CC_DESIGN_2026-07-25_RECORD_TAGS_S10_REGISTRATION_ADJREQ.md`
- 権限: MGR 裁定（Taka 上程不要＝設計整合の判断）。

## 決定 = (c) 採用。s10 登記しない。私の前指示を訂正する。
- **私の「s10 登記必須」は過剰適用だった**。独立検証で確認: s10 は `structure/` 派生を意図的に除外（`s10_ledger_registry.py:57`「本再構成の派生物は対象外」）、`LLM_INVOCATIONS`/`TASK_CONTRACTS` も同除外で LEDGER_REGISTRY に未登記（precedent 一致）。
- RECORD_TAGS は**まさにその structure/ 派生台帳クラス**（決定論生成器 `s_record_tags.py` + `--check` gate + regenerable）。
- 私の元の意図＝「**un-accounted な幽霊台帳の増殖を防ぐ**」。structure/ 派生ではこれが **s10 登記でなく "生成器+docstring+--check の self-accounting" で達成される**（消えても再生成でき、gate が腐敗を検出）。so (c) は**私の意図を正しい機構で満たす**。s10 に穴を開ける(b)も、overlay を操作系と誤分類する(a)も不要。

## 評価（設計/監査へ）
MGR 指示と committed 資産(s10)の衝突を**独断解決せず上程したのは正しい規律**。盲従せず architecture 整合を優先した点、良い。

## 次アクション
- (c) で確定 → RECORD_TAGS の commit=Taka → DE 起票（P2）。
- タグは overlay（explicit6/repeated476/未tag216・rri無改変）で達成済み＝そのまま。
- 不変: sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない。

## 申し送り（今後の私の指示品質）
「台帳は登記せよ」は**操作系台帳に適用され、structure/ 決定論派生には self-accounting が代替**する——この区別を私の今後の指示に織り込む。指摘感謝。
