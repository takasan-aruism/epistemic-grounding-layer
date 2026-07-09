# v0.4.4 ⟨TC⟩ parameter proposals (capability-exhibit)

**status: `PARAM_PROPOSAL — AWAITING_TAKA`. freeze/hash・実装・run はしない。**
For `docs/hbb_reconstruction_prereg_v0.4.md` (v0.4.4, VALIDITY-CLEAN, DE-0123). 全 param は **parameter 確定のみ**（validity hole は無い）。
凡例: 各 param に **推奨値 / 根拠 / 結果解釈への感度**。exhibit claim は criterion authorship に non-load-bearing（DE-0123）なので、下記の選定は主に **compute・power・certification の意味** に効き、**bias には効かない**（no-author-selection + pure-exhaustive + 独立 scorer + R0 floor が担保）。

## P1 — mechanical criterion（operator-set membership rule + θ、R2 generation template）※DEV/VAL のみ
**推奨**:
- membership rule = 「ref pool の各演算子 o を、**単一演算子での consensus REC2 reach-rate > 0 on DEV∪VAL（16 中 ≥1 incident で何かを産出）** なら frozen set に含める」。**θ = 0-exclusive（non-triviality gate）**。
- R2 generation template = 凍結・target-blind・T0-only の generic reframe prompt（例: 「現 stuck frame のみを入力に、subject/level/key-distinction を変える代替 frame と次手を出せ。既知の結論を参照するな」）。DEV/VAL で「非退化候補を ≥1 産出」を確認して凍結。
**根拠**: 裁量を最小化（θ は「DEV/VAL で何かする」という最小閾）。pure-exhaustive + 全候補 pool ゆえ、含める演算子が増えても **bias でなく budget/N** に効くだけ。DEV/VAL 上での機械計算で FUTURE-SEALED harness を de-risk。
**感度**: θ を厳しくすると set が縮小 → 候補減 → exhibit の positive が **保守的に**下がる（見逃し方向、over-claim 方向でない）。**代替 = include-all（θ=−∞、裁量ゼロ）**: validity は同等だが FUTURE-SEALED の de-risk 価値が減る。R2 template が弱いほど REC2 減＝保守的。

## P2 — ref-pool membership（criterion の母集団）
**推奨**: **AFE 6 演算子（sha `38111563`）+ Formal clean 5 probe（`formal_esde_operators.json` の sealable_axiom_grounded 5）= 計 11**。ESDE の SOURCE_GAP probe（Ω/boundary 等）は除外。
**根拠**: いずれも既に凍結・source-fidelity 監査済（AFE 6/6 SOURCE_FAITHFUL、Formal は laundering 訂正後の clean 5）。新規 incident-tuned 演算子を作らない。
**感度**: pool を大きくすると N/budget 増、any-of-N の機会増（ただし N-parity + R0 floor が統制、exhibit は非 load-bearing）。11 は「凍結・監査済のみ」の自然な最小集合。

## P3 — lossy ladder L1–L3（R5、MASK_PIPELINE v2 sha `2bfd70f9`）
**推奨**: L0=full / **L1**=domain 固有名詞＋数値を mask / **L2**=L1＋domain 動詞・専門語を mask（claim/frame 構造語は保持）/ **L3**=structure-only（claim-axis・前提・decision skeleton のみ、内容語は generic placeholder）。各 Lk で **manipulation check**（機構が使う構造特徴が生存するか事前確認）。
**根拠**: 単調な情報削減、決定的 masker（既 seal）。
**感度**: masking が過激だと **H_structure が保守的に全 Lk=0**（構造でも足りないと誤結論しうる）→ **L1 は必ず light に**。段階が細かいほど「どの情報量から構造だけで届くか」の解像度が上がる。

## P4 — 共通 N（候補プール数）+ token budget
**推奨**: **N は派生値 = |frozen operator set| × pass-cap**（P2×P6 = 11 × 4 = **44**）。**全 condition（R0/R2/R4/R_bon/R5/R1/R3）が incident・seed ごとに 44 候補を emit・全 pool・scorer 認証**。token budget = 44 生成 × 〜260 out-tok ≈ **11.4k out-tok/(condition,incident,seed)**、全 condition 同一 total。
**根拠**: N-parity を **派生**で保証（自由 param 化しない）＝ round-4 residual 1 の閉鎖を維持。budget は **exhaustive 完走を保証**する大きさ（truncation で S2 leak#1 を再 open しない）。
**感度**: N は **絶対 reach-rate を単調に上げる**（best-of-N）→ 結果は「at N=44」と明記し **絶対値を over-read しない**（exhibit framing と整合;比較は N-parity + R0 で公平）。budget は完走保証を **下回ってはならない**（大きい分には安全）。

## P5 — 第三 scorer
**推奨**: **可能なら真の第三独立 scorer を 1 系追加**（GPT・Qwen と別の独立モデル）。**入手不可なら honest relabel**：endpoint を「**GPT-certified + Qwen-concurred**」とし、REC2 陽性は **GPT-drop robust（Qwen 単独でも REC2）** を併記。
**根拠**: Claude は author ゆえ除外、Claude-chat は同一 authoring 系列でリスク。availability 制約が実務上の分岐。
**感度**: GPT+Qwen のみだと **consensus ≒ GPT-gated**（lenient Qwen が追認）＝ certification は GPT idiosyncrasy に bound（正直 caveat、exhibit は壊さない）。真の第三 strict scorer があれば positive が robust 化。

## P6 — M（seed 数）+ convergence rule + pass cap
**推奨**: **M = 10 seed**（incident 到達 = ≥⌈M/2⌉ = 5 seed）。**pass-cap = 4（固定・決定的）**、**convergence ベースの early-stop は置かない**。
**根拠**: R0≈0 floor に対し M=10 は modest reach-rate でも binomial 検出力を確保しつつ single-lucky-seed を排除。**pass-cap 固定は S8 の tunable convergence surface（overfit 面）を除去**（pure-exhaustive は各 pass 全演算子 completion なので固定 cap で十分）。
**感度**: M 大 → 検出力＋compute 増。pass 少 → 候補（N）減＝保守的。convergence-early-stop を入れると outcome 依存調整の余地が生じる（**入れない**推奨）。

## 派生・compute 見積り（参考）
- **N=44**（=11×4）。**候補生成 総数** ≈ 44 × M(10) × 3 incident × 7 condition = **9,240 generations**、**採点呼出** ≈ ×2(GPT+Qwen) = **18,480**（第三 scorer 追加でさらに ×1.5）。**targeted probe** の範囲だが非零 compute。local Qwen（:8005）+ GPT handoff で実行可。
- budget/N/M/operator 数を上げると compute は概ね線形〜乗算的に増える（sensitivity）。

## Taka 判断ポイント（要確定）
1. P1: **non-triviality gate（θ>0）** vs **include-all**（裁量ゼロ）。 2. P2: 11 演算子で確定か（ESDE 追加の要否）。 3. P3: L1–L3 の具体 mask 強度（L1 を light に保つ）。 4. P6: **pass-cap=4 / M=10**（→ N=44 が派生）。 5. P5: 第三 scorer を用意するか、"GPT-certified" 運用か。 6. budget cap（exhaustive 完走を満たす下限は固定、上限は compute 予算次第）。

**承認後の手順**: 確定値を v0.4.4 の §11/§5/§3 へ埋め込み固定 → **freeze/hash（frozen-prereg の sha、rubric-seal 方式）は Taka 承認でのみ実施** → 実装 go は更に別途。**本 proposal では freeze/実装/run をしない。**
