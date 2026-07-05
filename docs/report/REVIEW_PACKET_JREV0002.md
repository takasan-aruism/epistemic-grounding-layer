# EGL JREV-0002 再判定 依頼パケット(独立レビュー用)

日付: 2026-07-05  対象 commit: `cab6800..cad431c`(JREV-0001 remediation)
依頼先: 独立レビュー(GPT / 別重み。IR-2: 独立性は local swap でなく別 API で調達)

---

## 0. これは判定ではなく依頼です

著者(Claude Code)は**自分の修正を JUDGE_VERIFIED と宣言しません**。それはこの系が最初に殺すと
決めた「生成者の自己評価の無検証追認」そのものだからです。本パケットは JREV-0001 の各 finding に
対する remediation を提示し、**property 毎の再判定を依頼**します。各 property の「著者要求ステータス」は
REQUESTED であって verdict ではありません。§4 に**残る非保証(著者が過大報告していないかの検査面)**を
先に開示します。§5 の attack checklist で remediation を破れるか試してください。

判定は JREV-0001 と同形式(property-level + evidence_basis 併記)で `REVIEW_LEDGER.jsonl` に
JREV-0002 として記録してください。

---

## 1. JREV-0001 → remediation 対応

| JREV-0001 finding | verdict | remediation | DE |
|---|---|---|---|
| R5 ABSENCE→SPECIFIED | REJECTED | ABSENCE は validation_mode を持たず `absence_validation{mode:SEARCH_COVERAGE_COMPLETED, search_plan_id}`。SPECIFIED は polarity=NEGATIVE 専用。derive は ABSENCE で reject | DE-0018 |
| R2 CORRECTION/COMPLETION transition | NOT_VERIFIED | CR-1..4(class 必須/METADATA epistemic 不変/FACTUAL basis 必須/lifecycle 不可)+ CP-1..3(missing→concrete のみ/既存不変) | DE-0019 |
| (恒久対策) | — | 全 guard が non_guarantees を宣言(`egl/contracts.py`)。R2/H4b/R1 が事前に自認リストへ | DE-0020 |
| R1 semantic write authority | NOT_VERIFIED | 検出水準: PRIVILEGED_EVENTS + issue_capability(GRANT event)+ audit_write_authority。**prevention は騙らず**保証は検出可能性 | DE-0021 |
| R3 claim_key identity | NOT_VERIFIED | canonicalize_scope(case/区切り/alias)を claim_key 前に必須化。version algebra/entity は残 | DE-0022 |
| R4 leg binding | NOT_VERIFIED | 敵対テストで forgery 確定 → LegIntent 仕様確定(取得ラッパー時)。今は非保証宣言 | DE-0023 |
| H4b statement→scope | NOT_VERIFIED | 敵対テストで GC-7 miss 確定 → GC-6 後段 lint(Phase 1b)。F1 は skeleton で driver-injected=未検証 | DE-0023 |

---

## 2. property 再判定表(著者要求は REQUESTED)

| component/property | JREV-0001 | remediation 後の証拠 | 著者要求(REQUESTED) | 残る非保証 |
|---|---|---|---|---|
| DE0006/id_event_atomicity | VERIFIED | (据置) | 維持 | — |
| L4/validation_mode_derivation | **REJECTED** | test_sor T8c-e(NEGATIVE→SPECIFIED / ABSENCE reject / 別軸)。canonical C-00002 は absence_validation | 再評価(REJECTED 解消?) | source_class 真正性(leaf self-report) |
| CORRECTION_COMPLETION/transition_legality | NOT_VERIFIED | test_sor T11(CR-1/2/3/4・CP-1/2 + GPT 3 counter-factual 全通過) | VERIFIED 候補 | 専用 transition event 未実装(lifecycle 遷移は別途) |
| APPEND_EVENT/semantic_write_authority | NOT_VERIFIED | test_adversarial R1(forge 検出・enforce ratchet) | **検出水準のみ**(prevention 非目標) | prevention 不可(単一プロセス)/ Claim・Decision・leg 未 wiring |
| H3/claim_key_identity | NOT_VERIFIED | test_adversarial R3(case gaming 封鎖) | **surface 層のみ** | version algebra / entity 同一性(Phase 1b) |
| H1/leg_authenticity | NOT_VERIFIED | test_adversarial R4(forgery 再現=vuln 確定) | **未修正(仕様確定のみ)** | leg binding 真正性 → LegIntent 待ち |
| H4/statement_scope_binding | NOT_VERIFIED | test_adversarial H4b(GC-7 miss 確定) | **未修正(gap 記録のみ)** | statement→scope self-report → GC-6 待ち |
| DE0007/revision_completeness | VERIFIED | (据置) | 維持 | 2段以深 nested |

**evidence_basis は全て test-verified(counter-factual 含む)。コードレベル敵対レビューは本 JREV-0002 が初回。**

---

## 3. テスト証拠

| 試験 | 件数 | 主な counter-factual / forge |
|---|---|---|
| test_enforce.py | 13/13 | T1c(leg 反転で outcome 変化)ほか |
| test_sor.py | 36/36 | T8(ABSENCE reject/NEGATIVE→SPECIFIED)、T11(CR/CP + REJECTED→VERIFIED 復活 reject 等)、T12(guard non_guarantees 宣言) |
| test_adversarial.py | 11/11 | R1b(forge 検出)、R3b(case gaming 封鎖)、R4(forgery 再現)、H4b(GC-7 miss) |
| verify_rebuild.py | RC-3/RC-4 PASS | — |

---

## 4. 残る非保証(著者の自認リスト = 過大報告していないかの検査面)

`egl/contracts.py` GUARD_CONTRACTS の non_guarantees(全 guard 宣言済)。要点:
- **R1 は検出のみ**: 単一プロセスで capability は forge 可能。保証は「GRANT 記録なき privileged write は audit で検出可能」。prevention は騙らない。Claim/Decision/leg は未 wiring(audit で unprotected 可視、enforce_types で ratchet)。
- **R3 は surface のみ**: version algebra(0.11 vs >=0.11 の包含)と entity 同一性(model variant)は未解決 → 依然 key が割れ得る。
- **R4 未修正**: leg_plan_id binding forgery は現状可能(敵対テストで再現)。修正=LegIntent は取得ラッパー実装時。
- **H4b 未修正**: GC-7 は statement 主張を見ない。主防衛の Gate4 F1 は skeleton で driver-injected=未検証。
- **M4**: 2段以深 nested completeness は RMW 規律で担保、構造強制でない。
- **transition event 未実装**: CORRECTION は lifecycle 遷移を拒否するが、正当な遷移(REJECTED→撤回等)の専用 event は未実装。

---

## 5. attack checklist(remediation を破れるか)

1. **audit 回避(R1)**: GRANT 記録を残さず privileged write を audit clean にできるか。あるいは self-grant(RD が自分に CORRECTOR を GRANT)を audit が「正当」と誤認するか(=検出はできても解釈が甘いか)。
2. **claim_key 分割(R3)**: canonicalize_scope を通しても key を割れるか。version 表記(>=/~/範囲)、entity variant(`Qwen/…-NVFP4` vs `Qwen…`)、alias 未登録語で。
3. **CORRECTION/COMPLETION 政策(R2)**: CR/CP を満たしつつ不正な state 遷移を作れるか。例: FACTUAL correction に形だけの basis を付けて epistemic 改変、COMPLETION で empty collection(CP-3 の境界)を悪用。
4. **R5 の完全性**: absence_validation 分離後も、ABSENCE と NEGATIVE(明示的不支持)を混同させる経路が残るか。polarity 判定自体の self-report は?
5. **leg forgery(R4)**: 敵対テストの forgery が「仕様確定で許容」の範囲か、それとも今すぐ塞ぐべき severity か。
6. **guard 宣言の網羅性(恒久対策)**: non_guarantees に**載っていない**未保証性質を見つけられるか(=自認リストの穴)。これが見つかれば恒久対策自体が不完全。
7. **evidence basis の自己欺瞞**: 各 counter-factual が本当に根を検査しているか、driver 正直リプレイに退化していないか。

---

## 6. 著者が主張しないこと(明示)

- bundle 一括 JUDGE_VERIFIED は要求しない。property-level のみ。
- R4/H4b は**未修正**(仕様確定/gap 記録のみ)。VERIFIED を要求しない。
- R1 は**検出水準**であって prevention ではない。
- R3 は**surface 層**であって scope algebra/entity 解決ではない。
- 本 remediation の evidence は test-verified 止まり。**コード敵対レビューは本 JREV-0002 が初回**。

---

## 7. 依頼する出力

`REVIEW_LEDGER.jsonl` へ **JREV-0002**(JREV-0001 と同形式):
- property 毎の verdict(VERIFIED / NOT_VERIFIED / REJECTED / DEFERRED_ACCEPTED)+ evidence_basis(counter-factual / 設計レビュー / **コード敵対レビュー**の別を明記)。
- §4 の非保証のうち、**著者が過小評価しているもの**があれば指摘(JREV-0001 の R3 射程過小・R2 自認漏れと同じ判定)。
- §5 の attack が1つでも §4 の外に confirmed defect を出せば、DE 起票 → 修正 → JREV-0003。

台帳: DE-0018〜0023 / REVIEW_LEDGER.jsonl JREV-0001 / `egl/contracts.py`。
関連: REPORT_REVIEW_PACKET_G1_L4.md(初回)。
