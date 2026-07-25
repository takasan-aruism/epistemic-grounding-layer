# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 意図調べ(GAP-RRI-5) Qwen プロトタイプ（BUILT・measure-first）

- 宛: AUDIT（→ DESIGN → MGR）
- 発: 実装(IMPL) / 2026-07-26 / repo=egl / model=Qwen3.6-35B-A3B(:8005)
- 対応: `CC_DESIGN_2026-07-26_INTENT_INVESTIGATION_QWEN_PROTOTYPE_HANDOFF.md`（RRI §7 4軸/§9 7戦略）
- **これは能力測定であり成功宣言ではない**（measure-first・弱ければ弱いと言う）。

## 成果物（working tree・未commit）
- `structure/s_intent_probe_proto.py`（決定論メニュー/schema/fixture/parser/集計 + Qwen判断 + `--check`）
- `structure/INTENT_PROBE_PROTO.jsonl`（48行=fixture8×menu2×seed3・raw_output/provenance 全記録）
- meta fold（regen_meta）: LLM_INVOCATIONS（`s_intent_probe_proto:_llm` を実 :8005 CALL_SITE 登録）/ TASK_CONTRACTS / READ_PATHS

## インフラ（§0・実装の担当）
- :8005 = **健全**（container up・実推論が enable_thinking=false で返る。engine-ready を実測）。wedge 解消済み・追加再起動不要（別 STATUS 既報）。NO_INFRA 捏造なし。

## 決定論メニュー（構造固定・判断のみ Qwen）
- **4軸 enum**（§7）: context_anchoring/answer_determinacy/intent_breadth/premise_stability（各 spec §7 の enum 準拠）。
- **7戦略**（§9）: DIRECT/CONTEXT_RESOLVE/CHOICE/BOUNDED_MULTI_VIEW/INTENT_PROBE/PREMISE_PROBE/DEFER。
- 出力 schema 固定・**Qwen は enum から選ぶだけ**。schema/enum 逸脱は決定論パーサが REJECT（=発散/逸脱検出）。

## 発散対策（§2・実測で決定的）
- thinking OFF（`enable_thinking=false`）+ max_tokens=256 + **finish_reason=length は発散扱い**（成功にしない）。
- **tight vs loose メニュー比較（＝Taka 詰めの設計知見）**:
  - **tight メニュー → 発散率 0.00**（24call・length/schema/enum 逸脱ゼロ）。
  - **loose（冗長・非構造）メニュー → 発散率 1.00**（23 DIVERGE_LENGTH + 1 SCHEMA）。thinking OFF でも緩い prompt は発散。
  - ∴ **「メニューを tight にするほど発散しない」が定量実証**（0% vs 100%）。menu tightness が発散の第一レバー（[[llm-prompt-hygiene-not-budget]] の standing rule と一致）。

## Qwen 実測（§3・tight メニュー・measure-first）
| 指標 | 値 | 読み |
|---|---|---|
| (d) 発散率 | **0.00** | tight で完全に境界内 |
| (a) 軸評価妥当性 | **0.74** | expected 指定軸の一致率(24 判定) |
| (b) 戦略一致 | **0.54** | expected 戦略と一致(中程度) |
| (b) seed 間一貫性 | **6/8 fixture** | 誤りも含め seed 間で安定＝systematic |
| (c) 聞返 recall | **5/6** | probe 期待で probe を出す |
| (c) 誤聞返 | **0/18** | 過剰に聞き返さない |

### ★ どこで壊れる/迷うか（＝次のメニュー設計知見・handoff §5）
- **堅実（全 seed 正解）**: F1/F2 DIRECT（明確・確定）/ F6 INTENT_PROBE（「あれどこ？」曖昧）/ F8 DEFER（不正形）。**粗い区別は強い**。
- **壊れ所（隣接戦略の混同・全て systematic=seed 一貫）**:
  - **F3 CONTEXT_RESOLVE → BMV**: 支配的文脈を"解決"に使わず「複数観点比較」に流れる。**文脈で絞る動機が弱い**。
  - **F4 CHOICE → BMV**: 「安全に一つ選べない→選択肢提示」でなく BMV。**CHOICE と BMV の境界が曖昧**。
  - **F7 PREMISE_PROBE → INTENT_PROBE**: probe はするが**種別を誤る**（前提確認 vs 意図確認の区別が弱い）。
- パターン: Qwen は **probe-or-not / DIRECT / DEFER の粗い判断は正確、隣接する近縁戦略（CONTEXT_RESOLVE↔CHOICE↔BMV、INTENT_PROBE↔PREMISE_PROBE）の細分が弱い**。誤りは random でなく **systematic（6/8 seed 一貫）**。

## 評価（Taka 仮説の検証・正直に）
- Taka 仮説「良いメニューなら Qwen3.6 級でも矛盾しない選択」= **部分的に支持**。
  - 支持: tight メニューで **発散ゼロ + seed 一貫 6/8 + 粗い区別は正確 + 過剰聞返ゼロ**。誤りが systematic＝**メニュー設計で改善可能**な種類。
  - 留保: 戦略一致 0.54（中程度）・近縁戦略の細分は現メニューでは弱い。**"できる"と宣言しない**＝現状は「粗くは効く・細分は menu 改良が要る」。
- **次のメニュー設計提案（IMPL からの入力・DESIGN 判断）**: 近縁クラスタの**弁別基準を鋭くする**——(1) CONTEXT_RESOLVE に「支配的文脈があれば必ず先に解決」を明示 (2) CHOICE と BMV を「一つ選ぶ vs 複数見せる」で対比 (3) PREMISE_PROBE に「存在/成立の確認（intent でなく premise）」を強調。tight を保ったまま弁別語を足す。

## 検証（受入 §5・全 gate GREEN）
- `s_intent_probe_proto.py --check` **GREEN**: 記録 raw_output に決定論パーサ/集計を再適用→一致（LLM 非再実行）・fixture 固定・provenance 完全（model/endpoint/enable_thinking/max_tokens/seed/prompt_id/fixture_id/raw_output）。
- 実 :8005 CALL_SITE 登録（`s_intent_probe_proto:_llm`・meta self-heal が fold）。全 gate GREEN。
- ※軽微: 本 CALL_SITE は scanner 上 `gate_ref=NONE`（コードが USE_VLLM_INFERENCE を参照しないため）。実ゲートは :8005 開放。enforcement 一般化時に gate marker 配線を検討（別件）。

## ハンドオフ
- 次: 設計/監査 独立再監査（決定論再現・provenance）→ 結果を MGR へ（Qwen 能力・壊れ所・次メニュー設計）。commit=Taka → DE。
- 想定と実測: tight=0%発散・粗い区別強・細分弱（systematic）を silently 合わせず記録。「メニュー tight ほど発散しない」を定量実証。

---
*実装(IMPL)。メニュー=決定論固定・判断のみ Qwen・thinking OFF+tight で発散封じ・measure-first(弱ければ弱いと言う)。★3 本線・止めない。*
