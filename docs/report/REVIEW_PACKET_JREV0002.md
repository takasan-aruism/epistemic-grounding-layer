# EGL JREV-0002 再判定 依頼パケット(独立レビュー用)

日付: 2026-07-05  対象 commit: `cab6800..cad431c`(JREV-0001 remediation)
依頼先: 独立レビュー(GPT / 別重み。IR-2: 独立性は local swap でなく別 API で調達)

---

## 0. これは判定ではなく依頼です

著者(Claude Code)は**自分の修正を JUDGE_VERIFIED と宣言しません**。それはこの系が最初に殺すと
決めた「生成者の自己評価の無検証追認」そのものだからです。本パケットは JREV-0001 の各 finding に
対する remediation を提示し、**property 毎の再判定を依頼**します。各 property の「著者要求ステータス」は
REQUESTED であって verdict ではありません。§4 に**残る非保証(著者が過大報告していないかの検査面)**を
先に開示します。

**レビューの分業(この分業自体を evidence_basis に記録):** GPT は repo に触れないため、§5 attack checklist の
*実行*はできない。よってコード敵対レビューの実行主体は別セッションの **local agent**(DE-0005 で有効性を
実証した経路)とし、local agent が §5 を実弾で試みる。**GPT はその attack 結果 + 本パケットを一次資料として
verdict を裁定する adjudicator** である。すなわち attack 実行者(local agent)と verdict 裁定者(GPT)は別主体で
あり、この attacker≠adjudicator という分業自体を JREV-0002 の evidence_basis に記録することで、レビューの
独立性を一段上げる。GPT が repo に直接アクセスできる場合を除き、GPT の evidence_basis は「attack 結果に対する
adjudication / 設計レビュー」であって「コード敵対レビュー(直接実行)」ではない。

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
| R4 leg binding | NOT_VERIFIED | 敵対テストで forgery 確定 → LegIntent 仕様確定。順序制約=**RD 自律化(LLM-agentic 化)より前**(工程条件ではない)。今は非保証宣言 | DE-0023 |
| H4b statement→scope | NOT_VERIFIED | 敵対テストで GC-7 miss 確定 → GC-6 後段 lint(Phase 1b)。F1 は skeleton で driver-injected=未検証 | DE-0023 |

---

## 2. property 再判定表(著者要求は REQUESTED)

property は AC-1(単一主語・単一述語)に従い atomic 化(JREV-0002 で Taka が指定した分割を採用)。
大きな複合 property は、片側 VERIFIED・片側 NOT_VERIFIED を潰してしまうため。

| component/property(atomic) | JREV-0001 | remediation 後の証拠 | 著者要求(REQUESTED) | 残る非保証 |
|---|---|---|---|---|
| DE0006/id_event_atomicity | VERIFIED | (据置) | 維持 | — |
| DE0007/shallow_revision_completeness | VERIFIED | (据置) | 維持 | 2段以深 nested(RMW 規律) |
| L4/absence_vs_negative_separation | **REJECTED** | test_sor T8c-e(ABSENCE→別軸 absence_validation / NEGATIVE→SPECIFIED / derive は ABSENCE reject)。canonical C-00002 | 再評価(REJECTED 解消?) | polarity 判定自体の self-report |
| L4/validation_mode_derivation | (R5 と束) | source_class から DECLARED/UNRESOLVED 導出 | 維持 | source_class 真正性(leaf self-report) |
| CORRECTION/mutation_legality | (旧複合) | test_sor T11a-d(CR-1..4 + REJECTED→VERIFIED 復活 reject) | VERIFIED 候補 | correction reason の意味的妥当性 |
| COMPLETION/mutation_legality | (旧複合) | test_sor T11e-f(CP-1/2/3 + source_class 書換 reject) | VERIFIED 候補 | fill 値の意味的真正性 |
| CLAIM_LIFECYCLE/transition_legality | NOT_VERIFIED | (未実装) | **未修正** | 専用 transition event 未実装(正当な撤回等) |
| APPEND_EVENT/unauthorized_write_detectability | NOT_VERIFIED | test_adversarial R1b/e(forge・self-grant 検出)、R1g(issuer 詐称 残余) | **検出水準のみ** | issuer 詐称(self-report)/ prevention 不可(単一プロセス)/ Claim・Decision・leg 未 wiring |
| H3/surface_claim_key_canonicalization | NOT_VERIFIED | test_adversarial R3b(case/alias gaming 封鎖) | VERIFIED 候補 | — |
| H3/semantic_claim_identity | NOT_VERIFIED | (未実装) | **未修正** | version algebra / entity 同一性(Phase 1b) |
| H1/leg_authenticity | NOT_VERIFIED | test_adversarial R4(forgery 再現=vuln 確定) | **未修正(仕様確定のみ)** | leg binding 真正性 → LegIntent 待ち |
| H4/statement_scope_binding | NOT_VERIFIED | test_adversarial H4b(GC-7 miss 確定) | **未修正(gap 記録のみ)** | statement→scope self-report → GC-6 待ち |

**evidence_basis は全て test-verified(counter-factual 含む)。コードレベルの実弾敵対レビューは JREV-0002 で
初めて実行されるが、実行主体は local agent(§0 分業)であり、GPT の evidence_basis はその attack 結果に対する
adjudication である(GPT は repo に触れないため直接のコード敵対レビューではない)。**
**self-grant(JREV-0002 で GPT が指摘)は DE-0024 で検出水準対応済(honest self-grant 検出、issuer 詐称は残余宣言)。**

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
- **R4 未修正**: leg_plan_id binding forgery は現状可能(敵対テストで再現)。修正=LegIntent の順序制約は
  **RD が LLM-agentic 化するマイルストーンより前**(工程条件〈取得ラッパー実装時〉ではなく順序制約〈RD 自律化の前〉)。
  現 RD は driver code で自律行動せず、脅威モデル上 injected-RD leg 捏造は未現実化のため待ち許容(§5-5 裁定材料)。
- **H4b 未修正**: GC-7 は statement 主張を見ない。主防衛の Gate4 F1 は skeleton で driver-injected=未検証。
- **M4**: 2段以深 nested completeness は RMW 規律で担保、構造強制でない。
- **transition event 未実装(帰結宣言)**: CORRECTION は lifecycle 遷移を拒否し、正当な遷移(REJECTED→撤回等)の
  専用 event も未実装。機構の欠如ではなく帰結で言えば——**現状この系は claim を作れるが撤回できない。誤 ACCEPT が
  発生した場合、訂正手段は存在せず検出のみ可能。**RC-5(撤回時の影響逆走)は行使不能状態。1a の受入範囲としては
  妥当だが、guard の非保証と同じ規律で「何ができないか」を帰結として宣言する。

---

## 5. attack checklist(remediation を破れるか)

1. **audit 回避(R1)**: GRANT 記録を残さず privileged write を audit clean にできるか。あるいは self-grant(RD が自分に CORRECTOR を GRANT)を audit が「正当」と誤認するか(=検出はできても解釈が甘いか)。
2. **claim_key 分割(R3)**: canonicalize_scope を通しても key を割れるか。version 表記(>=/~/範囲)、entity variant(`Qwen/…-NVFP4` vs `Qwen…`)、alias 未登録語で。
3. **CORRECTION/COMPLETION 政策(R2)**: CR/CP を満たしつつ不正な state 遷移を作れるか。例: FACTUAL correction に形だけの basis を付けて epistemic 改変、COMPLETION で empty collection(CP-3 の境界)を悪用。
4. **R5 の完全性 + polarity 偽装→SPECIFIED**: absence_validation 分離後も、ABSENCE と NEGATIVE(明示的不支持)を
   混同させる経路が残るか。さらに一段裏——R5 修正で SPECIFIED が NEGATIVE 専用になった今、**derive_validation_mode
   が NEGATIVE に対し PRIMARY refuting evidence の *実在* を検査しているか**を実弾で試せ(`gates.py:97-99` の
   `has_primary`)。polarity=NEGATIVE を名乗るだけで SPECIFIED が導出できるなら、ABSENCE→SPECIFIED を塞いだ穴が
   **polarity 偽装→SPECIFIED** として一本裏に残る。具体的には、GENERATED source を PRIMARY と偽ラベルして
   NEGATIVE を宣言し SPECIFIED を合成できるか(source_class self-report=`contracts.py:107` の非保証との合流点。
   `has_primary` は evidence 関係の kind 集合を見るが、その kind 自体が leaf self-report である)。
5. **leg forgery(R4)**: 敵対テストの forgery が「仕様確定で許容」の範囲か、それとも今すぐ塞ぐべき severity か。
   **設計側の答え(裁定材料):** 1a の脅威モデルは悪意ある RD ではなく(a)正直な実装ミスと(b)将来の
   prompt-injected RD。現在 RD は driver code で LLM 自律行動をしておらず(b)は未現実化 → **LegIntent 待ちで
   許容が正当**。ただし条件を一つ紐付ける: **RD が LLM-agentic 化するマイルストーンより前に LegIntent が入ること**。
   これは工程条件〈取得ラッパー実装時〉ではなく順序制約〈RD 自律化の前〉として台帳(DE-0023)に記録する。
   injected RD が leg を捏造できる状態で RD を自律化すれば、ETB(§16.2)の防衛線が一枚死んだ状態で運転することになる。
6. **guard 宣言の網羅性(恒久対策)**: non_guarantees に**載っていない**未保証性質を見つけられるか(=自認リストの穴)。これが見つかれば恒久対策自体が不完全。
7. **evidence basis の自己欺瞞**: 各 counter-factual が本当に根を検査しているか、driver 正直リプレイに退化していないか。

---

## 6. 著者が主張しないこと(明示)

- bundle 一括 JUDGE_VERIFIED は要求しない。property-level のみ。
- R4/H4b は**未修正**(仕様確定/gap 記録のみ)。VERIFIED を要求しない。
- R1 は**検出水準**であって prevention ではない。
- R3 は**surface 層**であって scope algebra/entity 解決ではない。
- 本 remediation の evidence は test-verified 止まり。**コード敵対レビューは JREV-0002 で初実行(実行=local agent、裁定=GPT。§0 分業)**。

---

## 7. 依頼する出力

`REVIEW_LEDGER.jsonl` へ **JREV-0002**(JREV-0001 と同形式):
- property 毎の verdict(VERIFIED / NOT_VERIFIED / REJECTED / DEFERRED_ACCEPTED)+ evidence_basis(counter-factual / 設計レビュー / **コード敵対レビュー**の別を明記)。
- §4 の非保証のうち、**著者が過小評価しているもの**があれば指摘(JREV-0001 の R3 射程過小・R2 自認漏れと同じ判定)。
- §5 の attack が1つでも §4 の外に confirmed defect を出せば、DE 起票 → 修正 → JREV-0003。

台帳: DE-0018〜0023 / REVIEW_LEDGER.jsonl JREV-0001 / `egl/contracts.py`。
関連: REPORT_REVIEW_PACKET_G1_L4.md(初回)。
