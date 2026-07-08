# NEXT-BRANCH CANDIDATES(保存のみ・現時点では実装しない)

Taka 指示により保存。**現行 HBB branch の closure を先に完了**してから着手を検討する。
自律RD は未有効。self-improvement claim なし。

## NBC-1 — STOP-SHIFT-RUN-COMPARE / 分散収束 scheduler

- **status**: `SAVED — NOT_IMPLEMENTED`(HBB closure 後に評価; その後も実装は Taka go 待ち)
- **由来**: Taka 2026-07-08 提案。reconstruction stage 比較 prereg(closure 後作成)の **R4 arm** に相当。
- **暫定理解(Taka の正式 spec 待ち)**: frame reconstruction を単発生成でなく、
  **STOP(現 frame を停止)→ SHIFT(軸/主体/層を変更)→ RUN(shift 済 frame で実行)→ COMPARE(代替と比較・収束)**
  のループとして回す「分散収束 scheduler」。複数の shifted frame を分散生成し、比較を通じて収束させる制御構造。
- **位置づけ**: reconstruction を独立機能として扱う roadmap 案([[hbb_reconstruction_stage_proposal]], `PROPOSAL/AWAITING_TAKA`)の
  下流。detection stage の下流に置く reconstruction 実現手段の一候補(R1-R4 の R4)。
- **未確定(Taka に要確認)**: 「分散」の単位(複数 shift 候補の並列 or 複数 seed)、「収束」の判定基準、
  STOP/SHIFT のトリガ、COMPARE の scorer(MULTI_SCORER_CONSENSUS × DETECTION/RECONSTRUCTION 前提)。
- **gate(順序は load-bearing・崩さない)**: HBB N=13 closure(二軸 consensus)→ **robust hard-core 固定** →
  R1-R4 prereg 作成 → **その後**に初めて実装可否を Taka 判定。
  raw-API cross-model arm と独立 cross-review は closure 必須でなく、**closure 後の deployment / external-validation track** に保持
  (engine 有効性 と Qwen≥GPT/Claude の deployment significance を混同しないため; cf. [[project_ai_work_system_stack]])。
- **理由(Taka 2026-07-08)**: 先に scheduler を作ってから hard-core を選ぶと、hard-core が scheduler に overfit する
  (Formal compiler v0 の origin-laundering 事故と同型)。**hard-core は scheduler 実験の ground truth**として、
  必ず今の HBB closure で先に固定する。
