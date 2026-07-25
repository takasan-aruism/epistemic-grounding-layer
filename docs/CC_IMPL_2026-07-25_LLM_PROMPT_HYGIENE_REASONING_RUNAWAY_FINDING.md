# 実装(IMPL) → 管理(MGR): reasoning LLM の token 発散＝prompt 衛生の問題（FINDING・恒久視点）

- 宛: MGR（AUDIT/DESIGN 経由可）/ 発: 実装(IMPL) / 2026-07-25
- 契機: Taka 指示「LLM の token 数の件をレポートしてマネージャに伝えよ。**同じ問題2度目**なので今後の LLM 設計で重要な視点として記録を残す」
- 対象事象: 2b-2 命名（`s_account_axis_names.py`・初の実 :8005）で Qwen3.6-35B-A3B の thinking が終端せず発散。

## 症状と誤診（重要）
- 症状: `finish_reason=length`・`content=None`。**一見「max_tokens 不足」に見える**。
- 誤診の罠: max_tokens を増やす（32→512→1024→4096→8192）→ **AX-72ead44e は 8192(16倍)でも終端せず**。budget 増では救えなかった。
- **真因は prompt の曖昧さ**（Taka の指摘「qwen への指示が曖昧だから thinking が止まらない／どんな指示を出しているか確認せよ」で判明）:
  1. **機械ノイズ**: 各サンプルに `# gen-nonce 3190716-2-1784303070261` の乱数ヘッダ。
  2. **近重複**: 12 サンプルが gen-nonce 以外**バイト同一**（repeated_fixture の反復依頼をそのまま提示）。
  3. **途中切断**: content を固定長で切り "Your module MUST " で分断＝不完全文。
  → reasoning モデルが「なぜ全部同じ？nonce は何？何が違う？」と延々自問し発散。

## 是正（根治）
- prompt を **clean 化**（`# gen-nonce` 行除去 + 空白正規化 + 近重複除去 + 意味の要点を代表提示）→ **thinking が ~3083 tok で正常終端**。モード切替でなく prompt 品質で解決。

## 恒久視点（LLM 設計の checklist へ・2度目ゆえ institutionalize 推奨）
1. **reasoning/thinking モデルでは「token 発散＝prompt 衛生の欠陥」を第一に疑う**。max_tokens 増は対症でしばしば無限後退。
2. **投入前に prompt を必ず目視**（"どんな指示を出しているか確認"）。特に台帳/corpus 由来のテキストを機械的に流し込む経路は、ノイズ/重複/切断が混入しやすい。
3. **prompt 衛生の3点**: (a) 機械ノイズ（nonce/ハッシュ/デバッグ行）を決定論除去、(b) 近重複を除去して distinct 代表のみ、(c) 構造の途中で切らない（文/レコード境界で切る）。
4. **budget は衛生の後**: clean な prompt の自然終端を実測してから余裕（今回 3083→6144）を設計。truncation は握り潰さず明示エラー（空出力で捏造名を作らない）。

## 位置づけ
- これは gate を緩める話ではなく **入力（prompt）の質を上げる話**。[[llm_arithmetic_drift_tolerant_design]]（構造は決定論・値は揺れ許容）と同系＝**構造前処理（clean/dedup）を決定論で固めてから LLM に渡す**。
- 私（IMPL）側では 2b-2 命名で clean 化を実装済み・GREEN。本 FINDING は横展開（他の :8005 経路が増える時の設計則）として MGR に記録を残すもの。

---
*実装(IMPL)。Taka 指示による恒久視点の記録。同型再発防止＝prompt 衛生を LLM 設計の第一チェックに。*
