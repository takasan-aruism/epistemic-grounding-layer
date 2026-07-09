# Reconstruction Experiment — Preregistration v0.4.4 (NBC-1) — CAPABILITY-EXHIBIT

**status: `PREREG_v0.4.4 — FROZEN (params embedded, DE-0124). hash in hbb_reconstruction_prereg_seal.json. AWAITING TAKA GO for implement/run`. run/実装はしない。**
**round-6(DE-0123)= VALIDITY-CLEAN**（独立 auditor + author 検証）。**params 承認・埋込済(DE-0124)**: include-all(11 operators) / L1–L3 / pass-cap=4 / M=10 / **N=44** / 第三 scorer なし="GPT-certified + Qwen-concurred" / **budget=exhaustive completion 絶対条件**。capability-exhibit が rounds 2→5 の DOF-hopping を終端(held-out claim なし→target-aware knob 非 load-bearing)。R2>R0 は hard-core=no-arm-REC2 定義ゆえ R0≈0 で **R2>0=存在デモ**。generalization は §12 FUTURE-SEALED へ隔離。**freeze/hash artifact 作成済、実装/run は Taka go 待ち。**
Sequence: **v0.4.4 → round-6 audit(VALIDITY-CLEAN) → params 確定(DE-0124) → freeze/hash(完了) → 実装 go(要 Taka)**。現在地 = **Taka go 待ち**。
Lineage: audit rounds 2–5([[hbb_reconstruction_prereg_v0.4_audit]], DE-0116..0121)。root cause=**target-aware authorship**（Claude が {08,10,30} を知って機構を著す）が routing→selection→generation→criterion と hop。**診断収束**。Taka 決定(DE-0122)= **capability-exhibit へ downgrade、generalization(transfer + autonomy)を FUTURE-SEALED へ**。
Discipline: author ≠ attacker ≠ adjudicator. 自律RD 未有効。self-improvement claim なし。（parameter は全て確定・DE-0124;残 `⟨TC⟩` なし。）

## 1. CLAIM BOUNDARY（本版の核心）
audit 5 rounds の収束診断: **答え({08,10,30} の breakthrough_structure）を著した Claude が機構を著す限り、generalization/held-out 系の claim（autonomy も transfer も）は target-aware-authorship knob に load-bearing に汚染される。** よって本実験は generalization を主張しない。
- **PRIMARY = CAPABILITY EXHIBIT（存在デモ、generalization 非主張）**: DEV/VAL 由来で凍結し **author 選択をしない**機構が、**独立 2-scorer の consensus REC2 認証**を通る hard-core {08,10,30} の reconstruction を **産出できるか**。POSITIVE = 「この凍結 artifact は 3 構造の認証付き reconstruction を産出できる」（存在;target-aware 設計込みの下限）。NEGATIVE = 「target-aware に設計しても産出できない」（強い negative）。**いずれも generalization / autonomy を主張しない。**
- **criterion-authorship residual（round-5 R5-A）は本 claim では non-load-bearing**: held-out/generalization を主張しないので、Claude が criterion/pool/template を target 既知で著す事実は claim を汚染しない（存在デモに対して「著者が答えを知っていた」は反証にならない）。
- **generalization は全て FUTURE-SEALED track（§12）へ**: **transfer**（disjoint 導出機構が held-out へ般化）と **autonomous reconstruction** は、target-blind authorship（機構 author/scorer が target 未見）でのみ判定。本実験では走らせない。

## 2. なぜ / 問い（exhibit 版）
DE-0115: hard-core {08,10,30} は no arm consensus REC2。
問い（primary）: **DEV/VAL 由来・no-author-selection の凍結機構は、base 手法(R0)を超えて hard-core 3 構造の consensus REC2 認証付き reconstruction を産出できるか（存在）。scheduler(R4)は best-of-N/単段を超えるか。構造だけ(R5)で足りるか。** generalization は問わない（§12）。

## 3. 機構（凍結・include-all / 確定 DE-0124）
**operator set = include-all（zero-discretion）**: 凍結 ref pool の **全 11 演算子**を使う＝**AFE 6 演算子（sha `38111563`）+ Formal clean 5 probe（`formal_esde_operators.json` の sealable_axiom_grounded 5）**。**DEV/VAL θ-gating も per-operator 選択もしない**（Taka 承認: include-all＝criterion 側の裁量を完全に無くす）。ESDE の SOURCE_GAP probe は除外。SEALED {08,10,30} を一切使わない。
- **R2 generation template**: **凍結・target-blind・T0-only の単一 generic reframe prompt**（「現 stuck frame のみから subject/level/key-distinction を変える代替 frame と次手を出せ;既知結論を参照するな」）。exact string は実装時に本 spec 下で bind し frozen artifact に含める。
- **正直な residual 明記（exhibit に non-load-bearing）**: ref-pool composition・R2 template は **Claude 著（target-aware）**。capability-exhibit（§1）には **non-load-bearing**、generalization には **load-bearing** ゆえ generalization を §12 に隔離。include-all で operator-selection 裁量は消滅、残る著者面は pool 母集団と template のみ（いずれも exhibit に非 load-bearing）。**（旧「DEV/VAL 由来 criterion / no-Claude-discretion」は include-all 採用で置換）**

## 4. 条件（凍結）
入力クラス: **T0-ONLY** / **DETECTOR-FED**（T0 + detector defect locus）。機構は全条件 §3 の include-all 凍結演算子（11）。target は全条件 held-out。
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
- **pure exhaustive**: 各 pass で全 11 演算子を completion まで実行・truncation なし・出力 pool・順序 immaterial。**pass-cap = 4（固定・決定的、convergence ベース early-stop なし）**。budget は完全 exhaustive pass 完走を保証（下記 budget）。
- **no-author-selection**: author 選択を一切しない。各 condition は候補を全 emit（cross-pass も pool・partial final pass なし）。選択は target-held-out 独立 scorer のみ。REC2 到達 = いずれか 1 候補が consensus 認証。
- **N-parity（確定 DE-0124）**: **共通 N = 11 演算子 × pass-cap 4 = 44**（派生値）。**全 condition（R0/R1/R2/R3/R4/R5/R_bon）が incident・seed ごとに 44 候補を emit・全 pool・全採点**（token + pass + N 全一致）。best-of-N inflation を N-parity + R0 floor で統制。絶対 reach-rate は「at N=44」と明記し over-read しない。
- **budget（絶対条件）**: matched total token は **44 生成の exhaustive 完走を保証する大きさを絶対下限**とする（truncation で演算子/候補を落とさない＝S2 leak#1 を再 open しない）。全 condition 同一 total、消費 token/候補数を記録。
- **lossy ladder（R5、確定 DE-0124；MASK_PIPELINE v2 sha `2bfd70f9`）**: L0=full / **L1**=domain 固有名詞＋数値を mask / **L2**=L1＋domain 動詞・専門語を mask（claim/frame 構造語は保持）/ **L3**=structure-only（claim-axis・前提・decision skeleton のみ、内容語は generic placeholder）。各 Lk で **manipulation check**。H_structure は絶対到達で判定。
- **label**: **N**=候補プール数（=44、全 condition 共通）。**M**=seed 数（§8）。別物。

## 6. 採点（MULTI_SCORER_CONSENSUS × 2 軸 + GPT-drop）
2 軸(DET/RECON 0/1/2)を凍結 rubric v2(sha `012941ab…`)で。**scorer = GPT-strict + Qwen の 2 系（第三 scorer は追加しない・確定 DE-0124）**。endpoint を **"GPT-certified + Qwen-concurred"** と正直表記。**REC2 陽性 = GPT ∧ Qwen 一致 AND GPT-drop robust（GPT を除いても Qwen 単独が REC2）**。**GPT-bound caveat 明記**（consensus ≒ GPT-gated、certification は GPT idiosyncrasy に bound;exhibit は非 load-bearing）。token AND pass AND N(=44) を全条件一致。blind(条件匿名・順 shuffle・mixed batch)。Claude は非 scorer(author)。

## 7. 仮説（run 前凍結）+ 解釈マップ
- **H_exhibit(primary, 存在)**: §3 凍結機構による **R2** の hard-core consensus REC2 reach-rate が **R0 を binomial(α=0.05, 多重補正)で超過**する incident が ≥1。= **capability exhibit（機構が base を超えて認証付き reconstruction を産出）**。generalization/autonomy は主張しない。反証=補正後 0 → 「target-aware 設計でも産出せず」を強い negative として記録。**R0 は本 claim の正しい null**（R2>R0 は「機構 > base」を isolate＝exhibit が主張する当のもの;round-5 の R0-wrong-null は transfer を主張しなくなったことで解消）。
- **H_scheduler(secondary)**: 等 budget・等 pass・等 N で **R4 > max(R3, R_bon)**。caveat: 等 token ≠ 等 utility（R4 は budget 飽和）→ margin 併記。
- **H_structure(secondary, 絶対)**: ある Lk>0 で R5 が REC2。全 Lk で 0 → 構造のみ不十分。
- **H_assist(secondary)**: DETECTOR-FED(R1/R3) vs T0-ONLY(R2)。
- 全て consensus + GPT-drop + N-parity + 等 budget を満たして claim。margin・seed 分散・scorer 依存を併記。**generalization は一切主張しない。**

## 8. metric / power
primary: R2 の「R0 超過 incident 数」(binomial α=0.05, 多重補正)。**M = 10 seed（確定 DE-0124）**、incident 到達 = **≥⌈M/2⌉ = 5 seed**（single-lucky-seed を排除）。hard-core=**3 incident**（multiplicity 補正の対象数;`N`(=44) は候補プール数専用、こちらは incident 数）=targeted exhibit（benchmark でない、generalization 主張なし）。副次: scheduler/lossy/assisted/token・候補プール(N=44)消費。

## 9. freeze list（run 前に凍結・変更禁止;逸脱は記録）
条件 R0–R5/R_bon 定義 · §3 **include-all 11 演算子（AFE 6 sha 38111563 + Formal clean 5）+ R2 target-blind template**（SEALED 不使用；pool/template は Claude 著=exhibit に non-load-bearing） · **N-parity 共通 N=44** · no-author-selection/candidate-pooling/cross-pass pool/partial-pass 禁止 · pure exhaustive completion + **budget=exhaustive 完走保証（絶対条件）** · detector spec(R1/R3 同一・R4 不使用) · **pass-cap=4 固定・convergence early-stop なし** · **lossy L1–L3(MASK v2 sha 2bfd70f9)** + manipulation check · **scorer=GPT+Qwen("GPT-certified + Qwen-concurred")+ GPT-drop robust** · token+pass+N(44) 一致 · **M=10 seed** + α=0.05 + 多重補正 · 仮説(H_exhibit 他) + 解釈マップ + attribution(R2>R0)。
**FROZEN(DE-0124)**: 上記 params 埋込・凍結済。**hash = `hbb_reconstruction_prereg_seal.json`**。実装/run は **Taka go 待ち**（本 doc の freeze/hash は完了、run はしない）。

## 10. discipline
hard-core は scheduler より先に固定(DE-0115)。機構は DEV/VAL のみから導出（SEALED 不使用）。**criterion/pool/template は Claude 著（target-aware）＝ capability-exhibit に non-load-bearing、generalization には load-bearing ゆえ §12 に隔離（正直記載）。** author 選択をどの path にも置かない（選択は scorer のみ）。reconstructor author=Claude(機構)/ scorer=独立(Claude 除外)/ target=held-out。負の結果はそのまま記録。**generalization を本実験で主張しない。** self-improvement claim なし。

## 11. CONFIRMED PARAMETERS（確定・DE-0124）
1. **operator set = include-all（11: AFE 6 sha `38111563` + Formal clean 5）**、DEV/VAL θ-gating なし。R2 = 凍結 target-blind reframe template。 2. ref pool = 上記 11（ESDE SOURCE_GAP 除外）。 3. **lossy L1–L3**（L1 nouns+numbers / L2 +domain verbs・terms / L3 structure-only；MASK v2 sha `2bfd70f9`）。 4. **共通 N = 44（=11×4）**、**token budget = exhaustive 完走保証（絶対条件・下限固定）**。 5. **第三 scorer なし → "GPT-certified + Qwen-concurred"**（GPT-drop robust 併記）。 6. **M = 10 seed**、**pass-cap = 4 固定・convergence early-stop なし**、α=0.05、多重補正(3 incident)。

## 12. FUTURE-SEALED track（generalization: transfer + autonomy） — deferred・本実験外
generalization 系 claim を **全て**ここへ隔離。判定は **target-blind authorship**（機構の criterion/pool/template author が当該 incident の breakthrough を未見；理想は target 未生成）+ **target-blind scorer** でのみ可能な新規/未来 incident で。二段:
- **transfer**: DEV/VAL 由来（かつ author が hard-core 相当 target 未見）の機構が held-out incident へ般化するか。
- **autonomous reconstruction**: T0 のみから target 未見で reconstruct するか。
要件: (a) target が author/scorer に未開示（理想は未生成）、(b) 機構は当該 incident を見ずに凍結、(c) scorer も target-blind、(d) 本実験の harness/scoring を de-risk 済で流用。設計・実装は別途 Taka go。自律RD 未有効。→ 「著者が答えを知る実験では generalization を測れない」の構造的帰結。

## 13. gate（現在地）
v0.4.4 は **VALIDITY-CLEAN(round-6) + params 確定(DE-0124) + FROZEN/HASHED**（`hbb_reconstruction_prereg_seal.json`）。**次は Taka go でのみ実装 → run**。本 doc 側の freeze/hash は完了、**run/実装はまだしない**。raw-API arm・cross-review は本実験 scope 外(post-closure track)。
