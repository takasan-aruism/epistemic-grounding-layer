# CC 設計整合監査 — TOKEN 配線（SPEC_TOKEN_WIRING_v0_1）

- 監査者: Claude Code（CC-α）/ 2026-07-23
- 対象: `twoder/approval_registry.py`（アダプタ追加）＋ 6ファイル（Part B）＋ `probe/conformance_probe.py`（Part C）
- 正本: `SPEC_TOKEN_WIRING_v0_1.md` / ハーネス: `egl/docs/audit_token_wiring.py`
- **verdict（配線本体）: CONSISTENT**

## 配線監査（CONSISTENT）

| チェック | 結果 |
|---|---|
| C1 Part A アダプタ3関数＋既存3関数不変＋§2 骨格保存 | green |
| C2 Part A `test_token_wiring.py` 6/6＋verbatim（族C: forged/ignored 含む） | green |
| C3 Part B 6経路 rewire（`validate_by_token`＋import・旧直呼び無し） | green |
| C4 Part C probe §5 T1–T12 | green（10/10） |
| C5 再走行 `gate1_token`=green（死因#4 消滅） | green（`BREAKAGE_LIST_2026-07-23_rerun.jsonl`） |

配線は SPEC を正確に反映。**gate1_token（死因#4）は消えた。**

## ★重要所見: `gate1b_ts` の DIRECT は「実欠陥」ではなく「計器の SPEC 逸脱」（族E・計器を疑う）

再走行で `gate1b_ts` が DIRECT に unmask。実装インスタンスは「death#2、次は `generate_via_runner.py:45` の hardcoded 既定 ts 撤去」と解釈した。**これは計器の誤検出。**

- **SPEC**（CONFORMANCE_PROBE v0.3/v0.4）の gate1b ＝「**実 mint 経路（`mint_token`）を2回**通し `approval_id` が相異なること」。
- **実装**（`conformance_probe.py:229-238` `_gate1b_ts`）＝ `grant_approval` を**同一引数で直呼び**（`mint = bind_real("…mint_token")` を取得するが**未使用**）。
- **検証（実コード実行・決定的）:**
  - 実 mint 経路 `mint_token(attempt=1/2, task_id="T-DEATH2")` → `approval_id` **相異**（`APPROVAL-ab0452ce85` / `APPROVAL-8e31e7da5e`）＝ **death#2 は実経路で退化していない**（`mint_token` は attempt を task_id に含めるため）。
  - `grant_approval` 同一引数2回 → **同一**（`approval_id = sha1(task_id|op|action|ts)` の決定論の自明な帰結）。
- **結論:** `gate1b_ts` の DIRECT は、probe が SPEC を逸脱して `grant_approval` の決定論を測っているだけ。**実 mint 経路の attempt 機構により death#2 は CLOSED。**

## 次工程（修正の的が変わる）

- ❌ **death#2（`generate_via_runner.py:45` の ts 撤去）は不要**。実経路は attempt で非退化。
- ✅ **probe の `_gate1b_ts` を SPEC 準拠（`mint_token` を attempt 違いで2回）に直す** → `gate1b` green → 再走行で **DIRECT 無し** → **★3(B) DONE**。
- 前回 CONFORMANCE_PROBE 監査（CONSISTENT）は §5 T1–T12＋骨格保存＋spy 規律までで、**各 gate 実装の callee 準拠（gate1b が実 mint 経路 `mint_token` を使うか）を検証していなかった**。今回 DIRECT を精査して逸脱が発覚（監査の深化点・自己記録）。

## claim ceiling

- 配線本体は CONSISTENT（死因#4 消滅）。
- `gate1b_ts` の DIRECT は**計器欠陥**であり実欠陥ではない（検証で確定）。probe `_gate1b_ts` を SPEC 準拠に直せば ★3(B) は DIRECT 無しで DONE 見込み。
- 人間の扉: commit=Taka（配線 M7ファイル ＋ token-gate `?? approval_registry.py`・tests）。
