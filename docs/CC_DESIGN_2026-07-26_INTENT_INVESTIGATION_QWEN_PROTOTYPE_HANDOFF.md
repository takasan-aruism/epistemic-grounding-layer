# 設計/監査 → 実装: 意図調べ(GAP-RRI-5) Qwen プロトタイプ spec HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=egl / **:8005 使用（意図調べは Qwen 判断）**
- 正本: `CC_MGR_2026-07-26_INTENT_INVESTIGATION_QWEN_PROTOTYPE_HANDOFF.md` + `docs/EGL_REQUEST_RESOLUTION_RESEARCH_INTENT_SPEC_v0_2.md §7(4軸)/§9(7択)` + 本 handoff
- 位置づけ: DS-RRI 最重要＝初手に「意図を調べる」を構造で強制。**まず Qwen で"どこまで会話だけで対応できるか"を measure-first で測る**。gate 緩和でなく能力測定。

## 0. 前提インフラ（実装の担当・最初にやる）
- **:8005 は現在 wedge**（GPU アイドルなのに chat 返らず＝engine deadlock）。container `0961b484b5e1`(qwen36_vllm) を再起動/再作成で復旧。**engine-ready = "実推論が返るか"で判定**（memory `qwen36_35b_a3b_vllm_setup` 参照）。復旧不可なら NO_INFRA を正直に報告（捏造の測定をしない）。

## 1. 決定論メニュー（構造は固定・判断のみ Qwen）
- **4軸評価**（§7・各 enum 固定）: `context_anchoring∈{HIGH,MEDIUM,LOW,UNRESOLVED}` / `answer_determinacy∈{DETERMINATE,BOUNDED,OPEN,UNRESOLVED}` / `intent_breadth`(§7.3) / `premise_stability`(§7.4)（各 enum は spec §7 準拠）。
- **7戦略選択**（§9）: `DIRECT / CONTEXT_RESOLVE / CHOICE / BOUNDED_MULTI_VIEW / INTENT_PROBE / PREMISE_PROBE / DEFER`。
- **出力 schema 固定（決定論）**: `{axes:{context_anchoring,answer_determinacy,intent_breadth,premise_stability}, strategy, reason}`。Qwen は**固定 enum から選ぶだけ**（自由記述で軸/戦略を発明しない）。schema 外・enum 外は決定論パーサが REJECT（＝発散/逸脱の検出）。

## 2. 発散対策（必須・[[llm_prompt_hygiene_reasoning_runaway]] / standing rule 準拠）
- **thinking OFF**: `chat_template_kwargs.enable_thinking=false`（or `/no_think`）。
- **tight menu prompt**: メニュー(4軸 enum + 7戦略 + 出力 schema)を簡潔・機械ノイズ無し・重複無しで提示（prompt 衛生3点）。
- **max_tokens 上限** + **`finish_reason=length` は「発散」扱い**（成功にしない・空出力から捏造しない）。
- **設計知見の測定**: 「メニューを tight にするほど発散しない」を実測（tight 版 vs 緩い版で length/矛盾率を比較）。

## 3. Qwen 実測（measure-first・:8005）
- **多様な依頼 fixture**（決定論・固定セット）: 明確(DIRECT想定) / 文脈依存(CONTEXT_RESOLVE想定) / 曖昧・意図広い(INTENT_PROBE想定) / 前提が怪しい(PREMISE_PROBE想定) / 回答空間広い(BOUNDED_MULTI_VIEW想定) / 選択肢型(CHOICE想定) / 保留すべき(DEFER想定) を各複数。
- **測定指標（決定論集計）**:
  - (a) **軸評価の妥当性**: Qwen の4軸値が fixture の想定と整合するか（人手 or 決定論ラベルと突合）。
  - (b) **戦略選択の一貫性/無矛盾**: 軸値→戦略が矛盾しないか（例 DETERMINATE+HIGH→DIRECT のはず。INTENT_PROBE を出したら矛盾）。**同一依頼の seed 間一貫性**も測る（Taka 仮説「良いメニューなら Qwen3.6級でも矛盾しない」の検証）。
  - (c) **聞き返しの適切さ**: 曖昧/前提怪しいで INTENT_PROBE/PREMISE_PROBE を適切に出すか（過剰に聞き返さない・必要な時に聞く）。
  - (d) **発散率**: length/schema逸脱/enum外 の割合。tight vs 緩い の比較。
- **provenance**: model/endpoint/enable_thinking/max_tokens/seed/prompt_id/fixture_id/raw_output を全記録。LLM_INVOCATIONS に CALL_SITE 登録（meta self-heal が fold）。

## 4. 規律
- **measure-first**: Qwen が弱ければ（矛盾/発散/軸誤り）**"弱い"を正直に報告**（無理に"できる"にしない）。これは能力測定であり成功宣言でない。
- 決定論部（メニュー/schema/集計/fixture）は決定論・byte 再現。LLM 判断のみ非決定論。sole-writer 分離・commit=Taka・★3 本線は止めない。

## 5. 受入 / 報告（BUILT に）
- :8005 復旧の可否 + engine-ready 判定方法 + 発散を防いだ設定（enable_thinking/max_tokens/menu tightness）。
- **Qwen が意図調べをどこまでできたか**: (a)軸評価妥当性 (b)戦略一貫性(seed間含む) (c)聞き返し適切さ (d)発散率、を fixture 全体で決定論集計。
- **どこで壊れる/迷うか**（＝次に詰めるメニュー設計の知見）。
- 決定論メニュー/schema/集計が byte 再現・fixture 固定・provenance 完全。

## 6. 完了後
- `CC_IMPL_2026-07-26_INTENT_INVESTIGATION_QWEN_PROTOTYPE_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → 結果を MGR へ（Qwen の能力・壊れ所・次メニュー設計）。commit=Taka → DE。
- 想定と実測がズレたら silently 合わせず記録（Qwen が弱い/強いをそのまま）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。メニュー=決定論固定・判断のみQwen・thinking OFF+tight menuで発散封じ・measure-first(弱ければ弱いと言う)。★3 本線・止めない。*
