# hooks/ — meta 派生台帳の commit-境界 self-heal

## 有効化（clone ごとに1回・per-clone のローカル設定）
```sh
git config core.hooksPath hooks
```
`core.hooksPath` は `.git/config`（非追跡）に書かれるため、**clone ごとに1回**実行が要る。tracked なのは `hooks/pre-commit` 本体のみ。

## pre-commit の挙動
- **`structure/*.py` が staged の時のみ発火**（それ以外の commit=ledger/doc は no-op＝latency ゼロ）。
- `python3 structure/regen_meta.py` で meta 派生台帳（`LLM_INVOCATIONS` / `TASK_CONTRACTS` / `READ_PATHS` / `STATE_MACHINES`）を regen し `git add` で再ステージ。
- `regen_meta.py --check` が RED なら（真の異常）commit を中止し具体名を表示。
- **AST 走査限定・HF/GPU/埋め込み系は絶対に回さない**（`regen_meta.py` の META リストが `s_llm_invocations`/`s_task_contract` に限定）。

## 目的
新しい `structure/` script を足すたび、script 集合を走査する meta 派生が stale 化し commit 跨ぎで gate RED が残る問題（5回発生）を構造的に断つ。ゲートは緩めない（fold を自動化するだけ）。
