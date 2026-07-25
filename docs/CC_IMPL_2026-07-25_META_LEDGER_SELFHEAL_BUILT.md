# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): meta 派生台帳の commit-境界 self-heal（BUILT・P2）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用
- 対応: `CC_DESIGN_2026-07-25_META_LEDGER_SELFHEAL_HANDOFF.md`（私の regen_meta 提案が採用）

## 成果物（working tree・未commit）
- `structure/regen_meta.py`（単一エントリ・冪等・meta 限定）
- `hooks/pre-commit`（tracked・実行可）+ `hooks/README.md`（`core.hooksPath` 有効化メモ）
- `core.hooksPath=hooks` を local config に設定済み（非追跡ゆえ README に手順記録）
- 即時 fold（working tree・M）: `LLM_INVOCATIONS`(232) / `TASK_CONTRACTS`(19契約・s_record_tags 登録) / `READ_PATHS`

## 実装（handoff §1-2・ゲート不緩和・meta 限定）
- **`regen_meta.py`**: 明示 META = `["s_llm_invocations", "s_task_contract"]`（AST/source 走査のみ・**HF/GPU 非依存**・埋め込み系は絶対含めない）。regen は冪等（no-op なら差分ゼロ）。`--check` は各 meta の --check を集約し RED なら**未 fold の meta を具体名で**出し非ゼロ終了。
- **`hooks/pre-commit`**（軽量・meta 限定）:
  1. `structure/*.py` が staged の時のみ発火（他 commit=no-op・latency ゼロ）。
  2. `regen_meta.py` で meta を regen → `git add` で `LLM_INVOCATIONS/TASK_CONTRACTS/READ_PATHS/STATE_MACHINES` を再ステージ。
  3. `regen_meta.py --check` RED なら commit 中止（具体名表示）。
  - **埋め込み/HF stage は hook で一切回さない**（META リストで構造的に排除）。

## 検証（受入 §4・load-bearing 実測）
- **`regen_meta.py --check` GREEN**（LLM_INVOCATIONS/TASK_CONTRACTS byte一致）。**冪等**（2回連続 regen で差分ゼロ）。
- **META に埋め込み系が無いことをコードで確認**（`s_embed_axes/account/rthread/mine` 非含有を assert）。hook が HF を回さない。
- **hook 実効性（self-heal）実測**: LLM_INVOCATIONS を committed(231・stale)へ戻し + structure/*.py 変更を stage → `hooks/pre-commit` 実行 → **232 へ再 fold + 再ステージ + exit 0**。
- **hook 実効性（git 統合 + abort）実測**: 壊れた `s_zzz_broken.py`（syntax error）を stage → `git commit` → hook が regen_meta 実行 → s_task_contract が AST parse で失敗 → **commit を中止（HEAD 不変=commit 生成ゼロ）**。＝git が `core.hooksPath=hooks` を呼び、abort が load-bearing。
- **commit=Taka 尊重**: テストは abort パス（commit 生成なし）と直接呼出のみ。成功パスで実 commit を作らず、痕跡（s_zzz_broken / regen_meta テスト行 / staged）は全 revert。
- 全 gate GREEN: regen_meta / s_llm_invocations / s_task_contract / s_record_tags / s_embed_axes / s_account_axes / s_rthread_2br3 / s_exec_arch_acd / s_mine_accounts。

## やらなかったこと（handoff §3 遵守）
- ゲート緩和なし（MENTION_ONLY 検出は正しい・そのまま）。
- 全 structure/ 生成器の無差別 pre-commit 実行なし（HF/GPU を巻き込まない）。

## ハンドオフ
- 次: 設計再監査（regen_meta --check GREEN・冪等・META 軽量・hook self-heal + abort 実効）→ commit=Taka（即時 fold[LLM_INVOCATIONS/TASK_CONTRACTS/READ_PATHS] + regen_meta.py + hooks/pre-commit + hooks/README.md を1コミット群）→ DE 起票（P2）。
- 以後、新 structure/ script 追加時は hook が自動 fold＝commit 跨ぎ RED が構造的に起きない。
- 注: `core.hooksPath` は per-clone のローカル設定（README に手順）。commit 群には hooks/ 本体が入るが有効化は各 clone で1回。

---
*実装(IMPL)。ゲート不緩和・meta限定・自動 self-heal。commit=Taka を尊重しテストは非破壊。★3 本線は止めていません。*
