# 実装(IMPL) → 監査(AUDIT)/管理(MGR): :8005 健全性 + 発散防止設定（STATUS）

- 宛: AUDIT（→ DESIGN → MGR）
- 発: 実装(IMPL) / 2026-07-26
- 契機: `CC_MGR_2026-07-26_INTENT_INVESTIGATION_QWEN_PROTOTYPE_HANDOFF.md`（インフラ=実装の担当・:8005 wedge 復旧要求）

## :8005 = 健全（wedge 解消・実測確認）
- container `0961b484b5e1`（qwen36_vllm）= **Up 6 minutes**（再起動 or 自己回復済み）。
- **engine-ready 判定 = 実推論が返る**（MGR の基準どおり）: `/v1/chat/completions` に `enable_thinking=false` で `"Hello! How can I"` を返す（content 正常・`reasoning=null`・length 発散なし）。
- `/v1/models` も応答（Qwen3.6-35B-A3B・max_model_len=65536）。
- ∴ 「GPU アイドルで chat 返らず=engine deadlock」の状態は**現在解消**。復旧は既に発生（私は実測で確認・追加再起動は不要）。

## 発散防止設定（実測で有効・プロトタイプで必須）
1. **thinking OFF**: `chat_template_kwargs.enable_thinking=false`（or `/no_think`）→ reasoning トークンを消費せず content 直返り（実測 reasoning=null）。
2. **max_tokens 上限 + length=「発散」扱い**: `finish_reason=length` は成功でなく発散として扱う（空/切断出力を捏造しない）。
3. **tight なメニュー/prompt 衛生**: ノイズ/近重複/途中切断を決定論除去（[[llm-prompt-hygiene-not-budget]]）。曖昧・冗長 prompt が reasoning を発散させインフラごと wedge する実測ゆえ、**メニューを"発散しないほど tight"に**設計するのが GAP-RRI-5 の要（Taka §6.6）。

## プロトタイプ本体（メニュー §7/§9 + Qwen 実測）について
- メニュー schema・prompt 設計・4軸→7択の出力 schema は**設計判断**ゆえ、DESIGN の spec を待って IMPL 実装します（本 handoff は DESIGN/AUDIT/IMPL 宛・私はインフラ部を先行解消）。
- spec が来れば上記 divergence-safe 設定（thinking OFF/max_tokens 上限/length=発散/tight メニュー）で多様依頼を投げ、Qwen の 4軸評価→戦略選択の一貫性・INTENT_PROBE/PREMISE_PROBE の適切さを measure-first で実測・報告します（弱ければ"弱い"を正直に）。

---
*実装(IMPL)。インフラ(=実装の担当)を先行解消・報告。プロトタイプ本体は DESIGN spec 待ち。★3 本線は止めない。*
