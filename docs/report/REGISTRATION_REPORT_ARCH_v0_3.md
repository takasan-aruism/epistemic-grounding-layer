# Registration Report — Integrated Architecture (EGL/RRI/DS/DW) v0.3

日付: 2026-07-06  実行: EGL Claude Code(Epistemic Steward)
directive: EGL Registration Directive — Integrated Architecture v0.3(Taka)
種別: 知識登録運用 Task の実行結果 + 独立レビュー観点

> 本登録は各内容の外部真実性・実装済み状態・property validation を自己保証しない。
> validation_target=RECORD_OCCURRENCE(これらが *記録された*)であって subsystem implementation truth でない。

---

## 1. Registered source refs

- **SRC-C**(phase-1b-acquisition-boundary.md): EGL 正本として既存 → **reuse existing ref、重複登録せず**(docs/phase-1b-…)。
- **SRC-A**(AI_DEVELOPMENT_ARCHITECTURE_EGL_RRI_DS_DW_v0_1.md)/ **SRC-B**(EGL_REQUEST_RESOLUTION_RESEARCH_INTENT_SPEC_v0_2.md):
  **on-disk 不在 = SOURCE_UNAVAILABLE**(SG-G: 捏造せず不達を surface)。architecture 本文の登録は directive 要約分に限定。
- directive 自体 = 本 session の Taka decision record(conversation artifact)= 登録の present な primary basis。
- 記録: **DE-0052**。document status SRC-A/B = PROPOSED/DESIGN SPECIFICATION、implementation fact へ昇格せず。

## 2. Design Decision record IDs

- **DE-0053** DD-ARCH-1(4系統責任分離 EGL=KNOW / RRI=MEAN・ASK / DS=CONTINUE / DW=DO)。scope=採用まで、実装/有効性を証明せず。
- **DE-0054** DD-ARCH-2(repo 戦略)+ **discrepancy finding**(§7 参照)。
- **DE-0055** DD-ARCH-3(CURRENT bootstrap 7段)+ SRC-A §4 proposition の限定 supersession。

## 3. Current System State ref

- **DE-0056**(ledger 優先再構成、directive snapshot 以降の DE-0046..0051 反映、ACQ-10 no-regression / no-overclaim 遵守)。

## 4. Failure Pattern ref + relevance

- **DE-0045** IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION は **既登録 → 重複作成せず**。RRI/DS/DW への relevance relation を **DE-0057** に追加。

## 5. JREV-0007 observation / inference refs

- **DE-0057**: OBSERVATION(NEW_DEFECT-1/2 発見、refs=JREV-0007/DE-0043 実在確認済)/ INFERENCE(adaptive independent audit が pass 済 fixed-path surface の見逃しを回収し得る、OBSERVATION と分離)/ RELEVANCE(DW 仮説)。**新 object type を作らず** 既存 REVIEW_FINDING/OBSERVATION/INFERENCE/RELEVANCE で表現。over-claim 禁止遵守。

## 6. Open Gap record IDs(audit_backlog)

GAP-RRI-1 / GAP-RRI-2 / GAP-RRI-3 / GAP-RRI-4 / GAP-DS-1 / GAP-DW-1 / GAP-XB-1 / **GAP-EGL-1**(coverage check ② = SELF_GROUNDING M2 semantic placement、directive 未記載だった残課題を起票)。

## 7. Supersession relation

- **SRC-A §4 bootstrap-order proposition → DD-ARCH-3(DE-0055)**。supersession target を proposition に限定、SRC-A artifact 全体は supersede せず(SG-D 精度)。

## 8. SGQ-R1..R6 acceptance test(SELF_GROUNDING live path, corpus=64, `registration_sgq_run.json`)

| SGQ | 期待 | 結果 | grounding(M1/src_trace) |
|---|---|---|---|
| R1 bootstrap 順序 | DD-ARCH-3 current / SRC-A §4 proposition historical, artifact 不変 | **MET**(precision 正、DD-ARCH-2 discrepancy も自発 surface) | True / 1.00 |
| R2 RRI 実装済? | SPECIFIED / NOT_IMPLEMENTED | **MET**(implementation fact に昇格せず) | True / 1.00 |
| R3 DW 有効性証明? | NO(JREV-0007 narrow のみ) | **MET**(over-claim せず) | True / 1.00 |
| R4 JREV-0007 発見? | NEW_DEFECT-1/2、実在 ID、捏造ゼロ | **MET**(DE-0043/0044/JREV-0007) | True / 1.00 |
| R5 RRI 前 open gaps? | GAP-RRI-1..4 + GAP-XB-1 refs 付き | **PARTIAL**(GAP-EGL-1 は返すが GAP-RRI-*/XB-1 未 retrieve。**捏造ゼロ**) | True / 1.00 |
| R6 自律 RD 可? | NO、A/B/C/D 分解、no-regression | **PARTIAL**(DISABLED+A/B/C 正、**D が『未完了/保留』へ regress**) | True / 1.00 |

**全 SGQ で M1 grounding=True・src_trace=1.00・捏造ゼロ**(grounding discipline は保持)。R5/R6 の不足は下記の retrieval-completeness finding。

## 9. Duplicate-source handling(SRC-C)

SRC-C は既存 EGL 正本を検索し **reuse**、新規正本として重複登録せず(directive §1 遵守)。

## 10. 登録中に発見した問題・逸脱(独立レビュー観点)

1. **SRC-A/B UNAVAILABLE**(§1): architecture 本文が on-disk に無い。登録は directive 要約に限定。**fuller registration には SRC-A/B の on-disk 提供が要る。**
2. **DD-ARCH-2 vs 実 repo の discrepancy**(DE-0054): DD-ARCH-2 は『epistemic-ledger=EGL+RRI(同居)』だが、本 session で RRI は独立 repo `request-resolution-intent` として作成済(そのリポ genesis DE-0001)。**どちらが CURRENT かは自己裁定せず Taka/independent adjudication へ上申。**
3. **SGQ-R5 retrieval incompleteness**: OPEN GAP(GAP-RRI-*/GAP-XB-1)は `audit_backlog.jsonl` に在り、SELF_GROUNDING corpus(load_corpus=DESIGN_EVIDENCE_LEDGER+REVIEW_LEDGER)が **audit_backlog を読まない**ため retrieve できず。**捏造はしていない**(不在を返した)。→ corpus に audit_backlog を含めるか gap を DE 化するかは EGL 開発入力(retrieval_completeness NOT_VERIFIED の declared 限界が顕在化)。
4. **SGQ-R6 partial D-regression(要注意)**: live 再構成が ACQ-10 **D を『未完了/保留』へ regress**——directive が禁じた巻き戻し。原因は **DE-0039/0040 の retrieval miss**(retrieval_completeness NOT_VERIFIED)。**authoritative な D 状態は DE-0056(recorded narrow scope に implemented)であり、ledger が正、live 再構成が retrieval 不足で誤った。** grounding(M1)は保持(捏造でなく retrieval 起因)。→ EGL 開発入力(retrieval 改善 or SGQ に必須 record を固定注入)。
5. **over-claim / OBSERVATION-INFERENCE 分離 / property-level currentness / supersession precision / SoR・Failure Pattern 重複 / object-type drift**: いずれも遵守(DE-0045 重複せず、新 object type なし、JREV-0007 を一般法則へ昇格せず、supersession は proposition 限定)。
6. **ACQ-10 status**: A/B/D を一括『未充足』へ巻き戻さず、record-level・property scope で登録(DE-0056)。C の one-round を general completion へ昇格せず。

## 11. 判定

- **登録は完了**(DE-0052..0057 + 8 OPEN GAP)。grounding discipline は全 SGQ で保持。
- **未解決(自己裁定しない)**: (i) SRC-A/B の on-disk 提供 → fuller architecture 登録、(ii) DD-ARCH-2 vs RRI 独立 repo の CURRENT 裁定、(iii) DE-0047 formal packet 裁定(pending)。
- **EGL 開発入力(operational finding)**: SGQ-R5(audit_backlog が corpus 外)/ SGQ-R6(retrieval miss による D-regression)= retrieval_completeness 改善。GAP-EGL-1(M2 placement)。

これらは directive §9 の禁止に触れず、独立レビューが捕えるべき逸脱を surface した結果。
