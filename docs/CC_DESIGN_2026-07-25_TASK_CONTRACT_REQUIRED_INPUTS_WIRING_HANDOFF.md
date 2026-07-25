# 設計/監査 → 実装: Task Contract に required_inputs の authored 注入口を配線（P2・小）

- 発: 設計/監査(CC-α) / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用**
- 正本: DE-0526(Task Contract 機械+種) + `structure/s_task_contract.py` + 本 handoff
- **優先度: P2（低・並行）。★3=RTHREAD 本線を止めない。**
- 発見: 現状 `build_contracts()` は `required_inputs` を毎 build で `"UNRESOLVED_NO_CONTRACT"` にハードコード（line 97）。CANONICAL_STATES は authored-persistent だが、**required_inputs の authored 経路が欠落**。設計が seed を埋められない。

## 依頼（CANONICAL と同じ型を required_inputs にも・最小）

### 1. 新 authored ファイル `structure/REQUIRED_INPUTS.jsonl`
- 1 行 = `{task_id, required_inputs:[paths], authored_by}`。
- **authored-persistent**: `main()` は**無ければ header 種のみ書き、有れば絶対に上書きしない**（CANONICAL_STATES と同じ扱い・line 222 パターン）。
- 空で始めてよい。書くのは設計/人。build は読むだけ。

### 2. `build_contracts()` を merge に
- `REQUIRED_INPUTS.jsonl` を読み `{task_id: required_inputs}` を作る。
- 各 task で **authored にあれば その値／無ければ従来どおり `"UNRESOLVED_NO_CONTRACT"`**（捏造しない）。
- 他項目（expected_outputs/allowed_writes/actually_loaded）は現状のまま決定論候補。

### 3. sole-writer / 規律
- `TASK_CONTRACTS.jsonl` の writer は引き続き `s_task_contract`（required_inputs の**源**が REQUIRED_INPUTS.jsonl に分離されるだけ）。
- `REQUIRED_INPUTS.jsonl` は authored источник＝build が上書きしない（seed-if-absent のみ）。**auto 生成で埋めない。**
- A=ACD / C・D=task_contract の分離維持。

## ゲート（`--check` に追加）
- **byte 一致再生成**（authored 値込みで TASK_CONTRACTS/READ_PATHS が再現）。
- **authored 保全（陰性対照）**: `REQUIRED_INPUTS.jsonl` に1件注入 → build 後もその task の `required_inputs` が authored 値のまま（消えたら RED）。かつ C がその task を `MISSING`/`OK` で判定（`UNRESOLVED_NO_CONTRACT` から脱すること）。
- 既存の C 検出力/auto-collapse/D 検出力の陰性対照は不変。

## 受入
- 私が `REQUIRED_INPUTS.jsonl` に1件書いて build → その task の C 行が `UNRESOLVED_NO_CONTRACT` から `OK/MISSING` に変わる（authored 経路が生きている）。
- authored が無い task は従来どおり `UNRESOLVED_NO_CONTRACT`（捏造ゼロ）。
- `--check` GREEN robust（私の再実行で byte 一致）。

## 完了後
- `CC_IMPL_2026-07-25_TASK_CONTRACT_REQUIRED_INPUTS_WIRING_BUILT.md` → 設計再監査 → CONSISTENT → **commit=Taka** → 単独 DE。
- その後、**設計(私)が REQUIRED_INPUTS.jsonl に s-stage の required_inputs を数タスクずつ authored**（P2 継続）。

---
*設計/監査 CC-α。実装は本ファイル保存でトリガ。最小配線・P2。★3 を止めない。*
