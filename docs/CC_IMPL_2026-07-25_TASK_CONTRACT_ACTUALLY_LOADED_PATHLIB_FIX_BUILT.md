# 実装担当 → 設計/監査担当: actually_loaded の pathlib `S/"x"` 取りこぼし修正（BUILT・P2）

- 発: 実装インスタンス / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用**
- 対応: `CC_DESIGN_2026-07-25_TASK_CONTRACT_ACTUALLY_LOADED_PATHLIB_FIX_HANDOFF.md`
- 正本: `structure/s_task_contract.py`（`_binop_basename`/`_path_of`/const 収集/`--check`）

## 成果物（working tree・未commit）

- `structure/s_task_contract.py`（M・`_binop_basename` 追加 + `_path_of`/const 拡張 + pathlib 陰性対照）
- `TASK_CONTRACTS.jsonl / READ_PATHS.jsonl`（M・actually_loaded 増分＝正・handoff §ゲート通り「変わるのが正」）

## 実装（handoff 依頼どおり最小・他不触）

1. **`_binop_basename(node)`**: `ast.BinOp(op=Div)` かつ `right` が str `Constant` → 末尾 str = basename。連鎖 `S/"a"/"b"` は末尾（`b`）。base の中身は問わない（basename のみ要）。
2. **`_path_of` 拡張**: `_join_literal(node) or _binop_basename(node)`。const 収集も `OUT = S/"X.jsonl"` を解決。
3. write/read 判定・拡張子フィルタ・required_inputs merge・CANONICAL・sole-writer・A=ACD/C・D=task_contract は**不変**。

## 検証（陰性対照 load-bearing 実測）

- **pathlib 検出（陰性対照）**: `s4_edges` の actually_loaded に `FILE_MANIFEST.jsonl` 等が含まれること。**回帰模擬（Path/"x" 解決を無効化）で `PATHLIB_DETECTION_FAILED` + `REGEN_MISMATCH` RED（rc=1）を確認**＝空振りでない。
- **byte 一致再生成**: 2 回 regen が完全一致（STABLE）。両 `--check` GREEN。
- **s4_edges 実測**: reads = `[COMPONENT_INVENTORY, FILE_MANIFEST, REACHABILITY, SYMBOL_INDEX].jsonl`（4件・全て実読・過剰検出なし）。従来 `[]` → 実態に修正。
- 既存陰性対照（C 検出力 / auto-collapse 禁止 / D 検出力 / authored 保全）は不変 GREEN。

## ★ 正直な flag（handoff の s7 想定と実態が違う・裁定候補）

handoff §受入は「`s4_edges`/`s7_traceability` 等が pathlib 実読を含む」ですが、**s7_traceability は s4 と同型（直接 `open(S/"x")`）ではありません**。

- `s7_traceability`（7-14行）: `J = lambda p: [json.loads(l) for l in open(p) if l.strip()]` という**ヘルパ経由**で読み（`J(S/"FILE_MANIFEST.jsonl")` …7件 + `J(HOME/"twoder/...")` …複数）、書込は `(S/"ITEM_LADDER.jsonl").write_text(...)`（68行）＝**pathlib write**。
- 私の修正（`open(S/"x")` の直接 Div 解決）は **ヘルパ関数呼び出しの引数**や **`.read_text()`/`.write_text()`** には届かない。よって **s7 の actually_loaded は依然 `[]`（偽陰性が残存）**。
- これは handoff スコープ「Path/'literal' の解決を足すだけ・他は触らない」を**超える判断**（どのヘルパを"reader"とみなすか / write_text も対象か / 多引数ラッパは）なので、**独断で拡張せず flag します**。s7 の required_inputs を今 authoring すると偽 MISSING になります（handoff の懸念どおり）。

### s7 対応の裁定候補（お任せ）
- (a) 別 handoff で「単一 `open(引数)` のリーダ・ヘルパ呼び出し追跡 + pathlib `read_text`/`write_text`」を追加（中規模・独自の偽陽性リスクあり）。
- (b) s7 系は authoring 対象から当面除外し、直接 open のタスクから required_inputs を authoring。

## ★ 残 `[]` タスクの性質（誤検出でなく真の空を確認）

- `s1_manifest` / `s5_history` の `actually_loaded=[]` は **正しい**（`os.walk` + `subprocess`(git) のソース/履歴走査で jsonl 入力なし）。取りこぼしではない。
- ∴ 修正後の偽陰性は **s7_traceability のみ**（ヘルパ経由・上記 flag）。

## ハンドオフ

- 次: **設計独立再監査（byte一致 + pathlib 陰性対照 RED 実測 + 増分が実読一致 + s7 flag 裁定）→ CONSISTENT → commit=Taka → 単独 DE**。
- s7 の扱いを裁定いただければ、(a) 採用時は別ビルドで対応します。過剰主張より正直な偽陰性の開示を優先しました。

---
*実装インスタンス。★3=RTHREAD 本線は止めていません（P2 並行）。計器を authoring 前に直す趣旨に沿い、s4 は直し・s7 の型差は独断拡張せず flag。*
