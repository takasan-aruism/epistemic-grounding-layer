# CC 管理(MGR) → 設計/実装(CC-α): 意図調べ(GAP-RRI-5) Qwen プロトタイプ HANDOFF

- 宛: DESIGN/AUDIT/IMPL(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 位置づけ: DS-RRI の最重要点＝**初手に「意図を調べる」を構造で強制する step**（総覧doc §6・GAP-RRI-5）。まず Qwen で「どこまで会話だけで対応できるか」を測る。

## 依頼：意図調べ step の最小プロトタイプ＋Qwen 実測
1. **メニュー実装（決定論の構造）**：RRI spec §7(4軸: 文脈依存/答えの確定性/意図の広さ/前提の安定) → §9(7択: DIRECT/CONTEXT_RESOLVE/CHOICE/BOUNDED_MULTI_VIEW/INTENT_PROBE/PREMISE_PROBE/DEFER)。判断は Qwen、**メニュー/出力schemaは決定論で固定**。
2. **Qwen 実測（:8005）**：多様な依頼（曖昧/文脈依存/前提が怪しい/明確 等）を投げ、**Qwen が4軸評価→戦略選択を矛盾なくできるか**を測る。Taka 仮説「良いメニューなら Qwen3.6級でも矛盾しない」の検証。
3. **発散対策（必須）**：reasoning 発散＝インフラごと wedge するリスク実測済（[[llm-prompt-hygiene-not-budget]]）。**thinking OFF（`chat_template_kwargs.enable_thinking=false` or `/no_think`）＋tight なメニュー＋max_tokens 上限＋length は「発散」扱い**。「メニューを tight にするほど発散しない」も測る＝設計知見。

## インフラ（実装の担当・MGRは触らない）
- **現在 :8005 は wedge 状態**（GPU アイドルなのに chat 返らず＝engine deadlock。私の緩いプロンプト発散が原因の可能性）。**復旧は実装側で**（container `0961b484b5e1`=qwen36_vllm の再起動/再作成、engine-ready は"実推論が返るか"で判定）。既知の起動構成は memory `qwen36_35b_a3b_vllm_setup` 参照。

## 報告してほしいこと
- Qwen が意図調べをどこまでできたか（軸評価の妥当性・戦略選択の一貫性・聞き返し(INTENT_PROBE/PREMISE_PROBE)を適切に出すか）。
- どこで壊れる/迷うか（＝次に詰めるメニュー設計）。
- :8005 復旧の可否と、発散を防ぐ設定。
- 不変: measure-first（Qwenが弱ければ"弱い"を正直に）・commit=Taka・★3本線は止めない。
