# EGL JREV-0004 裁定 依頼パケット(独立レビュー用)

日付: 2026-07-05  対象 commit: `ecdc03b`(R8 / DE-0030)+ `ba593ae`(R7 / DE-0029)
依頼先: 独立レビュー(GPT / 別重み。IR-2)

---

## 0. これは判定ではなく依頼です(三者分業、コード攻撃 *実行* 済み)

著者(Claude Code)は自分の修正を JUDGE_VERIFIED と宣言しません。本パケットは JREV-0003 で GPT が
確定した §4外 design defect 2件(R7/R8)の remediation を提示し、**property 毎の裁定を依頼**します。

**分業(JREV-0002 §0 で確立、JREV-0003 で実行段階に到達):**
- **attacker = 別セッション local agent**。§5 attack を実弾実行——結果は §3。
- **adjudicator = GPT**。§3 の attack 結果 + 本パケットを一次資料に verdict を裁定。
- attacker(local agent)・author(Claude Code)・adjudicator(GPT)は三者別主体。

判定は同形式(property-level + evidence_basis)で `REVIEW_LEDGER.jsonl` に JREV-0004 として記録してください。

---

## 1. JREV-0003 → remediation 対応

| JREV-0003 finding | verdict | remediation | DE |
|---|---|---|---|
| R8 evidence-bag global veto(重要) | CONFIRMED | derive を袋 → **eligible typed SUPPORTS path** 導出へ。GENERATED は独立資格なし=無視だが**他 path を大域 veto しない**(非単調の除去)。relation_type==SUPPORTS のみ算入 | DE-0030 |
| R7 validation_mode/polarity asymmetry | CONFIRMED | **mode ⊥ polarity**(Taka 裁定=直交化、R5 supersede)。DECLARATION→DECLARED / SPECIFICATION→SPECIFIED(polarity 不問)。負の理由は別 field `negative_basis`(Gate0 が NEGATIVE に enum 必須) | DE-0029 |

---

## 2. property 再判定表(著者要求は REQUESTED)

| component/property(atomic) | JREV-0003 | remediation 後の証拠 | 著者要求 | 残る非保証 |
|---|---|---|---|---|
| L4/evidence_path_derivation(R8) | (defect) | 袋→eligible SUPPORTS path。counter-factual T8i(無関係 GENERATED を足しても DECLARED 維持=単調)。GENERATED-only→UNRESOLVED | VERIFIED 候補(単調・path-based) | taint-lineage(generated が抽出に関与)Phase 1b |
| L4/mode_polarity_orthogonality(R7) | (defect) | 2x2 test T8a/c/g/j: DECLARATION→DECLARED・SPECIFICATION→SPECIFIED(polarity 不問)。ABSENCE≠SPECIFIED は absence_validation 別軸で維持 | VERIFIED 候補 | observation_kind 自体が RD self-report |
| GATE0/negative_basis_required(R7) | (新) | NEGATIVE claim は negative_basis∈enum を Gate0 必須。adversarial R7 Gate0 3本(欠落/不正→reject、正規→pass) | VERIFIED 候補 | negative_basis の**値**は RD 供給(leaf self-report) |

**evidence_basis: test-verified(counter-factual T8 2x2 + T8i 単調)+ §3 の local-agent コード攻撃実行結果。**

---

## 3. コード攻撃 実行結果(local agent, 実弾)

別セッションの local agent が §5 を isolated `EGL_DATA_DIR` で実行(canonical data/ と data_jrev0003/ は
md5 一致=非汚染)。**§4外 NEW_DEFECT は検出されず。**

| attack | 実出力(要点) | verdict |
|---|---|---|
| 1 R8 単調性/eligibility | base PRIMARY+DECL→DECLARED。+GENERATED/+SECONDARY/+dangling/+REFUTES→PRIMARY+DECL/+CONTRADICTS→PRIMARY+DECL、**単独でも全部盛りでも DECLARED を維持**(mode 低下なし)。REFUTES/CONTRADICTS *単独* は UNRESOLVED(非 SUPPORTS は mode を grant しない) | **DEFENSE_HELD**(単調・path-based) |
| 2 GENERATED 独立資格なし | GENERATED+DECL only→UNRESOLVED、PRIMARY+MEAS+GENERATED+DECL→UNRESOLVED | **DEFENSE_HELD** |
| 3 R7 2x2 直交性 | DECLARATION×{POS,NEG}→DECLARED、SPECIFICATION×{POS,NEG}→SPECIFIED。negative_basis を変えても mode 不変(inert)。end-to-end で NEGATIVE claim が validation_mode=DECLARED/status=VERIFIED/negative_basis 保持=**polarity 漏れなし** | **DEFENSE_HELD** |
| 4 negative_basis 迂回 | curate 経由: NEGATIVE 欠落→DEFER、bogus→DEFER、正規→ACCEPT。ABSENCE は negative_basis 不要(≠NEGATIVE、SC-2 別 gate)。**4d 直接 apply_outcome(Gate0 迂回)は NEGATIVE/negative_basis=None を Claim 化するが、これは CU-1/単一プロセス code-trust 境界=宣言済み非保証の範囲**(§4外ではない) | **DEFENSE_HELD**(sanctioned path) |
| 5 回帰 | 未知 polarity→UNRESOLVED、ABSENCE→ValueError、MEASUREMENT→UNRESOLVED。run/run2/demo 全通。negative_basis 必須化は POSITIVE/ABSENCE flow を壊さない | **DEFENSE_HELD** |
| 6 §4外スキャン | **NEW_DEFECT なし**。observation 2件(下記) | — |

**observation(欠陥ではない・GPT 裁定材料):**
- **(a) negative_basis に二重防御なし**: polarity は Gate0+derive の二層(gates.py コメント「二重防御」)だが、
  negative_basis は Gate0 のみ(derive/apply_outcome/Claim 構築が再検査しない)。trust model 内だが非対称。
  Gate0 が唯一の chokepoint でなくなる時に second-layer assertion の価値。
- **(b) gate1 と derive の relation_type 非対称**: gate1_evidence は REFUTES/CONTRADICTS を grounds として
  受理(relation_type 非検査)する一方、derive は非 SUPPORTS を無視。REFUTES のみの候補は Gate1 通過するが
  derive は UNRESOLVED=**安全側 fail-closed**。unearned mode を grant しない。欠陥でなく asymmetry。

**overall(local agent)**: 宣言 scope 内で **R7/R8 は sound**。R8 は真に単調(大域 GENERATED veto 消失、
追加証拠が valid PRIMARY+DECLARATION path を下げない、GENERATED は独立資格なし)。R7 直交化は **polarity 漏れ
ゼロ**(mode は observation_kind の純関数、negative_basis は inert、status/mode に polarity 再エンコードなし)。
**sanctioned path 上に negative_basis 迂回なし**(唯一の迂回は Gate5 直呼び=宣言済み単一プロセス境界)。

---

## 4. 残る非保証(著者の自認リスト)

`egl/contracts.py` gates.derive_validation_mode(R7/R8 実装後):
- **taint-lineage 未実装(R8 残余)**: mode は eligible な非 GENERATED SUPPORTS path から導出(大域 veto 撤廃・単調)。
  ただし generated 素材が primary fragment の抽出に *関与* した場合の taint 伝播(DERIVED_FROM_GENERATED /
  TAINT_RELEVANT)は未表現=Phase 1b。大域 any-GENERATED→fail では近似しない。
- **observation_kind / negative_basis / source_class は leaf self-report**: R7 で mode を polarity から
  切り離し negative_basis を別軸化したが、**どの enum 値を付すか**は RD 供給。種別/理由/権威の詐称は
  単一プロセスでは検出不能(署名/プロセス分離まで)。
- **MEASURED/REPRODUCED 未導出**(Phase 1b/F3a)。
- **Gate4 finding は driver-injected**、取得境界(retrieval/LegIntent)未実装。

---

## 5. attack checklist(local agent が実弾実行)

1. **R8 単調性/eligibility**: 追加証拠で mode が *下がる*(非単調)経路。GENERATED/SECONDARY/dangling/
   非 SUPPORTS(REFUTES 等)relation で、拾うべき path を落とす or 拾うべきでない path を拾うか。
2. **R8 GENERATED 独立資格なし**: GENERATED+DECLARATION only → UNRESOLVED を確認。
3. **R7 2x2 直交性**: PRIMARY×{DECLARATION,SPECIFICATION}×{POSITIVE,NEGATIVE}。mode が observation_kind
   のみに依存するか。polarity がどこか(apply_outcome status 等)から漏れ戻らないか。
4. **R7 negative_basis 迂回**: NEGATIVE が negative_basis なしで Claim 化できるか(Gate0 迂回)。
   negative_basis が mode に影響しない(inert)ことの確認。
5. **回帰**: 未知 polarity fail-closed / ABSENCE raise / MEASUREMENT UNRESOLVED が維持か。
   negative_basis 必須化が正当な POSITIVE/ABSENCE flow を壊さないか(run/run2/demo)。
6. **その他**: §4 に載っていない未保証性質。

---

## 6. 著者が主張しないこと(明示)

- observation_kind / negative_basis / source_class の**値の真正性**は保証しない(leaf self-report)。
- MEASURED/REPRODUCED を導出する能力は無い(Phase 1a、意図的に UNRESOLVED)。
- taint-lineage(generated が導出に関与)は未実装(Phase 1b)。大域 veto の除去は単調性のためで、
  taint の放棄ではない。
- demo は取得の実装ではない。

---

## 7. 依頼する出力

`REVIEW_LEDGER.jsonl` へ **JREV-0004**(同形式):
- property 毎の verdict + evidence_basis(counter-factual / **コード敵対レビュー実行**(§3)/ 設計レビューの別)。
- §4 非保証の過小評価チェック。
- §3 attack が1つでも §4 外に confirmed defect を出せば DE 起票 → 修正 → JREV-0005。

台帳: DE-0029(R7)/ DE-0030(R8)/ `egl/contracts.py` / REVIEW_LEDGER JREV-0001..0003。
関連: REVIEW_PACKET_JREV0003.md。
