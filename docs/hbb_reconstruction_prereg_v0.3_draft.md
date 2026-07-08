# Reconstruction Experiment — Preregistration DRAFT (NBC-1 v0.3)

**status: `PREREG_DRAFT — AWAITING_TAKA`. 実装・run はしない。Taka go 待ち。**
Refs: DE-0115 (HBB CLOSED) · `hbb_hard_core_fixed.json` · `hbb_final_report.md` · NBC-1 ([[next_branch_candidates]]) ·
`measurement_instruments_3.json` (DETECTION_RECONSTRUCTION_SPLIT) · `measurement_instruments_2.json` (MULTI_SCORER_CONSENSUS).
Discipline: author ≠ attacker ≠ adjudicator. 自律RD 未有効。self-improvement claim なし。
**`⟨TC⟩` = NEEDS-TAKA-CONFIRM**(名称のみ受領した v0.3 仕様を私が具体化した箇所。run 前に Taka 確定が必要)。

## 0. なぜ（question）
HBB N=13 closure(DE-0115)の robust 所見: **autonomous(H0)reconstruction は未達**。engine の AA-unique 再構成は
全て H1 hint-assisted、H0-free の AA 再構成は base arm A の HBB-04 一点のみ。robust hard-core
**{HBB-08, HBB-10, HBB-30}** は no arm が consensus REC2 に到達しない(全て detected-not-reconstructed)。
→ 問い: **reconstruction を独立段階として与えると、hard-core を H0-autonomous に再構成できるか。scheduler(R4)は
単段(R3)を超えるか。再構成は T0 の内容駆動か、構造投影駆動か(R5)。**

## 1. 対象（固定・凍結）
- **primary target = fixed hard-core {HBB-08, HBB-10, HBB-30}**(`hbb_hard_core_fixed.json`、DE-0115 で closure 前に固定=scheduler へ overfit しない)。
- **held-out target(採点参照のみ、reconstructor には非開示)** = 各 incident の `breakthrough_structure`(Taka-adjudicated / 一部 GPT-formalized)。
- **secondary generalization set `⟨TC⟩`(任意)**: HBB-01 / HBB-05(engine が H1 でのみ再構成した AA)。「H1 でできたことを H0 でできるか」の般化確認。primary とは別集計。

## 2. 条件 R1–R5（凍結。R5 は必須・削除しない）
全条件は同一 T0(§1)を入力、同一 held-out target で採点、**同一 token budget**(§6)。reconstructor は target 非開示。

| 条件 | 定義 | 分離する変数 |
|---|---|---|
| **R1 Detection→Reconstructor** | 2 段: 検出段(consensus detector = skepticism ベース)が frame-defect を出力 → 専用 Reconstructor が (T0 + defect) から構造同値な代替 frame を構築 | 「検出の下流に再構成段を足す」効果 |
| **R2 Independent Frame Generator** | 検出に条件づけず、T0 のみから代替 frame を独立に複数生成→選択(diverge-then-select) | 独立生成 vs 検出条件づけ |
| **R3 Detection + T0（単段 control）** | 検出出力 + full T0 を **単段(scheduler 機構なし)**で reconstructor に与える | R4 の scheduler 寄与を切り出す基準線 |
| **R4 STOP-SHIFT-RUN-COMPARE scheduler (v0.3)** | NBC-1 scheduler: manifest multipass(§4.1)、structural-projection domain selector(§4.3)で shift 演算子(refs, §4.2)を選択、各 shifted frame を RUN、COMPARE で収束。full T0 | 収束型 multipass scheduler の寄与 |
| **R5 structure-only / lossy T0 + same scheduler** | **R4 と同一 scheduler**、ただし T0 を **structure-only / lossy 版**(§4.4)に置換 | 再構成が T0 内容駆動か構造投影駆動か |

R3 は R1/R4 の control(単段)。R5 は R4 の ablation(入力を構造のみに)。**R4 と R5 は scheduler を共有し、差は T0 の情報量のみ。**

## 3. v0.3 アーキテクチャの prereg 反映
### 4.1 manifest multipass
scheduler は **宣言的 manifest**(pass の列)を実行。各 pass = 1 回の STOP(現 frame 停止)→ SHIFT(§4.3 で選ばれた軸/主体/層の変更)→ RUN(shifted frame で候補生成)→ COMPARE(代替と比較・収束判定)。
- manifest schema・pass 上限・収束基準(COMPARE がいつ停止するか)は **`⟨TC⟩`**。draft 候補: pass 上限 = budget 到達 or `⟨TC⟩` 回連続で COMPARE 改善なし。
- manifest は run 前に凍結(pass 計画・上限を preregister)。

### 4.2 extensible-with-refs
shift 演算子は **ref で参照**(inline しない): AFE operators(sha `38111563`)/ Formal ESDE clean probes(`formal_esde_operators.json` の sealable 5)/ ESDE axioms 等を **凍結 ref set** として宣言。incident-tuned な演算子を新規に書かない(overfit 防止)。**採用 ref set は run 前に凍結**。`⟨TC⟩` = ref set の確定。

### 4.3 STRUCTURAL PROJECTION domain selector
T0 を構造ドメインへ **projection** し、その pass で適用する shift 演算子(ref)を選択する **決定的** selector。
- 目的: SHIFT を全演算子総当たりでなく、構造投影で絞る(Formal の Ω domain-selector に対応する機能位置。ただし v3.0 Formal Ω は SOURCE_GAP のため EGL-discipline 由来として実装)。
- selector 規則は **`⟨TC⟩`**(Taka の v0.3 spec 必須)。draft 候補: T0 から {claim 型・単位個別化・因果/相関・層(local/program)・観測/対象} の構造特徴を抽出→対応演算子 ref を選択。決定的・凍結。

### 4.4 structure-only / lossy T0（R5 用）
full T0 から表層内容を落とし **構造骨格のみ**を残す変換。
- 変換定義は **`⟨TC⟩`**。draft 候補: 固有名詞・数値・ドメイン語を generic token へ mask(MASK_PIPELINE v2 系)し、claim/frame の構造関係(主張軸・前提・決定要求)のみ保持。lossy = 情報量を意図的に削減。
- R5 = この lossy T0 を R4 と同一 scheduler に与える。**R5≈R4 なら構造投影が active ingredient、R5≪R4 なら T0 内容が load-bearing。**

## 5. 採点（MULTI_SCORER_CONSENSUS × DETECTION/RECONSTRUCTION）
- **2 軸**(DET 0/1/2, RECON 0/1/2)を **凍結 rubric v2**(sha `012941ab…`)で採点。
- **2 系独立 scorer = GPT rubric-v2 + Qwen rubric-v2**。**consensus = 両者一致**のみ claim。
- **Claude は reconstructor R1–R5 の author につき非 scorer**(author ≠ adjudicator)。target も held-out。
- reconstruct 判定 = consensus RECONSTRUCTION==2(構造同値な代替 frame を構築)。detection も併記。
- blind: arm/condition 匿名・順 shuffle・mixed batch(SEALED 手続き踏襲)。

## 6. token-budget matched test（公平性 control）
- 全条件(R1–R5)を **同一 total token budget** で比較。budget 数値は **`⟨TC⟩`**。
- 特に **R4/R5 の multipass が budget を超過して「多く使ったから勝つ」ことを禁止**: multipass は budget 内に収める(pass 数は budget で頭打ち)。単段(R3)と scheduler(R4)を **等 budget** で対比。
- 各 condition の消費 token を記録。budget 超過 run は無効。

## 7. 仮説（run 前に凍結）と解釈マップ
- **H_recon(primary)**: hard-core {08,10,30} で、いずれかの再構成条件(R1/R2/R4)が **H0-autonomous consensus REC2** を ≥1 incident で達成する（= HBB で no arm が届かなかった再構成を閉じる）。
  - 反証: 全条件・全 hard-core で H0 consensus REC2 = 0 → 「reconstruction stage は autonomous hard-core 再構成を解かない」を **negative としてそのまま記録**。
- **H_scheduler(secondary)**: 等 budget で **R4 > R3**(consensus REC で scheduler が単段を上回る)。
  - R4≈R3 → scheduler 機構は単段検出+T0 に上乗せしない。
- **H_structure(secondary)**: **R5 vs R4**。R5≈R4 → 構造投影が active ingredient(構造のみで再構成)。R5≪R4 → T0 内容が load-bearing。
- **H_gen(探索)**: R2(独立生成)vs R1(検出条件づけ)— 再構成は独立生成の方が良いか。
- いずれも「勝ち」を主張する前に MULTI_SCORER_CONSENSUS × 等 budget を満たすこと。margin・hint 依存・scorer 依存を明記。

## 8. primary endpoint と副次
- **primary**: hard-core 上の **H0-autonomous consensus REC2 到達 incident 数**(condition 別)。
- 副次: hint ladder 全体(H0–H3)での consensus REC2 reach(best-across-rungs);consensus DET2;R4 vs R3(等 budget);R5 vs R4;token 消費;secondary generalization set(§1)。

## 9. power / 反復（低 N の正直な扱い）
- hard-core = **3 incident のみ** → 統計的検出力は低い。これは benchmark でなく **targeted probe**。
- 反復: 各 (incident × condition) を **M 独立 seed `⟨TC⟩`**(draft 候補 M=5)で実行、consensus REC2 到達率を集計。seed 間で決定的でない生成は seed で変える(scheduler 内乱数は seed 由来)。
- 3 incident で「解けた/解けない」を強く一般化しない。generalization set は別集計の補助。

## 10. discipline（凍結・記録）
- run 前に **凍結**: 条件 R1–R5、ref set(§4.2)、selector 規則(§4.3)、lossy 変換(§4.4)、rubric(既凍結)、budget、seeds、仮説、解釈マップ。凍結後の変更禁止(逸脱は記録)。
- **hard-core は既に scheduler より先に固定**(DE-0115)= overfit 防止(DE-0111 同型事故の回避)。
- reconstructor author = Claude(機構のみ)/ scorer = GPT+Qwen(Claude 除外)/ target = held-out。演算子は既凍結 ref のみ、incident-tuned 新規演算子を書かない。
- 負の結果はそのまま記録。self-improvement claim を作らない。

## 11. Taka 確定待ち項目（`⟨TC⟩` 一覧）
1. v0.3 scheduler の manifest schema・pass 上限・**収束基準**(COMPARE 停止条件)。
2. **STRUCTURAL PROJECTION domain selector の規則**(構造特徴→演算子 ref の写像)。
3. **structure-only / lossy T0 変換**の定義(どこまで削るか)。
4. **extensible-with-refs の ref set 確定**(AFE 38111563 / Formal 5 probe / ESDE axioms / その他)。
5. **token budget 数値** と matched の単位(total tokens/incident?)。
6. seed 数 M と generalization set を含めるか。
7. STOP/SHIFT のトリガ定義(いつ現 frame を止め、何を shift するか)。

## 12. 非実施（gate）
- 本 prereg は **draft**。scheduler(R1–R5)実装・run はしない。
- 順序は load-bearing: **HBB closed(済)→ hard-core 固定(済)→ prereg 凍結(要 Taka 確定)→ 実装/run(Taka go)**。
- raw-API cross-model arm・独立 cross-review は本実験の scope 外(post-closure deployment/external-validation track)。
