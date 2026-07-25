# 設計/監査 → 実装: 意図調べ再測定 — thinking ON（HANDOFF・delta）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=egl / model=Qwen3.6-35B-A3B(:8005)
- 正本: `CC_MGR_2026-07-26_INTENT_PROBE_RETEST_THINKING_ON_HANDOFF.md`（Taka「think 使わないと案外バカ。使わせて」）+ 既存 `s_intent_probe_proto.py`（thinking OFF baseline）+ 本 handoff
- 位置づけ: 前回 thinking OFF は**過剰対策**（発散真因は緩い/ノイズ prompt であって thinking 自体でない）。**thinking を使わせて賢さを取り戻し、近縁戦略の細分が改善するか**を測る。

## 0. 是正の要点
- 発散は「thinking を切る」でなく「**clean/tight prompt + 十分な budget で正常終端させる**」で封じる（[[llm_prompt_hygiene_reasoning_runaway]] の本来の教訓＝clean prompt なら thinking は ~3000tok で終端）。

## 1. 依頼（既存プロトタイプの最小 delta）
- **thinking ON**（`enable_thinking=true` or /no_think を外す）で **同じ tight メニュー §7 4軸/§9 7戦略・同 8 fixture・3 seed** を再実行。
- **max_tokens は thinking の自然終端を許す値**（例 4000〜6144・前回 clean-prompt 実測 ~3083tok 参考）。
- **DIVERGE 判定**: **真の runaway（budget 到達で未終端＝finish_reason=length）だけを DIVERGE**。捏造しない（空/切断から名を作らない）。
- **自衛**: budget 上限 + タイムアウトで infra を固めない（前回 wedge の教訓）。thinking ON で発散が再発したら「tight でも thinking ON は発散」を正直に記録（menu をさらに締める設計知見へ）。

## 2. thinking OFF baseline との直接比較（同 fixture）
- 出力: thinking OFF（既存 48行）と **thinking ON** を並べ、以下の delta を決定論集計:
  - 発散率 / 軸妥当性(0.74) / 戦略一致(0.54) / seed一貫(6/8) / probe recall(5/6) / 誤probe(0/18)。
  - **焦点 = 近縁戦略の細分（CONTEXT_RESOLVE↔CHOICE↔BMV, INTENT_PROBE↔PREMISE_PROBE）が改善するか**（前回 systematic に混同）。F3/F4/F7 の改善を特に見る。
- provenance に **`enable_thinking` / `max_tokens` / `reasoning_tokens`（thinking 消費）** を追加記録。

## 3. 規律
- **measure-first**: thinking ON でも弱ければ"弱い"を正直に。強くなれば「細分まで効く」を実証。
- 決定論部（メニュー/schema/集計/fixture）不変・byte 再現。LLM 判断のみ非決定論。:8005 CALL_SITE 登録（meta self-heal fold）。全 gate GREEN・commit=Taka・★3 本線は止めない。

## 4. 受入 / 報告
- thinking ON の 発散率 / 各指標 / **近縁戦略細分の改善 delta** を thinking OFF と並べて決定論集計・byte 再現。
- reasoning_tokens の分布（自然終端 tok 数）と、発散が起きた場合の budget/条件。
- **判断材料**: 「Qwen は thinking ON でどこまで賢くなるか（細分まで効くか）／発散リスクと budget」。

## 5. 完了後
- `CC_IMPL_2026-07-26_INTENT_PROBE_RETEST_THINKING_ON_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → 結果を MGR へ → commit=Taka → DE。
- 注（DE 記録）: 本結果の DE は front door(`record_de`)で記録する際 **candidate に `generated_by_principal="CLAUDE_CODE"` + `claiming_principal="CLAUDE_CODE"` + `generation_mode="DIRECT"` を明示**（内部アクター開示・DE-0540 と同様。DE-0541 は失念で UNKNOWN になった＝再発防止）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。thinking ON で賢さを測る・発散は clean/tight+budget で封じる・measure-first。★3 本線・止めない。*
