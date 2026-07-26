# CC 管理(MGR) → 設計/実装(CC-α): build GO — 前提曖昧ステージ ＋ 後者の薄い縦串（HANDOFF）

- 宛: DESIGN/IMPL/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 権限: **Taka「実際作ってみないとなんともいえん・やってみて」= 両設計に build GO**。
- 方針: **作って測る**（measure-first）。findings は監査後。commit=Taka。★3 本線は止めない。

## Build 1（優先）：前提曖昧ステージ（A/B 統合 — "作って IP1/IP2 を捕まえるか"を測る）
承認済み統合案（`..._PREMISE_AMBIGUITY_AB_COMPARISON_FINDING` §5）を実装:
1. **段 = (B) を一般化**：`rri/rri/preflight_gate.py` の 1 ゲート固定を**ゲート表**にし、`detect()` を「登録全ゲートを回し最初に triggered を返す」へ。**submit.py 3d 段の呼び方は不変（新規配線ゼロ）**。完全決定論（:8005 不使用）。
2. **様式 = (A) input-clarity のスキーマを移植**：`ambiguity_type` / **`clarification_slots`（聞き返し文を捏造せず作る核）** / `possible_readings` / `false_positive_notes` / **抑制カウンタ（無視され続ける警告を自動抑制＝過剰聞き返し対処）**。
3. **★パターンは我々自身の証拠から書く**（(A)の34パターンは流用禁止＝実478発話で25%過剰発火＋我々の失敗0/3）。**指示先のない指示語（あれ/それ/例のやつ）・未成立前提**を我々の失敗事例から起こす。
4. **測る**：IP1/IP2/IP3 をこの段に通し、**今まで 0/3 で落としていたのを捕まえるか**。過剰発火率も（正当依頼の動詞=調べて/直して/状態 で誤発火しないか）。

## Build 2：後者の薄い縦串（retrieve 1本・監査の密度化込み）
`..._BACK_THIN_SLICE_DESIGN_DRAFT` ＋ `..._REVIEW_FINDING` の密度化を反映:
- **retrieve だけ end-to-end**（EGL "what's known/既に試したか"）。他アクションは NOT_BUILT を正直に返す。
- **★意図を故意に誤らせる注入試験**：正しくは CONTEXT_RESOLVE を BMV に強制 等で retrieve を走らせ、**返りが実用上壊れるか**＝「0.78 で十分か／遠い取り違えだけ致命か」を測る（これが縦串の主目的）。
- **長文で走らせ必ず計測**：入力長・意図調べ結果・崩れたか を記録（dogfood=我々の依頼は長文＝最大弱点領域。壊れる所＝次に作る所）。
- **#3 = LIVE 裏付けを入れて作る**：メニュー各項目に LIVE callee_symbol 必須・`--check` が EDGE_INVENTORY で LIVE 検証（過剰なら後で外す＝Taka「作って見てから」）。
- **probe→再開：ユーザ返答をそのまま信じず、新依頼として再度 意図調べにかける**（主張を検証なく飲む経路を作らない）。
- **NOT_BUILT/BLOCK は必ず記録**（front door `record_de`・`generated_by_principal=CLAUDE_CODE` 開示）。

## 順序・報告
- Build 1 先行（既存 LIVE 段の拡張＝軽い・粘る弱点の直接治療）→ Build 2。
- 各 BUILT → **監査が独立再検証** → MGR/Taka へ（未監査は"実装主張・未検証"扱い）。
- 不変: measure-first（弱ければ弱いと）・sole-writer・捏造ゼロ・commit=Taka・全 gate GREEN。
