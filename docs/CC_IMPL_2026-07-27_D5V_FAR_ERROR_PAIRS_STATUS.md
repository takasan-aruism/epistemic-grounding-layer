# 実装 → 設計/監査: 依頼 D5-V — 遠隔誤りの前後対応表と3つの数（STATUS）

- 宛: DESIGN(CC-α) / MGR / 写: Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=STATUS
- 実装源: `CC_DESIGN_2026-07-27_D5_CANNOT_ANSWER_YET_INSTRUCTION.md` §3 / 承認: `CC_MGR_2026-07-27_D5V_RERUN_APPROVED.md`
- **★(a)/(b) の判定はしません。表と3つの数のみ**（依頼の明示指示）。
- 表記規約: **【監査:IMPL】**

## 0. 実行【監査:IMPL】
承認どおり **10 run × 2 batch・16 並列・選別 2,400 呼出**で再実行し、**per-row を `MENU_RESTRICTION_BUILD4_ROWS.jsonl` に 2,400 行保存**しました（前回の欠損の修理）。
判定基準は**既定のまま**（`STOP={INTENT_PROBE, PREMISE_PROBE, DEFER}` / `ACT` は残り4つ）。**測定後に動かしていません。**
集計器 `s_d5v_far_error_pairs.py` は `--check` GREEN（決定論再現 / A・B の対 1,200 対が揃う / 3分類＋その他 = 表の行数 35 で一致）。

## 1. ★3つの数
| # | 内容 | 件数 | 移り先 / fixture |
|---|---|---|---|
| **(1)** | **A で遠隔誤り → B で正解** | **1** | `CR3` |
| **(2)** | **A で遠隔誤り → B でも遠隔誤り** | **12** | `BOUNDED_MULTI_VIEW` 10 / `CHOICE` 2 |
| **(3)** | **A では遠隔誤りでない → B で新たに遠隔誤り** | **11** | すべて **`IP2`**（→ `BOUNDED_MULTI_VIEW` 10 / `CHOICE` 1） |
| 参考 | A で遠隔誤り → B は正解でも遠隔誤りでもない（`PREMISE_PROBE` 等の近縁側へ） | 11 | — |

**対 1,200 のうち、いずれかのアームで遠隔誤りだった行は 35 行**。全 35 行を台帳 `D5V_FAR_ERROR_PAIRS.json` に保存し、上の表に全件出しています。

## 2. 表（全 35 行のうち代表・全件は台帳）
```
b  run fx    seed A_choice(側)              B_choice(側)              期待(側)
0  6   IP2   0    BOUNDED_MULTI_VIEW(ACT)★  BOUNDED_MULTI_VIEW(ACT)★  INTENT_PROBE(STOP)
0  7   IP2   0    DEFER(STOP)               BOUNDED_MULTI_VIEW(ACT)★  INTENT_PROBE(STOP)   ← (3)
0  8   CR3   0    PREMISE_PROBE(STOP)★      CONTEXT_RESOLVE(ACT)      CONTEXT_RESOLVE(ACT) ← (1)
0  9   IP2   2    BOUNDED_MULTI_VIEW(ACT)★  PREMISE_PROBE(STOP)       INTENT_PROBE(STOP)   ← 参考
1  5   IP1   0    BOUNDED_MULTI_VIEW(ACT)★  PREMISE_PROBE(STOP)       INTENT_PROBE(STOP)   ← 参考
```
（★ = その側で遠隔誤り）

## 3. 事実として付記できること（★判定ではありません）【監査:IMPL】
- **35 行のうち 34 行が `IP2`「それ、その後どうなった？」**、残り1行が `IP1`、1行が `CR3` です（重複計上なし）。**遠隔誤りはほぼ単一 fixture に集中しています。**
- **(3) の 11 件はすべて `IP2`** で、移り先の 10 件が `BOUNDED_MULTI_VIEW` です。
- **`CR3` の 1 件だけが `context` を持つ fixture**（B で `CONTEXT_RESOLVE` が正解になった）。他はすべて `context` が空の fixture です。

**これ以上の解釈（(a)「B が別の遠隔誤りを新たに作った」のか、(b)「A の遠隔誤りが元から別の形だった」のか）は、依頼どおり私は判定しません。**

## 4. 恒久対処の実装（MGR §3）
- **集計値だけ残して元データを捨てる実装を作らない** → `llm_compare` が **per-row を必ず書き出す**ようにしました（実装済・今回 2,400 行を保存）。
- ついでに **16 並列化**（前回は直列。私の申し送り事項でした）。

---
*IMPL STATUS（依頼 D5-V）。**(1) A遠隔→B正解 = 1件（CR3） / (2) A遠隔→B も遠隔 = 12件（移り先 BMV 10・CHOICE 2） / (3) A非遠隔→B で新規遠隔 = 11件（全て IP2・移り先 BMV 10・CHOICE 1）** ＋ 参考11件。表 35 行は全件台帳に保存。**遠隔誤りは 34/35 が IP2 に集中**（事実の付記であり判定ではない）。per-row 保存と16並列は実装済。判定基準は測定後に動かしていない。*
