# 設計/監査 → 実装: 意図調べ アーム C — 並列 1問1答分解 + 決定論集計（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=egl / model=Qwen3.6-35B-A3B(:8005)
- 正本: `CC_MGR_2026-07-26_INTENT_PROBE_PARALLEL_DECOMP_ADDENDUM_HANDOFF.md`（Taka「4カテゴリなら1つずつ○○の問いか?・3Bだから並列いくらでも」）+ 既存 `s_intent_probe_proto.py` + 本 handoff
- 位置づけ: 第3アーム。**細分の弱さを"LLMに細分させない"で回避**——LLM=粗い yes/no のみ、戦略の弁別は決定論集計。

## 0. 核心思想
- 低レベル LLM は**複雑な多部判断より 1問1答が正確**（tiny prompt＝発散もしにくい）。
- **近縁戦略の細分（CONTEXT_RESOLVE↔CHOICE↔BMV / INTENT_PROBE↔PREMISE_PROBE）を LLM に選ばせず、決定論集計で弁別**（前回 systematic 弱点の直接対策・2DER の良いメニュー思想）。

## 1. 分解（1問1答 tiny prompt・決定論固定）
- **軸プローブ ×4**（§7）: 各軸を独立 yes/no(+一言根拠) の tiny prompt に:
  - context: 「この依頼は"直前の文脈"に依存して初めて意味が定まるか？ yes/no」
  - determinacy: 「合理的な回答が1つに絞れるか（答えの確定性が高いか）？ yes/no」
  - intent_breadth: 「求めている範囲が広く/曖昧で、意図の確認が要るか？ yes/no」
  - premise_stability: 「依頼が前提している事実/存在は、確認せず信じてよいか？ yes/no」（no=前提が怪しい）
- 各 prompt は**メニュー全体を載せず当該1問のみ**（tight・ノイズ無し）。出力 schema=`{answer:yes|no, note}`（enum 固定・逸脱は決定論 REJECT）。
- 分解方式は**固定・記録**（prompt_id 付き）。

## 2. 並列実行（3B ゆえ安い）
- 全 sub-question（fixture×4軸×seed）を**並列発行**（`max-num-seqs` 内で束ねる）。並列数・レイテンシ・総呼出数を記録。
- thinking は C では tiny ゆえ **ON でも終端しやすい**——**軸ごとに thinking ON/OFF を測ってよい**（tiny+ON の終端 tok を記録）。発散（budget 到達未終端）は DIVERGE 記録。

## 3. 決定論集計（LLM に細分させない・弁別は集計側）
- 4軸の yes/no プロファイル → **決定論ルールで戦略**（§9）に写像。例（弁別を集計で持つ）:
  - premise_stability=no（前提怪しい）→ **PREMISE_PROBE**（intent と区別＝集計が持つ）。
  - intent_breadth=yes かつ premise ok → **INTENT_PROBE**。
  - context=yes（文脈依存）→ **CONTEXT_RESOLVE**（BMV でなく＝集計が"支配文脈は先に解決"を持つ）。
  - determinacy=yes かつ context=no かつ intent ok → **DIRECT**。
  - determinacy=no かつ選択肢が有限そう → **CHOICE** / 回答空間が広く発散 → **BOUNDED_MULTI_VIEW**（CHOICE vs BMV の弁別を集計ルールで明示）。
  - 不正形/保留相当 → **DEFER**。
  - ※ルールは**設計固定・記録**（近縁戦略の弁別語は spec §9 準拠で集計側に埋め込む）。曖昧で決まらなければ `UNRESOLVED_AGG`（捏造しない）。

## 4. 3アーム比較（同 fixture/seed・measure-first）
| アーム | 方式 |
|---|---|
| A 単発 thinking OFF | 既測(戦略一致0.54・細分弱) |
| B 単発 thinking ON | 別 handoff |
| **C 並列分解 1問1答＋決定論集計** | 本件 |
- 各アームで **軸妥当性 / 戦略一致 / seed一貫 / probe recall / 発散率 / レイテンシ・呼出数** を決定論集計・並置。**焦点＝C が"粗くも細分も"効くか**（F3/F4/F7 の細分改善）。
- provenance: arm/分解方式/並列数/thinking/budget/reasoning_tokens/sub-answers 全記録。:8005 CALL_SITE 登録（meta fold）。

## 5. 規律 / 受入 / 完了後
- measure-first（C も弱ければ正直に）・決定論部 byte 再現・全 gate GREEN・commit=Taka・★3 本線は止めない。
- `CC_IMPL_2026-07-26_INTENT_PROBE_ARMC_PARALLEL_DECOMP_BUILT.md` → 設計独立再監査 → 3アーム比較を MGR へ → commit=Taka → DE。
- DE 記録は front door(`record_de`)＋**candidate に CLAUDE_CODE 明示**（内部アクター開示・DE-0541 失念の再発防止）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。LLMは粗いyes/noのみ・細分は決定論集計・tiny並列・measure-first。★3 本線・止めない。*
