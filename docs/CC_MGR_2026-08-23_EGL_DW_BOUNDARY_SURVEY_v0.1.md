# EGL→DW 境界 全件調査 v0.1（★調査のみ・実装なし）

**作成: Claude Code（MGR／台帳側）／ 2026-08-23**
**指示: Taka「TASK/明細/PLAN lineage 改修方針」§12「実装前の全件調査」12項目。
★『branch という新概念が本当に必要か』を確定する。★私の担当は台帳側 ∴ 調査のみ。**

## 0. 結論

**概念は必要。ただし ★新しい ID 体系は不要**（`run_id` を PLAN へ広げれば表現できる見込み）。
★実装判断は DW 側の担当へ渡す。本書は**測った事実だけ**を置く。

## 1. ★決定的な事実3つ

### ① PLAN の作り直し経路は、いま構造的に存在しない
```python
_ALLOWED["PLAN"] = {"CREATED", "PLANNING"}      # dev-workcell/dw/workcell.py:482
```
一度 PLAN を記録すると二度と記録できない（`WorkflowViolation` で fail-closed）。
★実測: **600 task 中、PLAN が2回ある task は 0件**。
∴ 懸念された「同じ TASK の状態変更として受けてしまう」は**まだ起きていない**（禁止されているため）。

### ② ただし禁止を外した瞬間に、その事故が起きる
```
2本目の PLAN が入ると:
  derive_state は state を READY_FOR_IMPLEMENTATION へ戻す
  ★しかし generate_runs / audit_runs / upper_reviews は畳まれない（消えない）
  ★completion_blockers は view["generate_runs"] を全件見る
  → ★旧 PLAN の成果物で新 PLAN を「完了」にできてしまう
```
★これが §5「古い TEST が新 PLAN へ混入する事故」の**正確な発生箇所**＝ `derive_state` の view 構築。

### ③ 受け皿が既に在る
```python
view = {..., "plans": [], "sealed_contract": False}   # ★2026-08-23 に追加済（他インスタンス）
view["has_plan"] = True; view["plans"].append(e)
```
`has_plan`(bool) だけだったものが **PLAN の一覧**になっている。

## 2. §12 の12項目（全件）

| # | 項目 | 実測 |
|---|---|---|
| 1 | PLAN の再記録・置換経路 | **存在しない**（`_ALLOWED` が拒否・実績0件） |
| 2 | PLAN を読む consumer | **6箇所**。★全て `reversed(evs)` で「最後の PLAN」を取る：`live_worker_runtime.py:260` / `webui.py:387` / `webui.py:1270` / `dw/workflow.py:38` / `webui.py:259,284`（has_plan） |
| 3 | contract_seal の consumer | **12ファイル**：`contract_seal` / `request_template` / `route_table` / `handoff_contract` / `process_submission` / `domain_dw` / `progress_seal` / `submit` / `webui` / `dw/workcell` / `generate_via_runner` / `supersede_seal` |
| 4 | DW state の単位 | ★**TASK 単位**。`derive_state(task_id, events=None)`。`plan_revision` / `branch` を見る行は **0** |
| 5 | test_result の identity | ★`task_id` のみ（GENERATE/REGENERATE の payload 内）。`run_id` は event に付く |
| 6 | audit_result の identity | ★`task_id` のみ。`run_id` あり |
| 7 | disposition の identity | ★`task_id` のみ。**`run_id` なし** |
| 8 | upper_review の identity | ★`task_id` のみ。**`run_id` なし** |
| 9 | complete が見る母数 | `view["generate_runs"]` **全件** ／ `view["upper_reviews"]` **全件** |
| 10 | supersede / retry / regenerate | `create_task(supersedes=...)` は ★**task 単位**（2026-08-23 追加）。★**plan 単位ではない**。REGENERATE は同一 PLAN 内の作り直し |
| 11 | 旧成果物が新 PLAN へ混ざる場所 | ★**`derive_state` の view 構築**（`workcell.py` の fold）。state は戻るが list は畳まれない |
| 12 | branch を分けずに済む既存構造 | ★**`view["plans"]` が既に在る**。★`execution_context` 相当は **無い**（grep 0件） |

### ★run_id が付く段（実測）
```
GENERATE 405 / AUDIT 457 / REGENERATE 123
★PLAN には 付かない ／ DISPOSE・UPPER_REVIEW・COMPLETE にも 付かない
```

## 3. 新 ID 体系を作らずに済む案（★DW 側への申し送り・実装しない）

```
PLAN event に run_id を付ける            ← いま付いていない唯一の段
GENERATE/AUDIT/… は その PLAN の run_id を引き継ぐ
実行系列を run_id で畳む                 ← 旧 PLAN の成果物が新 PLAN に混ざらない
branch_reason は 既存 `supersedes` の作法（前向き宣言）に合わせる
```
★`execution_branch_id` を新設せず、**`run_id` を実行系列の鍵として使う**。

### §9「DW 改修を最小に」への適合
`derive_state(task_id, events=None)` は ★**既に events を受け取れる** ∴
**入口（`dispatch.next_legal_operation` / `dispatch_once`）で events を run_id で絞って渡す**方が、
`derive_state` 本体を変えるより改修範囲が小さい。
★GENERATE / TEST / AUDIT / DISPOSE / UPPER_REVIEW は **branch を理解しなくてよい**（§9 の狙いと一致）。

## 4. ★未確認（隠さない）
- 上の案で `completion_blockers` の母数が正しく絞れるかは**未検証**（実装していない）
- `run_id` を PLAN に付けたとき、既存 405+457+123 件の run_id を持つ event との**互換**は未測定
- REGENERATE を「同一 branch 内」とみなすか「新 branch」とみなすかは ★§6 の判定条件に依存し、未確定
