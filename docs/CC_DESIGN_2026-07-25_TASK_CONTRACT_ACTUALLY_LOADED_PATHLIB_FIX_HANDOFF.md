# 設計/監査 → 実装: actually_loaded の pathlib `S/"x"` 取りこぼし修正（P2・小）

- 発: 設計/監査(CC-α) / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用**
- 正本: DE-0527(required_inputs 配線) + `structure/s_task_contract.py`(`_writes_and_reads`/`_path_of`) + 本 handoff
- **優先度: P2（低・並行）。★3=RTHREAD 本線を止めない。**

## 発見（独立検証済）
- `actually_loaded`(AST の literal-open 検出)が **pathlib の `open(S/"FILE_MANIFEST.jsonl")` 形式を拾えず**、12/17 タスクが loaded=[] という誤り。
- 実例: `s4_edges` は `open(S/"FILE_MANIFEST.jsonl")`, `open(S/"SYMBOL_INDEX.jsonl")`, `open(S/"REACHABILITY.jsonl")`, `open(S/"COMPONENT_INVENTORY.jsonl")` を読むが全て未検出。`s7_traceability` も同型。
- 現 `_path_of` は Constant / Name(const dict) / os.path.join のみ解決。**`ast.BinOp(op=Div)`(Path 割り算)を解決しない**のが原因。
- 影響: この状態で required_inputs を authored すると**偽 MISSING**（実読なのに未読判定）→ C が無意味化。**authoring 前に検出器を直す必要。**

## 依頼（最小・`Path / "literal"` の解決を足すだけ）
1. **const 解決の拡張**: モジュール先頭の `S = ...` / `STRUCT = ...` 等が Path/str を指す場合、`_path_of`（と const 収集）で **`ast.BinOp` の `op=ast.Div`** を解決:
   - `left` が既知の base（S/STRUCT/ROOT 等の Name、または入れ子 BinOp）で、`right` が str `Constant` → **末尾 str = basename** を採用。
   - 連鎖 `S/"a"/"b"` は末尾 basename（`b`）を採用（既存 basename 方針と一致）。
2. **write/read 判定は現状のまま**（`open(...,"w"/"a")`=write / それ以外=read）。`.jsonl/.json/.npy/.txt/.md` フィルタも不変。
3. **他は触らない**。required_inputs merge・CANONICAL・sole-writer 分離・A=ACD/C・D=task_contract は不変。

## ゲート（`--check` に追加）
- **byte 一致再生成**（actually_loaded が増えるので TASK_CONTRACTS/READ_PATHS は変わる=それが正）。
- **pathlib 検出の陰性対照(load-bearing)**: `s4_edges` の actually_loaded に **FILE_MANIFEST.jsonl 等が含まれる**こと（含まれなければ RED）。かつ `Path/"x"` 解決を外すと RED（回帰模擬）。
- 既存の C 検出力 / auto-collapse / D 検出力 / authored 保全の陰性対照は**不変**（GREEN）。

## 受入（設計が独立再検証）
- 私が再実行して、`s4_edges`/`s7_traceability` 等の actually_loaded が **pathlib 実読を含む**（loaded=[] が実態に直る）。
- 新規 actually_loaded の増分が**実読と一致**（捏造ゼロ・過剰検出なし）。
- 両 `--check` GREEN robust。

## 完了後
- `CC_IMPL_2026-07-25_TASK_CONTRACT_ACTUALLY_LOADED_PATHLIB_FIX_BUILT.md` → 設計再監査 → CONSISTENT → **commit=Taka** → 単独 DE。
- その後、**設計(私)が REQUIRED_INPUTS.jsonl に required_inputs を数タスクずつ authored**（正しい actually_loaded の上で・P2 継続）。

---
*設計/監査 CC-α。実装は本ファイル保存でトリガ。計器を先に直してから authoring。P2・★3 を止めない。*
