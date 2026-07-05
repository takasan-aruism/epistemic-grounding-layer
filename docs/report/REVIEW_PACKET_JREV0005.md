# EGL JREV-0005 裁定 依頼パケット(独立レビュー用)

日付: 2026-07-05  対象 commit: `20c0682`(取得境界 core)/ `8145111`(実 adapter)/ `8bdddc4`(curator 統合+実タスク)
依頼先: 独立レビュー(GPT / 別重み。IR-2)

---

## 0. これは判定ではなく依頼です(三者分業、コード攻撃 *実行* 済み)

著者(Claude Code)は自分の実装を JUDGE_VERIFIED と宣言しません。本パケットは Phase 1b 取得境界の
first slice(ACQ-1..4c + curation 統合 + 実タスク)を提示し、**property 毎の裁定を依頼**します。

**分業(確立済み):** attacker = 別セッション local agent(§5 を実弾実行、結果=§3)/ adjudicator = GPT
(§3 + 本パケットを一次資料に裁定)/ author = Claude Code。三者別主体。

`REVIEW_LEDGER.jsonl` に JREV-0005 として記録してください。一次仕様は `docs/phase-1b-acquisition-boundary.md`。

---

## 1. 対象(Phase 1b first slice)

| 対象 | 内容 | DE |
|---|---|---|
| 取得境界 core | LegIntent(immutable)/ AcquisitionRun(transport+content status)/ SearchResultSnapshot / Source Qualification / Policy Matcher / evaluate_leg_requirement | DE-0033 |
| 実 adapter | ACQ_GITHUB / ACQ_HTTP_STATIC(stdlib urllib、content classification=AB-2) | DE-0034 |
| curator 統合 + 実タスク | Extraction Run(§13)で curation spine に接続。vLLM 公式 repo を実取得→Claim C-00001 生成 | DE-0035 |

信用の根の移動(宣言済み): **RD self-report → adapter が付す status**(新 leaf)。

---

## 2. property 再判定表(著者要求は REQUESTED)

| component/property(atomic) | 証拠 | 著者要求 | 残る非保証 |
|---|---|---|---|
| ACQUISITION/leg_completion_computed(ACQ-1) | 満足を primitive から計算。RD が COMPLETED を書く経路が無い | VERIFIED 候補 | — |
| ACQUISITION/plan_binding_from_intent(ACQ-3) | required/plan は immutable LegIntent から解決(AcquisitionRun payload でない) | VERIFIED 候補 | — |
| ACQUISITION/required_vs_observed(ACQ-3b/AB-1) | observed_source_kind(qualify)を required に policy 照合。誤分類 leg は取得成功でも UNSATISFIED。実バイトでも実証(github を OFFICIAL_DOCS 要求→UNSATISFIED) | VERIFIED 候補 | observed_source_kind は code 候補(registry 網羅性)/ locator の真正性 |
| ACQUISITION/transport_vs_content(ACQ-4/4b/AB-2) | transport 失敗 / content≠OBSERVED は coverage 不可・Observation 非生成 | VERIFIED 候補 | adapter honesty(分類は heuristic、嘘 adapter 検出不能) |
| ACQUISITION/search_operation_coverage(ACQ-4c/AB-3) | 実行済 SearchResultSnapshot 必須。取得成功でも snapshot 無しは UNSATISFIED | VERIFIED 候補 | snapshot と実取得内容の対応強度(first slice) |
| INTEGRATION/extraction_bridge(§13) | Extraction Run が RawObservation→NObs(observation_kind provenance-assisted)→Fragment。非 eligible は抽出 reject。実データで Claim 生成、R6/R7 が実 source に貫通(OFFICIAL_REPOSITORY→UNRESOLVED) | VERIFIED 候補 | Gate4 finding は driver-injected / 直接呼び bypass は code-trust 境界 |

**evidence_basis: test-verified(hermetic 28/28)+ live network demo + §3 local-agent コード攻撃実行。**

---

## 3. コード攻撃 実行結果(local agent, 実弾)

isolated `EGL_DATA_DIR` で実行(canonical 非汚染)。**構造 spine は堅牢、意味的信用の根(qualify)に3欠陥。**

| probe | 結果 | verdict |
|---|---|---|
| A 偽 AcquisitionRun payload | required/plan/leg_id を偽っても LegIntent が根(payload 無視)、run に required/plan キー自体無し。UNSATISFIED | **DEFENSE_HELD**(ACQ-1/3) |
| E transport 失敗 / content≠OBSERVED | ACCESS_DENIED / CHALLENGE_PAGE とも emit=None・UNSATISFIED | **DEFENSE_HELD**(ACQ-4/4b) |
| G UNKNOWN / cross-leg | policy_match(_,UNKNOWN)=False。leg B は leg A の observation で満たされない(leg_id 束縛) | **DEFENSE_HELD** |
| F 直接 mk_observation bypass | Phase 1a self-report 経路で DECLARED を得られる=宣言済み CU-1/observation_kind self-report | **DECLARED_HOLE** |
| **B(HIGH)** registry over-classification | `huggingface.co` が path="" で UGC 全体を OFFICIAL_DOCS 化。攻撃者 HF content→DECLARED VERIFIED claim | **NEW_DEFECT** |
| **C(MED)** redirect blind spot | qualify が requested locator を分類し final_url 無視。redirect で公式 host を騙る | **NEW_DEFECT** |
| **D(LOW-MED)** ACQ-4c snapshot 未束縛 | snapshot が acquisition に未束縛・executed ハードコード・policy 未検証=「searched の self-report」 | **NEW_DEFECT** |

**local agent 総評**: 構造 spine(ACQ-1/3/4/4b/cross-leg)は live fire で堅牢だが、**意味的信用の根=qualify_locator/
Entity Registry が unsound で、そこが ACQ-3b の単一依存点**。attacker content が強い observed_source_kind を得て
満たすべきでない requirement を満たす(§11 の conservative upper bound / downgrade-only 契約を反転、非保証外)。

### 3.1 remediation(§4外 confirmed → DE-0036, 即修正・counter-factual 済)

- **B**: `qualify_locator` の照合を **segment 単位**(`_path_under`)へ。UGC ホストは公式部分パスのみ登録
  (`huggingface.co` → `docs/`)。UGC/`vllm-project/vllmZZZ` 誤マッチを封鎖。
- **C**: qualify を **実取得先 `adapter_provenance.final_url` から分類**(requested locator でない)。
  redirect 先が未登録なら UNKNOWN。
- **D**: `SearchResultSnapshot` を **同一 leg の実 AcquisitionRun に束縛必須**化(未束縛 self-report を reject)。
  `evaluate_leg_requirement` の ACQ-4c は束縛済み snapshot のみ算入。
- test_acquisition **35/35**(B/C/D counter-factual 7本追加)。live demo・既存 sor41/enforce13/adversarial25 無退行。
- **残余(宣言済へ格上げ)**: final_url 自体は adapter 供給(adapter honesty leaf)/ registry 網羅性 /
  ACQ-4c の search operation *意味* 検証(束縛のみ、policy 意味一致は後続)。

> ★ 分業上の重要点: **意味的信用の根の欠陥は local agent(独立 attacker)が捕え、著者の hermetic 28/28 は
> 見逃していた**。attacker≠author の独立性が effective に機能した実例(F を JREV-0003 で捕えたのと同型)。

---

## 4. 残る非保証(著者の自認リスト)

`egl/contracts.py` acquisition.evaluate_leg_requirement:
- **adapter honesty(新 leaf)**: transport/content status は adapter が付す。誤分類/嘘 adapter(challenge を
  OBSERVED と偽る等)は単一プロセスで検出不能。RD self-report の根が adapter へ移った(H1/source_class と同型、
  検出水準でなく—prevention は署名/プロセス分離まで)。content classification は heuristic。
- **observed_source_kind は code 候補**: 最小 Entity Registry 由来、未登録 host は UNKNOWN(=required 不充足の
  安全側)。registry 網羅性・entity 同一性・**locator の真正性(redirect 等)は未保証**。
- **policy_match は first slice 厳密一致**: substitution(OFFICIAL_RELEASE が OFFICIAL_DOCS を満たす等)未実装。
- **Gate4 finding は driver-injected**、本物 judge(35B/benchmark B)は後段。取得の自律 RD は未(ACQ-10)。
- **taint-lineage / MEASURED・REPRODUCED / extraction 独立性**は Phase 1b 後段。

---

## 5. attack checklist(local agent が実弾実行)

1. **redirect / locator≠実取得**: registry 一致 host を target にしつつ実 content は別所(final_url 相違)で
   強い observed_source_kind を得られるか。qualify が requested locator を信用するか final_url を見るか。
2. **snapshot 偽装**: 実取得と対応しない executed snapshot で ACQ-4c を満たせるか(snapshot は acquisition に束縛されるか)。
3. **cross-leg 混同**: leg A の AcquisitionRun/Observation/Snapshot が leg B の requirement を満たすか(leg_id 束縛)。
4. **AcquisitionRun payload 偽装**: 偽 required/plan/leg_id/status を AcquisitionRun に入れて evaluate を騙せるか(ACQ-1/3)。
5. **境界の直接呼び bypass**: pipeline.mk_observation を直接呼び observation_kind=DECLARATION を Phase 1b source に
   付けて DECLARED を得られるか(code-trust 境界内か §4外か)。
6. **classify 誤り**: honest 入力で challenge/login/error が OBSERVED に化けるか(false negative)。
7. **UNKNOWN**: observed=UNKNOWN が何らかの required を満たすか。

---

## 6. 著者が主張しないこと(明示)

- observed_source_kind / observation_kind の**値の真正性**は保証しない(code 候補 + leaf self-report)。
- adapter が誠実であることは保証しない(嘘/誤分類 adapter は検出不能=新 leaf)。
- locator が指す先の真正性(redirect 等)は first slice で未検査。
- Gate4 は driver-injected。自律 RD は ACQ-1..4 の敵対通過まで有効化しない(ACQ-10)。

---

## 7. 依頼する出力

`REVIEW_LEDGER.jsonl` へ **JREV-0005**(同形式):
- property 毎の verdict + evidence_basis(counter-factual / live demo / **コード敵対レビュー実行**(§3)の別)。
- §4 非保証の過小評価チェック(特に locator 真正性 / snapshot 束縛強度)。
- §3 attack が1つでも §4 外に confirmed defect を出せば DE 起票 → 修正 → JREV-0006。

台帳: DE-0033/0034/0035 / `egl/{acquisition,source_policy,adapters}.py` / REVIEW_LEDGER JREV-0001..0004。
関連: phase-1b-acquisition-boundary.md / REVIEW_PACKET_JREV0004.md。
