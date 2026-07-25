# 実装担当 → 設計/監査担当: Task Contract に required_inputs authored 注入口を配線（BUILT・P2）

- 発: 実装インスタンス / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用**
- 対応: `CC_DESIGN_2026-07-25_TASK_CONTRACT_REQUIRED_INPUTS_WIRING_HANDOFF.md`（DE-0526 の継続・P2）
- 正本: `structure/s_task_contract.py`

## 成果物（working tree・未commit）

- `structure/s_task_contract.py`（M・配線本体）
- `structure/REQUIRED_INPUTS.jsonl`（??・authored 源・**header 種のみ／空**）
- `TASK_CONTRACTS.jsonl / READ_PATHS.jsonl / STATE_MACHINES.jsonl` は **diff ゼロ**（authored 空 → 出力完全同一＝捏造ゼロを byte で実証）

## 実装（handoff 3点そのまま・CANONICAL と同型）

1. **`REQUIRED_INPUTS.jsonl`（authored-persistent）**: `main()` は無ければ header 種のみ書き、**有れば絶対に上書きしない**（CANONICAL_STATES と同じ seed-if-absent）。1 行 = `{task_id, required_inputs:[paths], authored_by}`。build は読むだけ・auto 生成で埋めない。
2. **`build_contracts()` を merge に**: `load_required()` が `REQUIRED_INPUTS.jsonl` → `{task_id: required_inputs}`。各 task は **authored にあればその値／無ければ従来どおり `UNRESOLVED_NO_CONTRACT`**（捏造しない）。他項目（expected_outputs/allowed_writes/actually_loaded）は現状のまま決定論候補。
3. **sole-writer / 分離維持**: `TASK_CONTRACTS.jsonl` の writer は引き続き `s_task_contract`。required_inputs の**源だけ** `REQUIRED_INPUTS.jsonl` に分離（build は上書きしない）。A=ACD / C・D=task_contract の分離不変（ACD --check も GREEN・二重 writer 回帰なし）。

## ゲート（`--check` に追加・全 GREEN）

- **byte 一致再生成**（authored 値込み。実 OUT_REQ は触らず temp round-trip）。
- **authored-wiring 検出力（陰性対照・load-bearing 実測）**: `REQUIRED_INPUTS.jsonl` に1件注入 →
  - ① file→dict→merge が authored 値を**保全**（消えたら `AUTHORED_MERGE_FAILED`）
  - ② その task の C が `UNRESOLVED_NO_CONTRACT` から**脱す**（残れば `AUTHORED_WIRING_FAILED`）
  - **回帰模擬で RED 実証**: merge を旧 hardcode に戻すと両 RED（rc=1）を確認。空辞書では通らない＝空振りでない。
- 既存の C 検出力 / auto-collapse 禁止 / D 検出力の陰性対照は**不変**（GREEN）。

## 受入（設計が独立再検証してほしい点）

- あなたが `REQUIRED_INPUTS.jsonl` に1件書いて `python3 s_task_contract.py` → その task の C 行が `UNRESOLVED_NO_CONTRACT` から `OK/MISSING` に変わる（**両方 live 実証済**: MISSING=未読 required、OK=`s_account_axes` の `ACCOUNT_AXES_v1.json` 実読）。
- authored が無い task は従来どおり `UNRESOLVED_NO_CONTRACT`（現状 17/17・捏造ゼロ）。
- `--check` GREEN robust（fresh 再実行で byte 一致）。

## ハンドオフ

- 次: **設計独立再監査（byte一致 + authored 保全陰性対照 RED 実測 + 捏造ゼロ）→ CONSISTENT → commit=Taka → 単独 DE**。
- その後、設計が `REQUIRED_INPUTS.jsonl` に s-stage の required_inputs を数タスクずつ authored（P2 継続）。機構は空から生きています。

---
*実装インスタンス。★3=RTHREAD 本線は止めていません（本件 P2 並行・小配線）。想定と実測のズレ無し。*
