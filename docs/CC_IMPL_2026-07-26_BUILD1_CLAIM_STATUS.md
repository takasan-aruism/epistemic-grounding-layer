# 実装(IMPL) → 監査(AUDIT): Build 1（前提曖昧ステージ）を IMPL が取る（STATUS・衝突回避）

- 宛: AUDIT(CC-α) / 発: 実装(IMPL) / 2026-07-26 / TYPE=STATUS
- 対象: `CC_MGR_2026-07-26_BUILD_GO_AMBIGUITY_STAGE_AND_BACK_SLICE.md`（宛先が DESIGN/IMPL/AUDIT で複数役割）

## 目的
build GO が cluster 宛のため、**Build 1 を IMPL と AUDIT の双方が実装して二重発明する事故**を防ぐ。役割を明示:
- **Build 1 の実装は IMPL が取る。** CC-α は **AUDIT（独立再検証）** に回ってほしい。
- Build 2（縦串）は Build 1 の BUILT+AUDIT の後（handoff の順序どおり）。

## Build 1 の実装計画（measure-first・LIVE を測る前に触らない）
承認済み統合案（AB_COMPARISON §5）:
1. **ゲート表**: `rri/rri/preflight_gate.py` の 1ゲート固定を registry 化。既存 HBB-30 gate（RRI-GATE-AMBIGUOUS-QUANT-001）を**バイト等価で保存**し、referent gate を追加。`detect()` は登録順に回して最初の triggered を返す・完全決定論（:8005 不使用）。submit.py 3d 段の呼びは原則不変（後述の1点だけ要検討）。
2. **様式移植**: (A) input-clarity のスキーマ（`ambiguity_type`/`clarification_slots`/`false_positive_notes`/抑制カウンタ）。**clarification_slots があるので聞き返し文を捏造しない。**
3. **パターンは我々の証拠から**: (A)34パターンは流用禁止（実478発話で25%過剰・当該0/3）。**「指示語表層 AND 束縛できる先が無い」**——後半（先が無い）は構造判定（文脈空・セッションに束縛可能な直近対象なし）＝機械にしかできない側。
4. **測る**: IP1/IP2/IP3（あれ/それ/例のやつ）を通し **0/3→捕捉率**、正当依頼動詞（調べて/直して/状態…）での**過剰発火率**（回帰セット=478実発話 が使えるか調査中）。

## ★事前申告（feasibility-first・監査が見るべき点）
- submit.py 3d 段の `NEXT_LEGAL_OPERATION` は**現状 quant 専用文が hardcode**。referent gate が triggered した時に正しい聞き返し（clarification_slots 由来）を返すには、3d 段で `pg` 自身の clarification を使う**1行の配線変更**が要る。「新規配線ゼロ」の目標と抵触するので、**最小変更に留めて BUILT で明示**する（隠さない）。
- LIVE production（rri/twoder）への変更は working tree のみ・**commit=Taka**。measure-first で「捕まえる/過剰発火しない」を先に egl 側の計測モジュールで示し、LIVE 配線は測ってから提案する。

*IMPL。Build 1 を取る＝二重発明回避。CC-α は AUDIT へ。★3 本線は止めない。*
