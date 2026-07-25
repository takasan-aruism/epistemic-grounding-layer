# 設計/監査 → 実装: meta 派生台帳の commit-境界 self-heal（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用
- 正本: `CC_MGR_2026-07-25_LLM_INVOCATIONS_RED_RECURRENCE_HANDOFF.md`（再発防止）+ IMPL FINDING（regen_meta 提案）+ 本 handoff
- 位置づけ: P2。★3 本線は止めない。**ゲートは緩めない**（fold を自動化する方向）。

## 0. 根因（一般化）
- LLM_INVOCATIONS 固有でなく「**structure/ script 集合を列挙/走査する meta 派生台帳**」全般。**LLM_INVOCATIONS + TASK_CONTRACTS** が新 structure/ script 追加のたび RED→手動 fold（5回目）。
- 即時 fold は DESIGN 側で実施済み（working tree: LLM_INVOCATIONS 232 / TASK_CONTRACTS に s_record_tags 登録 / 両 --check GREEN）。本 handoff は**再発防止機構**。

## 1. `structure/regen_meta.py`（単一エントリ・冪等・meta のみ）
- **明示 META リスト** = `["s_llm_invocations", "s_task_contract"]`（AST/source 走査のみ・**HF/GPU 非依存**。埋め込み系 stage は絶対に含めない）。増えたら1行追記（un-accounted 化しない）。
- 実行: 各 meta 生成器を regen（決定論ゆえ no-op なら差分ゼロ・何度でも安全）。
- `regen_meta.py --check`: 全 meta 台帳の `--check` を集約し、RED があれば **どの script が未 fold かを具体名で**出して非ゼロ終了（bare REGEN_MISMATCH より原因が一目）。

## 2. pre-commit hook で commit-境界 self-heal（自動化・discipline は5回失敗済み）
- **tracked `hooks/pre-commit`** を置き `git config core.hooksPath hooks` を設定（このリポjで有効化）。
- hook ロジック（**軽量・meta 限定**）:
  1. staged に `structure/*.py` が**含まれる時のみ**発火（それ以外の commit=ledger/doc は no-op＝latency ゼロ）。
  2. `python3 structure/regen_meta.py` を実行 → meta 台帳出力（LLM_INVOCATIONS / TASK_CONTRACTS / READ_PATHS）を `git add` で **再ステージ**。
  3. `python3 structure/regen_meta.py --check` → RED なら **commit を中止**（具体名を表示）。
- **絶対に埋め込み/HF stage を hook で回さない**（重い・offline lock 問題）。meta（AST 走査）限定。

## 3. やらないこと
- ゲートの緩和（MENTION_ONLY を無視する等）は禁止。ゲートは正しく検出している。
- 全 structure/ 生成器の無差別 pre-commit 実行（HF/GPU 依存を巻き込む）は禁止。

## 4. ゲート / 受入（設計が独立再検証）
- `regen_meta.py --check` GREEN（LLM_INVOCATIONS/TASK_CONTRACTS byte一致）。冪等（2回連続 regen で差分ゼロ）。
- **hook 実効性の実証**: structure/ に無害な1行を足して stage→`git commit` を試行 → hook が meta を regen+再ステージ し、意図的に stale にした meta があれば commit が中止される（load-bearing）。テスト後は無害変更を revert。
- META リストに埋め込み系 stage が無いことをコードで確認（hook が HF を回さない）。
- 私が fresh に `regen_meta.py` を回して no-op（既に fold 済みゆえ差分ゼロ）。

## 5. 完了後
- `CC_IMPL_2026-07-25_META_LEDGER_SELFHEAL_BUILT.md`（宛 AUDIT/DESIGN）→ 設計再監査 → CONSISTENT → **commit=Taka（即時 fold[LLM_INVOCATIONS/TASK_CONTRACTS/READ_PATHS] + regen_meta.py + hooks/pre-commit + core.hooksPath 設定メモ を1コミット群）** → DE 起票（P2）。
- 以後、新 structure/ script 追加時は hook が自動 fold＝commit 跨ぎ RED が構造的に起きない。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。ゲート不緩和・meta限定・自動self-heal。★3 本線・止めない。*
