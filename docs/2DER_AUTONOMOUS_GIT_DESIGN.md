# 2DER Autonomous Git — design + policy proposal (off-ramp workstream C)

> 設計 + policy 提案のみ。**有効化は Taka 判断**。現行 standing policy = commit=Taka / 自律RD未有効。実装した機構
> (twoder.autonomous_git)は `AUTONOMOUS_GIT_ENABLED=False` で **DISABLED**、有効化には Taka の記録された policy 決定
> (DE + CHG)が要る。本 workstream は git 窓口を私から外すための設計であり、勝手に自律 commit を回すものではない。

## 1. 問題
現在 git commit/push は全て私(Claude Code)が実行している = git 窓口が私に固定。off-ramp の一環として、**台帳追記の
commit を 2DER 側で(限定的・ゲート付きで)自律化**し、私を外す。ただし過剰自律は危険なので保守的に設計する。

## 2. 保守的スコープ（何を自律化してよいか）
- **自律可**: **ledger/registry の append のみ**（DE 台帳 / CHANGE_LOG / ARTIFACT_REGISTRY / ROADMAP_REGISTRY /
  各 *_LEDGER.jsonl）。これらは append-only の記録で、内容は既存の sole-writer 機構(de_admission / artifact_registry)
  が検証済み。commit はその記録を git 履歴に固定するだけ。
- **人間必須（自律不可）**: **コード変更(.py)・docs・spec** の commit。設計・実装の変更は人間承認を要する。
- `is_ledger_path()` が分類。code が1つでも混じれば `within_autonomous_scope=False` + blocker。

## 3. ゲート（commit_gate）
自律 commit が許可される条件（全て AND）:
1. `AUTONOMOUS_GIT_ENABLED=True`（policy 有効化、既定 False）
2. `within_autonomous_scope`（ledger-only、code 無し）
3. blocker 無し
4. **scoped GIT_COMMIT approval token が有効**（authority.validate_approval、bare boolean 不可、task=repo/op=GIT_COMMIT
   束縛、single-use または standing scoped grant）
既定では条件1が偽なので、**live では常に deny**。`execute_commit` はゲート拒否時は refuse、許可時でも本設計モジュールは
live git を実行しない（実行は Taka 有効化後の別ステップ）。

## 4. Policy 提案（Taka 判断待ち）
- **提案 A（推奨・最小）**: ledger-only append の自律 commit を、**repo 毎の standing scoped grant**（operation_class=
  GIT_COMMIT、approved_by=taka、approved_scope=["GIT_COMMIT"]、失効あり）の下で許可。code は従来通り人間。有効化 =
  `AUTONOMOUS_GIT_ENABLED=True` + standing grant を DE/CHG で記録。
- **提案 B（より保守的）**: 自律化しない。commit proposal を UI(command surface)に出し、Taka が承認ボタンで token を
  発行 → その token で 2DER が commit。人間が1クリック残る（半自律）。
- どちらでも **push は別 operation**（GIT_PUSH）として扱い、default branch(main/master)への push は追加 policy を課す。

## 5. 安全設計
- **branch 保護**: main/master への自律 commit は保守的（提案では ledger append のみ許容、force-push 禁止、履歴書換禁止）。
- **監査**: 自律 commit も CHANGE_LOG に記録（既存機構）+ approval_id を紐付け（DS AUTHORITY_APPROVAL_GRANT/CONSUMED）。
- **rollback**: append-only なので revert 容易。異常時は AUTONOMOUS_GIT_ENABLED=False に即戻す kill-switch。
- **kill-switch**: `AUTONOMOUS_GIT_ENABLED` 単一フラグで全停止。

## 6. 有効化に要るもの（Taka）
1. 提案 A/B の選択
2. `AUTONOMOUS_GIT_ENABLED=True` の policy 決定を DE + CHG で記録（approved_by=taka）
3. （提案 A なら）repo 毎 standing scoped GIT_COMMIT grant の発行
4. push policy（GIT_PUSH / branch）の確定
これらが揃うまで機構は DISABLED のまま。**「設計した / 機構がある」≠「git 窓口が私から外れた」** — 外れるのは Taka が
有効化し、実際に 2DER が私なしで ledger commit を回した counterfactual run が記録された時。

## 7. 実装状況（本 workstream）
- `twoder/autonomous_git.py`: propose_commit / commit_gate / execute_commit（DISABLED）+ is_ledger_path。test 11/11。
- **未実施**: 有効化、live git 実行の配線、standing grant 発行、push policy。全て Taka 判断。
