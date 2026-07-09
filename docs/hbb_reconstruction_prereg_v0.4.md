# Reconstruction Experiment — Preregistration v0.4.4 (NBC-1) — CAPABILITY-EXHIBIT

**status: `PREREG_v0.4.4 — round-6: VALIDITY-CLEAN. FREEZE-READY pending ⟨TC⟩ params + Taka approval`. 実装・run・freeze/hash はしない。**
**round-6(DE-0123)**: [[hbb_reconstruction_prereg_v0.4_audit]] = **VALIDITY-CLEAN**（独立 auditor + author 検証）。capability-exhibit downgrade が rounds 2→5 の DOF-hopping を **終端**（held-out claim を消したので target-aware knob が非 load-bearing）。R2>R0 は hard-core が no-arm-REC2 定義ゆえ R0≈0 で **R2>0=存在デモ**に collapse。smuggled generalization なし・§12 は真の deferral・§9↔§11/R0-null/N-M すべて discharged。残る gate = **⟨TC⟩ params + Taka freeze/hash 承認のみ**（追加 validity round 不要）。§8 の N-symbol nit は修正済。
Sequence gate: **v0.4.4 → round-6 独立 audit → clean なら ⟨TC⟩ params → freeze/hash(要 Taka)→ 実装 go(要 Taka)**。
Lineage: audit rounds 2–5([[hbb_reconstruction_prereg_v0.4_audit]], DE-0116..0121)。root cause=**target-aware authorship**（Claude が {08,10,30} を知って機構を著す）が routing→selection→generation→criterion と hop。**診断収束**。Taka 決定(DE-0122)= **capability-exhibit へ downgrade、generalization(transfer + autonomy)を FUTURE-SEALED へ**。
Discipline: author ≠ attacker ≠ adjudicator. 自律RD 未有効。self-improvement claim なし。`⟨TC⟩`=NEEDS-TAKA-CONFIRM(parameter)。

## 1. CLAIM BOUNDARY（本版の核心）
audit 5 rounds の収束診断: **答え({08,10,30} の breakthrough_structure）を著した Claude が機構を著す限り、generalization/held-out 系の claim（autonomy も transfer も）は target-aware-authorship knob に load-bearing に汚染される。** よって本実験は generalization を主張しない。
- **PRIMARY = CAPABILITY EXHIBIT（存在デモ、generalization 非主張）**: DEV/VAL 由来で凍結し **author 選択をしない**機構が、**独立 2-scorer の consensus REC2 認証**を通る hard-core {08,10,30} の reconstruction を **産出できるか**。POSITIVE = 「この凍結 artifact は 3 構造の認証付き reconstruction を産出できる」（存在;target-aware 設計込みの下限）。NEGATIVE = 「target-aware に設計しても産出できない」（強い negative）。**いずれも generalization / autonomy を主張しない。**
- **criterion-authorship residual（round-5 R5-A）は本 claim では non-load-bearing**: held-out/generalization を主張しないので、Claude が criterion/pool/template を target 既知で著す事実は claim を汚染しない（存在デモに対して「著者が答えを知っていた」は反証にならない）。
- **generalization は全て FUTURE-SEALED track（§12）へ**: **transfer**（disjoint 導出機構が held-out へ般化）と **autonomous reconstruction** は、target-blind authorship（機構 author/scorer が target 未見）でのみ判定。本実験では走らせない。

## 2. なぜ / 問い（exhibit 版）
DE-0115: hard-core {08,10,30} は no arm consensus REC2。
問い（primary）: **DEV/VAL 由来・no-author-selection の凍結機構は、base 手法(R0)を超えて hard-core 3 構造の consensus REC2 認証付き reconstruction を産出できるか（存在）。scheduler(R4)は best-of-N/単段を超えるか。構造だけ(R5)で足りるか。** generalization は問わない（§12）。

## 3. 機構導出（DEV/VAL 由来・凍結） — ad-hoc tuning 抑制 + FUTURE-SEALED de-risk
操作機構（shift operator set membership・R2 generation mechanism・prompt components）を **DEV∪VAL（16 incident: HBB-02,07,09,14,15,16,18,19,20,22,23,25,26,27,28,29；SEALED hard-core と disjoint）のみ**から、事前登録 mechanical criterion（例「DEV/VAL reconstruction reach ≥ θ」`⟨TC⟩`）で導出・凍結。SEALED {08,10,30} を calibration に不使用、per-operator hand-tuning 禁止。
- **目的（正直な位置づけ）**: これは generalization を clean にする手段では**ない**（round-5: criterion/pool/template 自体を Claude が target 既知で著す＝residual が残る）。目的は (a) 明示的な per-target ad-hoc tuning の抑制、(b) **FUTURE-SEALED harness の de-risk**（同じ機構導出を target-blind に再利用可能に）。
- **正直な residual 明記**: criterion rule/θ・ref-pool composition・R2 template は **Claude 著（target-aware）**。これは capability-exhibit（§1）に対し **non-load-bearing**、generalization に対しては **load-bearing** ゆえ generalization を §12 に隔離。**（旧「no-Claude-discretion」主張は撤回；§9/§11 と整合）**

## 4. 条件（凍結）
入力クラス: **T0-ONLY** / **DETECTOR-FED**（T0 + detector defect locus）。機構は全条件 §3 の DEV/VAL 導出。target は全条件 held-out。
| 条件 | 入力 | 種別 | 役割 |
|---|---|---|---|
| **R0 baseline** | T0 のみ、単段（base A / skepticism B） | T0-ONLY | **null**（base 手法）。candidate-pooling/N-parity 同一適用。exhibit は R2>R0 で「機構が base を超えて産出」 |
| **R2 Independent Frame Generator** | T0 のみ、全 N 候補 pool（author 選択なし） | T0-ONLY | **primary（capability-exhibit）条件** |
| **R4 STOP-SHIFT-RUN-COMPARE** | T0 のみ、全演算子×全 pass pool | T0-ONLY | scheduler |
| **R_bon best-of-N** | T0 のみ、全 N sample pool | T0-ONLY | scheduler の best-of-N confound control |
| **R5 = R4 on lossy T0(L1..L3)** | lossy T0、R4 と同一・同 pass・同 token・同 N | T0-ONLY(lossy) | 構造充足の絶対到達 |
| **R1 Detection→Reconstructor** | T0 + detector | DETECTOR-FED | 検出供給の効果 |
| **R3 Detection+T0 単段** | T0 + detector、単段 | DETECTOR-FED | R4 の scheduler 寄与 control |

## 5. no-author-selection + pure-exhaustive + N-parity
- **pure exhaustive**: 各 pass で全 ref 演算子を completion まで実行・truncation なし・出力 pool・順序 immaterial。budget は完全 exhaustive pass 完走を保証。
- **no-author-selection**: author 選択を一切しない。各 condition は候補を全 emit（cross-pass も pool・partial final pass なし）。選択は target-held-out 独立 scorer のみ。REC2 到達 = いずれか 1 候補が consensus 認証。
- **N-parity**: 全 condition を候補プール数 **N**（`⟨TC⟩`）で一致（token + pass + N 全一致）。best-of-N inflation を N-parity + R0 floor で統制。
- **lossy ladder（R5）**: L0..L3（`⟨TC⟩`）+ manipulation check。H_structure は絶対到達で判定。
- **label 明確化**: **N** = 凍結候補プール数（全 condition 共通）。**M** = seed 数（§8 の ⌈M/2⌉ 用）。両者は別物。

## 6. 採点（MULTI_SCORER_CONSENSUS × 2 軸 + GPT-drop）
2 軸(DET/RECON 0/1/2)を凍結 rubric v2(sha `012941ab…`)で。scorer = GPT-strict + Qwen + 第三 scorer(`⟨TC⟩`;不足時 "GPT-certified + Qwen-concurred" と正直改称)。**REC2 陽性 = ≥2 scorer 一致 AND GPT-drop robust**。GPT-bound caveat 保持。token AND pass AND N を全条件一致。blind(条件匿名・順 shuffle・mixed batch)。Claude は非 scorer。

## 7. 仮説（run 前凍結）+ 解釈マップ
- **H_exhibit(primary, 存在)**: §3 凍結機構による **R2** の hard-core consensus REC2 reach-rate が **R0 を binomial(α=0.05, 多重補正)で超過**する incident が ≥1。= **capability exhibit（機構が base を超えて認証付き reconstruction を産出）**。generalization/autonomy は主張しない。反証=補正後 0 → 「target-aware 設計でも産出せず」を強い negative として記録。**R0 は本 claim の正しい null**（R2>R0 は「機構 > base」を isolate＝exhibit が主張する当のもの;round-5 の R0-wrong-null は transfer を主張しなくなったことで解消）。
- **H_scheduler(secondary)**: 等 budget・等 pass・等 N で **R4 > max(R3, R_bon)**。caveat: 等 token ≠ 等 utility（R4 は budget 飽和）→ margin 併記。
- **H_structure(secondary, 絶対)**: ある Lk>0 で R5 が REC2。全 Lk で 0 → 構造のみ不十分。
- **H_assist(secondary)**: DETECTOR-FED(R1/R3) vs T0-ONLY(R2)。
- 全て consensus + GPT-drop + N-parity + 等 budget を満たして claim。margin・seed 分散・scorer 依存を併記。**generalization は一切主張しない。**

## 8. metric / power
primary: R2 の「R0 超過 incident 数」(binomial α=0.05, 多重補正)。incident 到達 = **≥⌈M/2⌉ seed**（M=seed 数、`⟨TC⟩` 候補 10）。hard-core=**3 incident**（multiplicity 補正の対象数;`N` 記号は §5/§11 の候補プール数専用、こちらは incident 数）=targeted exhibit（benchmark でない、generalization 主張なし）。副次: scheduler/lossy/assisted/token・候補プール(N)消費。

## 9. freeze list（run 前に凍結・変更禁止;逸脱は記録）
条件 R0–R5/R_bon 定義 · §3 DEV/VAL mechanical derivation(operator set rule/θ・R2 template、SEALED 不使用；**criterion は Claude 著＝target-aware と明記、exhibit に対し non-load-bearing**) · N-parity 共通 N · no-author-selection/candidate-pooling/cross-pass pool/partial-pass 禁止 · pure exhaustive completion + budget sizing · detector spec(R1/R3 同一・R4 不使用) · convergence rule + pass cap · lossy ladder 各 level + manipulation check · scorer 集合 + GPT-drop robust rule · token+pass+N 一致 · M(seed) + α + 多重補正 · 仮説(H_exhibit 他) + 解釈マップ + attribution(R2>R0)。
**freeze/hash は round-6 独立 audit 通過 + Taka 承認の後にのみ。**（§9↔§11 の旧矛盾は §3/§9 の「criterion=Claude 著・exhibit に non-load-bearing」明記で解消）

## 10. discipline
hard-core は scheduler より先に固定(DE-0115)。機構は DEV/VAL のみから導出（SEALED 不使用）。**criterion/pool/template は Claude 著（target-aware）＝ capability-exhibit に non-load-bearing、generalization には load-bearing ゆえ §12 に隔離（正直記載）。** author 選択をどの path にも置かない（選択は scorer のみ）。reconstructor author=Claude(機構)/ scorer=独立(Claude 除外)/ target=held-out。負の結果はそのまま記録。**generalization を本実験で主張しない。** self-improvement claim なし。

## 11. 残 `⟨TC⟩`（parameter）
1. §3 mechanical criterion(operator set rule/θ・R2 template)— **DEV/VAL のみで確定；Claude 著で可（exhibit に non-load-bearing）**。 2. ref pool membership 候補。 3. lossy ladder 各 level。 4. token budget(exhaustive 完走保証)・共通 **N**(候補プール数)。 5. 第三 scorer 供給可否。 6. **M**(seed 数, 候補10)・convergence rule + pass cap。

## 12. FUTURE-SEALED track（generalization: transfer + autonomy） — deferred・本実験外
generalization 系 claim を **全て**ここへ隔離。判定は **target-blind authorship**（機構の criterion/pool/template author が当該 incident の breakthrough を未見；理想は target 未生成）+ **target-blind scorer** でのみ可能な新規/未来 incident で。二段:
- **transfer**: DEV/VAL 由来（かつ author が hard-core 相当 target 未見）の機構が held-out incident へ般化するか。
- **autonomous reconstruction**: T0 のみから target 未見で reconstruct するか。
要件: (a) target が author/scorer に未開示（理想は未生成）、(b) 機構は当該 incident を見ずに凍結、(c) scorer も target-blind、(d) 本実験の harness/scoring を de-risk 済で流用。設計・実装は別途 Taka go。自律RD 未有効。→ 「著者が答えを知る実験では generalization を測れない」の構造的帰結。

## 13. 非実施（gate）
v0.4.4 は **PENDING round-6 audit**。実装・run・freeze/hash をしない。順序: **v0.4.4 → round-6 独立 audit → clean なら ⟨TC⟩ params → freeze/hash(要 Taka)→ 実装 go(要 Taka)**。raw-API arm・cross-review は本実験 scope 外(post-closure track)。
