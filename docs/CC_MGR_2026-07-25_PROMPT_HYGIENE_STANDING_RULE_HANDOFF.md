# CC 管理(MGR) → 設計/監査(CC-α): prompt 衛生を LLM 設計の第一チェックに（STANDING RULE）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-25 / TYPE=HANDOFF
- 対応: `CC_IMPL_2026-07-25_LLM_PROMPT_HYGIENE_REASONING_RUNAWAY_FINDING.md`（Taka 指示・2度目ゆえ institutionalize）
- 受理: IMPL の FINDING を **standing design rule として受理・institutionalize**。MGR 記憶にも刻んだ。

## 標準規則（全 :8005 経路に適用）
1. reasoning モデルの token 発散＝**prompt 衛生の欠陥を第一に疑う**。max_tokens 増は対症・無限後退。
2. **投入前に prompt を目視**（台帳/corpus 由来を機械流し込みする経路は要注意）。
3. 衛生3点: (a)機械ノイズ(nonce/hash/debug行)を決定論除去 (b)近重複除去→distinct代表のみ (c)文/レコード境界で切る。
4. budget は衛生の後（clean 終端を実測→余裕）。truncation は明示エラー（空出力から捏造しない）。

## 依頼（急ぎでない・naming を止めない）
- 上記を **LLM-invocation の設計 checklist** に載せる（今後 :8005 経路が生える時の必須確認）。
- **将来 :8005 経路が増えたら**、prompt 衛生を**各 script で再発明せず共有 preprocessing util** に切り出すのが望ましい（clean/dedup/境界切り）。今すぐの新規実装は不要＝naming 完了を優先。
- 位置づけ: gate 緩和でなく入力品質。[[llm_arithmetic_drift_tolerant_design]] 同系（構造前処理は決定論で固めてから LLM）。
