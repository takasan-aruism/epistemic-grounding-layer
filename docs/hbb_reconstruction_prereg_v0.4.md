# Reconstruction Experiment — Preregistration v0.4 (NBC-1)

**status: `PREREG_v0.4.2 — S2 leaks closed (B1-(i) + no-author-selection); PENDING round-4 re-audit + ⟨TC⟩ params + Taka freeze`. 実装・run・freeze/hash はしない。**
**audit(DE-0117, rounds 2–3)**: [[hbb_reconstruction_prereg_v0.4_audit]]。9/11 clean。**S2**: round-2 で Taka が **B1-(i) pure exhaustive** を選択→ R4 演算子の routing DOF を除去(§5.2)。round-3 で **leak#2 が primary R2 の frame 選択に残存**を検出→ **no-author-selection 原則(§2)で全 condition の選択を target-blind scorer へ移し param 非依存に除去**。**B2 修正済**。次: **round-4 独立再監査 → clean なら ⟨TC⟩ params 確定 → Taka 承認で freeze/hash**。
Sequence gate: **v0.4 → 独立 audit → 問題なければ freeze/hash → その後に初めて実装 go(Taka)**。
Supersedes v0.3 (`docs/hbb_reconstruction_prereg_v0.3_draft.md`, BLOCKED). Incorporates the DE-0116 audit fixes
(S1–S11) as design decisions. Refs: DE-0115 (hard-core) · DE-0116 (audit) · `hbb_hard_core_fixed.json` ·
`measurement_instruments_2/3.json`. Discipline: author ≠ attacker ≠ adjudicator. 自律RD 未有効。self-improvement claim なし。
`⟨TC⟩` = NEEDS-TAKA-CONFIRM(**parameter only** — v0.4 は validity hole を設計で解消済、残るは param 確定と少数の Taka 判断)。

## 0. なぜ / 問い
DE-0115: autonomous(H0)reconstruction は未達(engine の AA-unique 再構成は H1 hint-assisted、H0-free AA 再構成は base A の HBB-04 一点)。robust hard-core **{HBB-08, HBB-10, HBB-30}**(no arm consensus REC2)。
問い: **T0 のみ(autonomous)で hard-core を reconstruct できる条件はあるか。scheduler は best-of-N/単段を超えるか。構造だけで足りるか。**

## 1. 監査 fix の対応表（v0.3 → v0.4）
| 監査 | fix in v0.4 | 節 |
|---|---|---|
| **S1** in-harness baseline 欠如 | **R0 baseline** を同 harness・等 budget で追加、within-experiment null に | §3, §7 |
| **S2** selector = target-aware overfit routing | **B1-(i) pure exhaustive を mandate**（Taka 選択, DE-0117）: 全 ref を **completion まで実行**・budget で **完走保証**・出力 pool・**順序 immaterial** ⇒ routing 不可。selector は primary 非使用、STRUCTURAL PROJECTION は secondary study へ降格 | §5.2, §5.3 |
| **S3** consensus≈GPT | REC2 陽性は **GPT drop に robust**(GPT 抜きでも ≥1 独立 scorer が REC2)を要求 + **第三 scorer**;GPT-bound caveat を本文に明記;不足時は "GPT-certified" と正直改称 | §6 |
| **S4** 「H0-autonomous」が H1 再命名 | **autonomy を厳密定義**: T0 のみ入力=AUTONOMOUS、defect locus 供給=ASSISTED。**primary autonomy 主張は R2(+R4 を T0-only で走らせた場合)に限定**、R1/R3 は assisted(別 endpoint) | §2, §4, §7 |
| **S5** bar が p-hackable | success = seed reach-rate が **R0 を binomial 検定(α 固定)で超過**;incident 到達 = **≥⌈M/2⌉ seed**;primary = **単一事前指定条件(R2)**、3 incident に多重比較補正 | §7, §8 |
| **S6** R5 lossy circular | **graded lossy ladder(L0..L3)** + **manipulation check**;H_structure を **絶対到達**(ある Lk>0 で REC2)に再定義、R5≈R4 差分主張を廃す | §2, §5.4, §7 |
| **S7** matched-budget=best-of-N confound | **best-of-N control(R_bon)** 追加;H_scheduler = **R4 > max(R3, R_bon)** 等 budget;R4 vs R2 も報告 | §3, §6, §7 |
| **S8** convergence 未凍結=tunable | convergence rule + pass cap を **freeze list**、outcome 依存調整を禁止 | §5.1, §9 |
| **S9** 等 token budget で R5 が多 pass | R4↔R5 は **pass 数 AND token を一致**、両軸一致時のみ H_structure 解釈 | §6 |
| **S10** detector spec 未凍結 | **detector spec を freeze list**、R1/R3(assisted)で同一（R4 は autonomous=detector なし） | §2, §9 |
| **S11** ref set 未凍結 | anti-overfit は **ref set + selector 凍結が前提**と明記、ref set を run 前凍結 | §5.2, §9 |

## 2. 条件（凍結。autonomy と assisted を分離）
入力規約: **AUTONOMOUS = T0 のみ**（defect locus/hint なし）。**ASSISTED = T0 + detector 出力（defect locus）**（= HBB H1 相当）。
| 条件 | 入力 | 種別 | 役割 |
|---|---|---|---|
| **R0 baseline** | T0 のみ、単段（base A / skepticism B） | AUTONOMOUS | **within-experiment null**（HBB の "no arm" を同 harness・等 budget で再現。R0 が REC2 に届けば前提が harness artifact だったと記録） |
| **R2 Independent Frame Generator** | T0 のみ、代替 frame を独立生成し **全 N 候補を pool（author 選択なし）** | AUTONOMOUS | **primary autonomy 条件** |
| **R4 STOP-SHIFT-RUN-COMPARE** | T0 のみ（自前で shift 生成）、**全演算子 × 全 pass を pool** | AUTONOMOUS | scheduler。autonomy set に含む |
| **R_bon best-of-N** | T0 のみ、N 独立 sample を **全 pool（author 選択なし）**、STOP/SHIFT/COMPARE なし | AUTONOMOUS | scheduler の best-of-N confound を切る control |
| **R1 Detection→Reconstructor** | T0 + detector defect locus | ASSISTED | 「検出を与えれば再構成できるか」（autonomy 主張には使わない） |
| **R3 Detection+T0 単段** | T0 + detector、単段 | ASSISTED | R4 の scheduler 寄与 control（assisted 側） |
| **R5 = R4 on lossy T0(L1..L3)** | lossy T0 のみ、R4 と同一 scheduler・**同 pass 数 + 同 token** | AUTONOMOUS(lossy) | 構造充足の絶対到達テスト（§5.4） |
target は全条件 held-out（reconstructor 非開示）。

**★ no-author-selection 原則（B1-(i) を全 selection に拡張, DE-0117 round-3）**: どの condition も **author 側の選択を一切しない**。各 condition は生成した候補を **全 emit**（R4=全演算子×全 pass を pool / R2=全 N frame / R_bon=全 N sample / R0/R1/R3/R5 同様）、**cross-pass も pool（best-pass の author 選択なし）**。generation prompt は **凍結・target-blind・T0-only・seed 変動のみ**。**target-held-out の独立 scorer が全候補を採点**し、**condition が incident で REC2 到達 = その候補のいずれか 1 つが consensus 認証**。→ 選択は全て target-blind scorer 側へ移り、**leak #2（target を知る author が選択基準を選ぶ）を primary(R2)含め全 path で param 非依存に除去**。any-of-N の inflation は全 condition 同一処理 + R0 floor（H_recon=R2>R0）で統制。budget は全 pass 完走を保証（**partial final pass なし**）。

## 3. baseline / control（S1, S7）
- **R0** = HBB 最強手（A base + B skepticism）を **この harness・T0 のみ・等 budget** で {08,10,30} に。preregister: R0 の consensus REC2 reach-rate が within-experiment の **floor**。
- **R_bon** = 等 budget の plain best-of-N（構造なし sampling）。
- **attribution rule(preregister)**: 再構成条件 X の主張は **X の REC2 reach-rate > R0**（binomial, α=§7）でのみ成立。R0 が既に REC2 に届く場合 → 「HBB の no-arm は harness 依存だった」を **negative としてそのまま記録**（実験の第一の落とし穴を先に潰す）。

## 4. autonomy の定義（S4）
- **AUTONOMOUS**: 入力 = T0 のみ。hint/defect locus を与えない。
- **ASSISTED**: T0 + detector 出力（defect locus）= HBB H1「隠れた前提」ヒント相当。
- **primary autonomy endpoint = R2**（必要なら R4/R_bon/R5 も autonomy set）。**R1/R3 の REC2 は assisted と明示分類**し、autonomy 主張に流用しない。

## 5. scheduler(v0.3 features、監査後)
### 5.1 manifest multipass（S8）
pass 列 STOP→SHIFT→RUN→COMPARE。**convergence rule・pass cap は freeze list(§9)で run 前凍結、outcome 依存調整禁止**。`⟨TC⟩`: 具体 rule（候補: pass cap = budget 到達 or K 連続 COMPARE 改善なし）。
### 5.2 extensible-with-refs（S2, S11） — **B1-(i) pure exhaustive を mandate**
shift 演算子は **凍結 ref set**（AFE `38111563` / Formal clean 5 / ESDE axioms 等、`⟨TC⟩`=集合確定）。
**pure exhaustive**: 各 pass で **全 ref 演算子を completion まで実行**（誰も除外しない・**truncation しない**）、出力を **pool** するので **順序は結果に immaterial**。matched budget（§6）は **少なくとも 1 回の完全 exhaustive pass の完走を保証する大きさ**に sizing。incident-tuned 演算子を書かない。
→ **routing による除外・昇格が構造的に不可能**＝S2 の overfit DOF を **param 非依存**で除去（Taka B1-(i) 選択, DE-0117）。
### 5.3 STRUCTURAL PROJECTION domain selector（S2 → secondary study に降格）
**primary autonomy path（R2/R4）では selector を使わない**（§5.2 pure exhaustive・順序 immaterial）。**R2 の frame 選択も §2 の no-author-selection 原則で除去済**（author 選択はどの path にも無い；選択は target-blind scorer のみ）。STRUCTURAL PROJECTION（順序/優先付けが再構成に効くか）は **overfit-critical path 外の別 secondary study**（例: R4-selector vs R4-exhaustive）としてのみ実行し、**primary autonomy claim には非寄与**と明示。secondary study の selector も target 非参照で凍結（`⟨TC⟩`）だが、**primary の validity はこれに一切依存しない**。→ 「exhaustive within budget」の truncation→selection leak は消滅（budget は完走保証、演算子は落ちない）。
### 5.4 lossy ladder（S6, S9）
**L0=full / L1=light mask / L2=heavy mask / L3=structure-only**（MASK_PIPELINE v2 系、`⟨TC⟩`=各 level 定義）。**manipulation check**: 各 Lk で selector の structural 特徴が生存するか事前確認。R5 は R4 と **pass 数 AND token を一致**。H_structure は **絶対到達**（ある Lk>0 で consensus REC2）で判定、R5≈R4 差分は使わない。

## 6. 採点（S3）: MULTI_SCORER_CONSENSUS × 2 軸 + GPT-drop robust
- 2 軸(DET/RECON 0/1/2)を凍結 rubric v2(sha `012941ab…`)で。
- scorer = **GPT-strict + Qwen + 第三 scorer(`⟨TC⟩`: 供給可能な独立系;不足時は endpoint を "GPT-certified + Qwen-concurred" と正直改称)**。
- **REC2 陽性 = ≥2 scorer 一致 AND GPT-drop robust（GPT を除いても ≥1 独立 scorer が REC2）**。GPT-bound caveat を本文に保持。
- **token-budget matched(S7,S9)**: 全条件同一 total token。**matched budget は §5.2 の exhaustive 完走を保証する大きさに sizing**（各 pass は全 ref 演算子を完走、**truncation で演算子を落とさない**＝S2 の budget-door leak を塞ぐ）。multipass の pass 数は convergence/cap で bound;R4↔R5 は pass 数も一致。全条件の消費 token を記録。
- blind: 条件匿名・順 shuffle・mixed batch。Claude は reconstructor author につき非 scorer。

## 7. 仮説（run 前凍結）+ 解釈マップ
- **H_recon(primary, autonomy)**: **R2** の consensus REC2 reach-rate が **R0 を binomial(α=0.05)で超過**する hard-core incident が、多重比較補正後 ≥1。反証 = 補正後 0 → 「autonomous reconstruction は未達」を negative 記録。
- **H_scheduler(secondary)**: 等 budget・等 pass で **R4 > max(R3, R_bon)**。R4≈R_bon → scheduler は best-of-N を超えない。caveat: **等 token ≠ 等 utility**（R4 は budget を全演算子で飽和させるが R3/R_bon は saturate しうる）→ margin をこの非対称込みで読む。
- **H_structure(secondary, 絶対)**: ある lossy level Lk>0 で R5 が consensus REC2 到達（構造で足りる）。R5 が全 Lk で 0 → 構造のみでは不十分。
- **H_assist(secondary)**: assisted(R1/R3)が autonomous(R2)を超える（検出供給が効くか）。**autonomy 主張には使わない**。
- 全て MULTI_SCORER_CONSENSUS + GPT-drop robust + 等 budget を満たして初めて claim。margin・seed 分散・scorer 依存を必ず併記。

## 8. metric / power（S5）
- **primary**: R2 の「R0 超過 incident 数」(binomial α=0.05, 多重補正)。
- incident 到達 = **≥⌈M/2⌉ seed**（seed-robust、単発ラッキー seed を排除）。`⟨TC⟩`: **M**(候補 10)。
- N=3 = **targeted probe**（benchmark でない、強い一般化をしない）。副次: assisted、scheduler、lossy ladder、token 消費、generalization set(HBB-01/05, 別集計 `⟨TC⟩`)。

## 9. freeze list（run 前に凍結・変更禁止;逸脱は記録）
条件 R0/R1/R2/R3/R4/R5/R_bon 定義 · **detector spec(S10, R1/R3 で同一・R4 は不使用)** · ref set(S2,S11) · **pure exhaustive completion 保証 + budget sizing(S2, B1-i)**（primary は selector 不使用） · **no-author-selection / candidate-pooling（全 emit・cross-pass pool・partial pass なし）+ generation prompt 凍結(target-blind, T0-only, seed 変動)（S2 round-3, leak#2）** · STRUCTURAL PROJECTION secondary study の selector は別枠凍結 · convergence rule + pass cap(S8) · lossy ladder 各 level + manipulation check(S6) · scorer 集合 + GPT-drop robust rule(S3) · token budget + pass 一致(S7,S9) · M + α + 多重補正(S5) · 仮説 + 解釈マップ + attribution rule(S1)。
**freeze/hash は独立 audit 通過後 + Taka 承認後にのみ実施**（本 v0.4 では未実施）。

## 10. discipline
hard-core は scheduler より先に固定(DE-0115)= overfit 防止。reconstructor author=Claude(機構のみ)/ scorer=独立(Claude 除外)/ target=held-out / 演算子=凍結 ref・**pure exhaustive completion（順序 immaterial ⇒ routing 不可, B1-i）**。**author 選択をどの path にも置かない（§2 no-author-selection；選択は target-blind scorer のみ）**。負の結果はそのまま記録。self-improvement claim なし。

## 11. 残 `⟨TC⟩`（parameter 確定 / 少数の Taka 判断。validity hole ではない）
1. convergence rule + pass cap の具体値。 2. ref set membership。 3. （**primary は pure exhaustive で selector 不使用 → validity 非依存**）STRUCTURAL PROJECTION secondary study を走らせる場合のみ selector rule + target 非参照凍結。 4. lossy ladder 各 level 定義。 5. token budget 数値（exhaustive 完走を保証する大きさ）・matched 単位。 6. 第三 scorer の供給可否（不足なら "GPT-certified" 改称で運用可）。 7. M(候補10)・generalization set 採否。

## 12. 非実施（gate）
v0.4.2 は **PENDING round-4 re-audit**（S2 leak#1=B1-(i)・leak#2=no-author-selection で closed、B2 修正済）。実装・run・freeze/hash をしない。順序: **v0.4.2 → round-4 独立 audit → clean なら ⟨TC⟩ params 確定 → freeze/hash(要 Taka)→ 実装 go(要 Taka)**。raw-API arm・cross-review は本実験 scope 外(post-closure track)。
