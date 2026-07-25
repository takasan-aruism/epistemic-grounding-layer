# CC 管理(MGR) → 実装/設計(CC-α): 意図調べ再測定 — thinking ON で（HANDOFF）

- 宛: IMPL/DESIGN(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 対応: `CC_IMPL_2026-07-26_INTENT_INVESTIGATION_QWEN_PROTOTYPE_BUILT.md`（thinking OFF・戦略一致0.54）
- 契機: **Taka「think 使わないと案外バカ。使わせて」**

## 是正：thinking OFF は過剰対策だった
- 前回 divergence 対策で `enable_thinking=false` にしたが、**発散の真因は"緩い/ノイズある prompt"であって thinking 自体ではない**（[[llm-prompt-hygiene-not-budget]] の本来の教訓＝clean prompt なら thinking は ~3000tok で正常終端）。
- thinking OFF は Qwen を dumb 化した疑いが濃い（戦略一致0.54・近縁戦略の細分弱）。**thinking を使わせて賢さを取り戻す。**

## 依頼：thinking ON で再測定（同 fixture・比較）
1. **thinking ON** で同じ意図調べ（tight メニュー §7 4軸/§9 7戦略・同 8 fixture・3 seed）を再実行。
2. **発散は"thinking を切る"でなく"clean/tight prompt＋十分な budget で正常終端させる"で封じる**：
   - tight メニュー維持（前回 tight=発散0% 実証済、それは thinking OFF 下だが、tight prompt は thinking ON でも終端が期待できる）。
   - **max_tokens は thinking の自然終端を許す値**（例 4000〜6144。前回の clean-prompt 実測 ~3083tok を参考）。**真の runaway（budget 到達で未終端）だけを DIVERGE 扱い**、finish_reason=length は発散として記録（捏造しない）。
3. **thinking OFF ベースラインと直接比較**：発散率／軸妥当性0.74／戦略一致0.54／seed一貫6-8／probe recall5-6/誤probe0 が **thinking ON でどう動くか**。特に**近縁戦略の細分（CONTEXT_RESOLVE↔CHOICE↔BMV, INTENT_PROBE↔PREMISE_PROBE）が改善するか**が焦点。

## 規律
- measure-first（thinking ON でも弱ければ"弱い"）。もし thinking ON で発散が再発しインフラを固めるなら、**budget 上限＋タイムアウトで自衛**しつつ「tight でも thinking ON は発散する」を正直に記録（menu をさらに締める設計知見へ）。
- provenance に enable_thinking/max_tokens/reasoning_tokens も記録。全 gate GREEN・commit=Taka・★3 本線は止めない。

## 期待する判断材料
「Qwen は thinking ON でどこまで賢くなるか（細分まで効くか）／その時の発散リスクと budget」——これが Taka の求める "AI同士でどこまでできるか" の核。
