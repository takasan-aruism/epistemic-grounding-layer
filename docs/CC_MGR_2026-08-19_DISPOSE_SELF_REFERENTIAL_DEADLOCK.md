# 宛: Taka / 設計 / 監査 ―― **DISPOSE を直す契約が、DISPOSE で止まった**（自己言及の行き止まり）

**Claude は DISPOSE していない。実装していない。`run_next` を叩いていない。Taka に途中裁定を求めていない。**

## 0. 結論

```
★★完了条件（judgment-required → headless Claude → disposition記録 → 自走再開）= ★不成立
★★理由 = ★★DISPOSE の 欠落を 直す 契約が ★その DISPOSE の 欠落で 止まった。
★Claude が 代行すれば 越えられるが ★★それは 今回 禁じられた 行為 ∴ ★していない。
```

## 1. 実測（★2件・同じ形）

| | 前の契約 | 今回の契約 |
|---|---|---|
| 文書 | `CC_DESIGN_2026-08-19_CONTRACT_TASKS_TO_ENQUEUE.md` | `CC_DESIGN_2026-08-19_CONTRACT_DISPOSE_DECISION.md` |
| 部品 | `tasks_to_enqueue`（封印試験16本） | `dispose_decision`（封印試験17本） |
| task | TASK-2DER-4E2A58F2 | **TASK-2DER-6AC3EA20** |
| 常駐が投げたか | ★自力（3分） | **★自力（★already 77→78）** |
| PLAN | ★越えた | **★越えた（1分）** |
| GENERATE / TEST | ★通った | **★通った（`last_test_passed = True`）** |
| AUDIT | ★Qwen が実施 | **★Qwen が実施** |
| 現在 | DISPOSITION_REQUIRED | **DISPOSITION_REQUIRED** |
| `mechanically_dispositionable` | ★False | **★False** |
| `dispose_runs` | 0 | **0** |

### 今回の走行（★1分刻み・GM と manager_v0 の正規面）

```
0分 queue ["TASK-2DER-6AC3EA20"] ／ CREATED  ／ PLAN     ／ who CLAUDE
1分 同                            ／ READY_FOR_IMPLEMENTATION ／ GENERATE ／ who MACHINE
2分 同                            ／ ★DISPOSITION_REQUIRED   ／ DISPOSE  ／ who CLAUDE
```

**★2分で PLAN・GENERATE・TEST・AUDIT を通り、★DISPOSE で止まった。**

### 所見（★category だけ写す。★中身は評価しない）

```
今回 : scope_expansion 1 ／ requirement_not_implemented 1 ／ self_report_primitive 1
前回 : scope_expansion 1 ／ requirement_not_implemented 1 ／ self_report_primitive 1
★★2件とも 同じ 3カテゴリ（★事実として 記録する。★意味は 私が 判断しない）
```

## 2. ★行き止まりの形

```
DISPOSE の judgment-required を 越える 仕組み（dispose_decision）を 作る
   → その 契約自身が ★judgment-required で 止まる
   → 越えるには ★Claude が DISPOSE する 必要が 在る
   → ★今回の 指示は それを 禁じている
```

**★これは実装の失敗ではない。★機構が設計どおり fail-closed で止まっている。**

## 3. ★越え方の候補（★私は実行していない・★Taka 裁定）

```
A. ★今回1件だけ Claude が DISPOSE する（★ブートストラップ）
   → ★以後は dispose_decision が 効き ★自走する
   → ★実測の 前例が 在る: claude-manager による DISPOSE = ★11回
   → ★安全境界を 変えない（★1件の 判断を Claude が する だけ）
   → ★但し「Claude が 代行しない」の 今回の 指示に 触れる ∴ ★Taka の 一言が 要る

B. ★headless claude（`claude -p`）を DISPOSE 用に 先に 呼ぶ
   → ★これが まさに この契約が 作ろうとしている 物 ∴ ★まだ 無い

C. ★所見を 減らす（★契約を 直して 再投入）
   → ★2件とも 同じ 3カテゴリが 出た ∴ ★同じ所で 止まる 見込み（★未検証）
```

**★私の見立て（★決定ではない）: A が最小。★1件だけ Claude が判断すれば、以後の同種は機械が回す。**
**★これは「Claude ゼロ」ではなく「Claude をほとんど使わない」という Taka の方針とも整合する。**

## 4. ★いま塞がっているもの（★実数）

```
DISPOSITION_REQUIRED で 止まっている task = ★25件（★2026-08-19 04:41 実測）
   うち judgment-required = ★18件 ／ 機械処分可なのに 止まっている = 7件
★今夜 増えた 2件（4E2A58F2 / 6AC3EA20）は この 18件に 含まれる
★どちらも ★試験は 通っている（★実装は 出来ている）
```

## 5. 報告

```
★自走距離        = ★PLAN → GENERATE → TEST → AUDIT（★2分・★前回と 同じ）
★止まった段      = ★DISPOSE（★同じ場所・★同じ理由）
★Claude の DISPOSE 判断 = ★0
★Taka 途中裁定   = ★0
★新規実装        = ★0 行 ／ 新しい 判断規則 = ★0
★完了条件        = ★不成立（★自己言及の 行き止まり）
★次の1手         = ★Taka の 一言（★上の A / B / C）
```

## 6. していないこと

```
★DISPOSE を 代行していない ／ run_next 0 ／ 所見を 手で 処分していない
★_MAP / _TEST_CATEGORIES / disposition 規則を 触っていない
★契約本文を 読んで 評価していない ／ 所見の 正誤を 判断していない
★契約を 直して 再投入していない（★C を 勝手に やらない）
```
