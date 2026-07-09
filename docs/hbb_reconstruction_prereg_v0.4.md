# Reconstruction Experiment — Preregistration v0.4.3 (NBC-1) — CLAIM SPLIT

**status: `PREREG_v0.4.3 — claim split adopted (B disjoint-calibration); PENDING round-5 audit + ⟨TC⟩ params + Taka freeze`. 実装・run・freeze/hash はしない。**
Sequence gate: **v0.4.3 → round-5 独立 audit → clean なら ⟨TC⟩ params → freeze/hash(要 Taka)→ 実装 go(要 Taka)**。
Lineage: v0.4→v0.4.2 の audit(rounds 2–4, [[hbb_reconstruction_prereg_v0.4_audit]], DE-0116/0117/0118/0119)で S1–S11 + S2 の routing/selection leak を closed。round-4 が **root cause = target-aware generation authorship(structural)** を検出→ Taka 決定(DE-0120)= **B disjoint-calibration + claim split**。本版はそれを反映。§ 番号は再構成（過去 audit の §-ref は v0.4.0–0.4.2 に対応）。
Discipline: author ≠ attacker ≠ adjudicator. 自律RD 未有効。self-improvement claim なし。`⟨TC⟩`=NEEDS-TAKA-CONFIRM(parameter)。

## 1. CLAIM BOUNDARY（本版の核心・claim split）
**なぜ split か**: hard-core {08,10,30} の breakthrough target は **repo 内 + Claude/GPT context に既知**。完全な target-blind autonomous-reconstruction test には戻せない → **autonomous reconstruction を本実験の load-bearing claim にしない**。
- **PRIMARY = target-disjoint reconstruction transfer on historical hard-core**。DEV∪VAL のみから **機械的に導出・凍結**した機構（§3）が、held-out の hard-core 構造を reconstruct できるか（scorer 認証、target は reconstructor から held-out）。機構設計は hard-core target を一切使わない＝「disjoint に設計した機構が hard-core へ **transfer** するか」を測る。**autonomy は主張しない**（target 既知の事実を honest に反映）。
- **autonomous reconstruction → FUTURE-SEALED track（§12、deferred）**。breakthrough target が **まだ存在しない**、または **mechanism author/scorer が未見**の新規 incident でのみ判定。本実験では走らせない。

## 2. なぜ / 問い（transfer 版）
DE-0115: hard-core {08,10,30} は no arm consensus REC2（reconstruction 未達）。
問い（primary）: **DEV/VAL-disjoint に導出した reconstruction 機構は、held-out の歴史的 hard-core 構造へ transfer して REC2 に届くか。scheduler(R4)は best-of-N/単段を超えるか。構造だけ(R5)で足りるか。**（autonomy は問わない＝§12 へ）

## 3. 機構導出（B disjoint-calibration） — S2 root cause の本実験 fix
操作機構＝**shift operator set membership・R2 generation mechanism・prompt components**。これらを **DEV∪VAL（HBB split の 16 incident: HBB-02,07,09,14,15,16,18,19,20,22,23,25,26,27,28,29；SEALED hard-core と disjoint）のみ**から、**事前登録した mechanical criterion** で導出・凍結する。
- **SEALED {08,10,30} を selection/calibration に一切使わない。Claude の自由裁量 DOF を残さない**（criterion は generic・pre-registered・DEV/VAL 上で機械計算、per-operator hand-tuning 禁止、独立監査可）。
- operator set: 凍結 ref pool（AFE `38111563`/Formal clean 5/ESDE axioms 等）から「**DEV/VAL reconstruction reach ≥ θ**」等の frozen mechanical rule で membership 決定（`⟨TC⟩`=rule/θ、**DEV/VAL のみ**で確定）。
- R2 generation mechanism + prompt: DEV/VAL で fix した frozen template（target 非参照・T0-only・seed 変動）。hard-core を見て変えない。
→ 機構設計が hard-core target を使わない＝**set composition / prompt による {08,10,30} への steer が構造的に不可能**（round-4 root cause = residual 2 を本実験について閉じる）。**残る contamination（target が既知である事実）は §1 の claim downgrade（transfer, not autonomy）で honest に負う。**

## 4. 条件（凍結）
入力クラス: **T0-ONLY**（T0 のみ；autonomy は claim しないので旧「AUTONOMOUS」ラベルは廃止）/ **DETECTOR-FED**（T0 + detector defect locus = HBB H1 相当）。機構は全条件 §3 の DEV/VAL 導出を使用。target は全条件 held-out。
| 条件 | 入力 | 種別 | 役割 |
|---|---|---|---|
| **R0 baseline** | T0 のみ、単段（base A / skepticism B） | T0-ONLY | within-experiment null（floor）。§5 の candidate-pooling/N-parity を同一適用 |
| **R2 Independent Frame Generator** | T0 のみ、全 N 候補 pool（author 選択なし） | T0-ONLY | **primary（transfer）条件** |
| **R4 STOP-SHIFT-RUN-COMPARE** | T0 のみ、全演算子×全 pass pool | T0-ONLY | scheduler |
| **R_bon best-of-N** | T0 のみ、全 N sample pool | T0-ONLY | scheduler の best-of-N confound control |
| **R5 = R4 on lossy T0(L1..L3)** | lossy T0、R4 と同一 scheduler・同 pass・同 token・同 N | T0-ONLY(lossy) | 構造充足の絶対到達（§5.4-eq） |
| **R1 Detection→Reconstructor** | T0 + detector | DETECTOR-FED | 検出供給の効果（transfer 主張には非使用） |
| **R3 Detection+T0 単段** | T0 + detector、単段 | DETECTOR-FED | R4 の scheduler 寄与 control |

## 5. no-author-selection + pure-exhaustive + N-parity（S2 selection/routing + round-4 residual 1）
- **pure exhaustive（B1-(i)）**: 各 pass で全 ref 演算子を **completion まで実行**・truncation なし・出力 pool・**順序 immaterial**。budget は完全 exhaustive pass の完走を保証する大きさ。
- **no-author-selection**: author 側の選択を一切しない。各 condition は候補を **全 emit**（R4=全演算子×全 pass / R2=全 N frame / R_bon=全 N sample / R0/R1/R3/R5 同様）、**cross-pass も pool（best-pass 選択なし）・partial final pass なし**。選択は **target-held-out 独立 scorer** のみ。REC2 到達 = いずれか 1 候補が consensus 認証。
- **N-parity（round-4 residual 1 fix）**: 全 condition を **候補数 N でも一致**（token だけでなく）。R0↔R2↔R_bon↔R4↔R5 の共通 N を凍結（`⟨TC⟩`=N）。→ best-of-N inflation を **N-parity + R0 floor** で統制（多く draw して reach を稼げない）。
- **lossy ladder（R5）**: L0=full/L1=light/L2=heavy/L3=structure-only（`⟨TC⟩`）+ manipulation check。H_structure は **絶対到達**（ある Lk>0 で REC2）で判定。

## 6. 採点（MULTI_SCORER_CONSENSUS × 2 軸 + GPT-drop）
- 2 軸(DET/RECON 0/1/2)を凍結 rubric v2(sha `012941ab…`)で。
- scorer = **GPT-strict + Qwen + 第三 scorer(`⟨TC⟩`；不足時は endpoint を "GPT-certified + Qwen-concurred" と正直改称)**。**REC2 陽性 = ≥2 scorer 一致 AND GPT-drop robust**。GPT-bound caveat を保持。
- **token AND pass AND N を全条件一致**（§5）。budget は exhaustive 完走保証。消費 token/候補数を記録。blind（条件匿名・順 shuffle・mixed batch）。Claude は reconstructor author につき非 scorer。

## 7. 仮説（run 前凍結）+ 解釈マップ
- **H_transfer(primary)**: §3 の **DEV/VAL 導出機構**による **R2** の hard-core consensus REC2 reach-rate が **R0 を binomial(α=0.05, 多重補正)で超過**する incident が ≥1。= **target-disjoint reconstruction transfer**。反証=補正後 0 → transfer 未成立を negative 記録。**autonomy は主張しない**。
- **H_scheduler(secondary)**: 等 budget・等 pass・等 N で **R4 > max(R3, R_bon)**。caveat: 等 token ≠ 等 utility（R4 は budget を飽和）→ margin 併記。
- **H_structure(secondary, 絶対)**: ある Lk>0 で R5 が REC2。全 Lk で 0 → 構造のみ不十分。
- **H_assist(secondary)**: DETECTOR-FED(R1/R3) vs T0-ONLY(R2)。
- 全て consensus + GPT-drop + N-parity + 等 budget を満たして claim。margin・seed 分散・scorer 依存を併記。

## 8. metric / power
- primary: R2 の「R0 超過 incident 数」(binomial α=0.05, 多重補正)。incident 到達 = **≥⌈M/2⌉ seed**（`⟨TC⟩`: M 候補 10）。
- N=3(hard-core) = **targeted probe**（benchmark でない、強い一般化なし）。副次: scheduler/lossy/assisted/token・候補数消費。

## 9. freeze list（run 前に凍結・変更禁止;逸脱は記録）
条件 R0–R5/R_bon 定義 · **§3 DEV/VAL mechanical derivation（operator set rule/θ・R2 generation template、SEALED 不使用・no-Claude-discretion）** · **N-parity 共通 N（round-4 residual 1）** · no-author-selection/candidate-pooling/cross-pass pool/partial-pass 禁止 · pure exhaustive completion + budget sizing · detector spec(R1/R3 同一・R4 不使用) · convergence rule + pass cap · lossy ladder 各 level + manipulation check · scorer 集合 + GPT-drop robust rule · token+pass+N 一致 · M + α + 多重補正 · 仮説 + 解釈マップ + attribution rule(R_success>R0)。
**freeze/hash は round-5 独立 audit 通過 + Taka 承認の後にのみ実施**（本版では未実施）。

## 10. discipline
hard-core は scheduler より先に固定(DE-0115)。**機構は DEV/VAL のみから機械導出・SEALED 不使用（§3）で Claude 裁量 DOF を除去**。author 選択をどの path にも置かない（選択は target-blind scorer のみ）。演算子=凍結 ref・pure exhaustive completion。reconstructor author=Claude(機構のみ)/ scorer=独立(Claude 除外)/ target=held-out。負の結果はそのまま記録。**autonomy を本実験で claim しない**（§1）。self-improvement claim なし。

## 11. 残 `⟨TC⟩`（parameter）
1. §3 mechanical criterion（operator set rule/θ、R2 generation template）— **DEV/VAL のみで確定**。 2. ref pool membership 候補。 3. lossy ladder 各 level。 4. token budget（exhaustive 完走保証）・共通 N。 5. 第三 scorer 供給可否（不足なら "GPT-certified" 改称）。 6. M(候補10)・convergence rule + pass cap。

## 12. FUTURE-SEALED autonomous track（deferred・本実験外）
autonomous reconstruction は **本実験で claim しない**。判定は **breakthrough target がまだ存在しない、または mechanism author/scorer が未見の新規 incident** でのみ可能な **FUTURE-SEALED track** に移す。要件: (a) target が author/scorer に未開示（理想は未生成）、(b) 機構は当該 incident を見ずに凍結、(c) scorer も target-blind。設計・実装は別途 Taka go（自律RD 未有効）。→ 「著者が答えを知る実験は autonomous reconstruction を clean に主張できない」を構造的に受けた分離。

## 13. 非実施（gate）
v0.4.3 は **PENDING round-5 audit**。実装・run・freeze/hash をしない。順序: **v0.4.3 → round-5 独立 audit → clean なら ⟨TC⟩ params → freeze/hash(要 Taka)→ 実装 go(要 Taka)**。raw-API arm・cross-review は本実験 scope 外(post-closure track)。
