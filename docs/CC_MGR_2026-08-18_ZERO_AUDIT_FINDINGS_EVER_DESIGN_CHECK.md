# 宛: 設計 / 監査 ―― `zero_audit_findings_ever` の設計意図確認（修正なし）

## 0. 結論

**停止は仕様どおり。設計欠落でも実装不一致でもない。修正は不要。**
`zero_audit_findings_ever` は**完了不変条件ではない** ―― **機械が自動で上級監査を PASS してよいか**の条件。

## 1. 正本（`dev-workcell/dw/upper_review_gate.py` 逐語）

> "...recorded DW state has nothing to review. For that subset only, this deterministically records a machine
> UPPER_REVIEW PASS with the checked invariants as its evidence trail. **Everything non-trivial stays a Claude barrier.**"
> "This is **NOT an authority approval** (audit AMEND-2DER-SUPERVISOR-AUDIT-001 P0-3): it is a deterministic gate for the
> trivial case. **The FINAL completion claim still goes through the PROPOSE_COMPLETE gate**...
> Same mechanize-only-the-rule-based-slice pattern as DISPOSE(0185)/PLAN(0007)."

**∴ 意図** ―― 「一度も所見が出ていない＝**見るべき物が無い**」ものだけ機械が自動で通す。
所見が出た時点で「自明ではない」ので、**設計上わざと Claude の関門に置く。**

## 2. 修正済み task の復帰経路 ―― **在る**

`dispatch.py::_MAP` 上:
```
DISPOSITION_REQUIRED →DISPOSE(MANAGER)→ READY_FOR_REGENERATE →REGENERATE→ READY_FOR_AUDIT
  →AUDIT→ READY_FOR_UPPER_REVIEW →UPPER_REVIEW(CLAUDE_SENIOR)→ PROPOSE_COMPLETE → COMPLETE
```
**機械の自動 PASS には戻れない**が、**完了経路そのものは閉じていない**。
必要なのは `CLAUDE_SENIOR` が UPPER_REVIEW で PASS を出すこと。

## 3. 「過去に所見があった」と「現在 未処分0」は **別概念として定義済み**

```python
"zero_audit_findings_ever": len(findings) == 0,                    # ★履歴
"no_open_dispositions": not (view.get("latest_dispositions") or {}) # ★現在
```
両方が別の欄として `evidence()` に在る。**区別は既に付いている。**

## 4. 履歴を残したまま「現在 clean」へ復帰する状態 ―― **在る（ただし自動PASSは復活しない）**

`no_open_dispositions=true` / `completion_blockers_empty=true` へは戻れる。
しかし `trivially_clean = all(inv.values())` なので、`ever` と `no_rework` が false の限り
**機械の自動 PASS は二度と効かない**。**これは意図**（"Everything non-trivial stays a Claude barrier"）。

## 5. 実測（今回の2件＋対照1件）

| | state | n_findings | rework | last_test_passed | zero_audit_findings_ever |
|---|---|---|---|---|---|
| ★対照 1B79DD10 | **COMPLETE** | **0** | 0 | **true** | **true** |
| ★止2 72833830 | JUDGE_REQUIRED | 1 | 0 | false | false |
| ★止1 7C7AE062 | JUDGE_REQUIRED | 2 | 1 | false | false |

**対照が通ったのは実力ではなく、監査所見が0件で `trivially_clean` に入ったから。**
**止まった2件は `last_test_passed=false` ―― 実装が封印試験に通っていない。**
判定者の「完了させてよい根拠が無い」は**正しい**。

## 6. 過去の修正との関係（Taka の記憶の裏取り）

`egl/docs/CC_DESIGN_2026-08-08_BUILD_SPEC_SHOW_THE_ARTIFACT_TO_THE_JUDGE.md`（逐語）:
> 上級監査は **11回** 走り、毎回 中身の在る FAIL を返していた。
> 原因＝**判定者に渡している材料は6つだけ**（成果物も sha も試験の詳細も渡していない）。
> ∴ **判定者は正しい。見えない物を『在る』とは言えない。**

**処置は `latest_test_result`（成果物と試験結果を判定者に見せる純関数）。**
**現在も繋がっている**（実測: `twoder/senior_review.py` に `latest_test_result` 2箇所・`build_prompt` 2箇所）。

**∴ ケースは違う。** 08-08 は「材料が渡っていない」。今回は「**材料は渡っているが、実装が試験に落ちている**」。
`zero_audit_findings_ever` は当時も今回も**原因ではない**。

## 7. 変更対象 ―― **なし**

修正は要らない。必要なのは **`DISPOSE`（MANAGER）と `UPPER_REVIEW`（CLAUDE_SENIOR）を実行すること**＝**私の手番**。

## 8. 私の誤報の訂正（記録として残す）

| 私が報告したこと | 実測 |
|---|---|
| 「`run_until_barrier` が GENERATE を飛ばす」 | **誤り**。止まった3件とも GENERATE は走っていた |
| 「出口が構造上ない」 | **誤り**。完了経路は開いている（機械の自動PASSだけが戻らない） |
| 「JUDGE/DISPOSITION の滞留に触れないと進めない」 | **誤り**。`DISPOSE` も `UPPER_REVIEW` も**私に割り当てられた工程** |

**3件とも、片側の記録だけを見て断定した。** 工程列と不変条件を引いたら全部覆った。
