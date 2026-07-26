# CC 管理(MGR) → 設計/実装(CC-α): Recognition Resolver v0.2 承認・Build 1/2 続行（HANDOFF）

- 宛: DESIGN/IMPL/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 権限: **Taka 承認（2026-07-26）「この枠で Build 1/2 を進めて」**。
- 対応: `CC_DESIGN_2026-07-26_RECOGNITION_RESOLVER_ARCHITECTURE_v0_2.md`

## 確定：v0.2 を今後のアーキとして採用
- **中核＝「認識を解く」でなく「接地しない前提で走り出すのを止める」**。EGL の「根拠なき claim を認めない」を**入力側に適用**。認識固定(観測不能)を追わず、**入力の仮定前提が接地するかを機械で確認**。
- **generation(§10)→retrieval に置換**／選択役依存の Frame 比較(§11)→決定論の処理決定に置換、を採用（今日の実測に接地）。
- v0.1 §1-9/§13-14 維持・§10-11 置換・§12 に SUPERSEDE 追加、で確定。

## Build 1（前提曖昧ステージ）＝ v0.2 の P1-P4 ゲート表で
既発の build GO を v0.2 に接続。**Nゲート化の中身＝P1-P4**（全決定論・LLM ゼロ）:
- **P1 出典**（数値＋出典なし）＝既存 LIVE ゲート。
- **P2 参照**（あれ/それ ∧ 束縛先なし）＝実装中。
- **P3 文脈**（文脈依存を選んだのに context==""）＝即効。
- **★P4 存在の前提**（「以前作ったX」「その6倍の導出」）＝**台帳/ファイルに接地するか照合**＝HBB-30 の本体。**LLM に疑わせず、機械が台帳に当たり"無ければ無い"と返す。** PP1/PP2 も同型。
- 様式は input-clarity のスキーマ（clarification_slots＝聞き返し文・抑制カウンタ）、**パターンは我々の証拠から**（A の34は流用禁止）。
- 測る：IP1/IP2/IP3 を通し、今まで 0/3 で落としていたのを捕まえるか＋過剰発火率。

## Build 2（後者の薄い縦串）＝ そのまま続行
既発 build GO のとおり（retrieve 1本・意図誤り注入試験・長文計測・LIVE裏付け --check・probe再開は返答を再意図調べ・NOT_BUILT/BLOCK 記録）。

## 不変
measure-first（弱ければ弱いと）・findings は監査後・sole-writer・捏造ゼロ・commit=Taka・全 gate GREEN・★3 本線は止めない。Build1 先行 → Build2。
