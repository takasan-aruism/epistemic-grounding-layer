# EGL Phase 1a 未完 再棚卸し(2026-07-05)

JREV-0004 PASS 時点。局所修正の追走を止め、**何が完成し / 何が Phase 1b 送りで / 何が Phase 1a
blocker として残るか** を再棚卸しする(Taka 指示)。原 DE-0005 欠陥リスト(H/M/L)+ JREV findings
(R1–R8/F)を disposition まで全追跡。

---

## 0. punchline

- **Phase 1a の *構造強制* 目標は達成済み**。walking skeleton が「shape は通したが enforce していない」
  (DE-0005)状態から、差別化機構(SC-2/GC-7/dedup/validation_mode/ABSENCE 分離)が**構造で強制され、
  独立敵対レビューを4周(JREV-0001..0004)耐えた**状態へ。
- **残るのは全て semantic layer = LLM が判断に入る領域**(取得/GC-6/本物 Gate4/意味的同一性)。
  ここは意図的に Phase 1b。今 Phase 1a に残る *構造* blocker は無い。
- **唯一の Phase 1a→1b 境界条件**: R4 LegIntent を **RD 自律化(LLM-agentic 化)より前**に(DE-0023)。
  取得の自律化を始める瞬間に発火する順序制約。
- **反復した設計現象**: 修正の度に信用の根が一段下へ動いた(self-report → provenance 導出 → typed path)。
  各層の *葉* は RD 供給のまま残る。これは欠陥でなく、prevention の根(署名/プロセス分離)が Phase 1b で
  あることの帰結。§5 参照。

---

## 1. ✅ COMPLETE — 構造強制 + 独立レビュー通過

| 原欠陥 / finding | 内容 | 修正 | 検証 |
|---|---|---|---|
| **H1** SC-2 self-report status | gate3 が leg event から coverage 再導出、scon.status 非参照 | DE-0010 | JREV-0003 E4(嘘 COMPLETED を上書き)= search_summary_independence **JUDGE_VERIFIED** |
| **H3** gate2/importance dead | decide が gate2 衝突(CONFLICT_REVIEW_REQUIRED)/ importance バー適用 | DE-0010 | surface_claim_key_canonicalization **JUDGE_VERIFIED**(JREV-0002) |
| **H4** GC-7 未接続 | gc7_lint を curate 連鎖へ + scope キー算入 | DE-0010 | 接続は完了(意味束縛は §3 へ) |
| **H5** counters.json 第2 SoR | 廃止、id-in-append(log=counter 単一 SoR) | DE-0006/0012 | id_event_atomicity **JUDGE_VERIFIED**(counter-factual lock) |
| **H6** 採番 lock なし | fcntl.flock で並行採番直列化 | DE-0006/0012 | counter-factual(lock無効=衝突) |
| **M1** CU-1 規律≠構造 | schema 完全性 guard(partial-update を append_event が reject) | DE-0007 | write authority は検出水準(R1) |
| **M2** RD polarity 制御分岐 | polarity を Gate0 enum 検査 + derive fail-closed | F/DE-0028 | polarity_enum_fail_closed **JUDGE_VERIFIED**(JREV-0003) |
| **M3** dangling crash | None 添字せず clean-fail(DEFER) | DE-0010 | Challenge Set C |
| **M4** shallow merge 兄弟喪失 | 全 state 変更 event は完全 revision、partial を構造 reject | DE-0007/0015 | shallow_revision_completeness **JUDGE_VERIFIED** |
| **M5** importance dead | H3 と同根で解消 | DE-0010 | — |
| **M6** ABSENCE claim_key 潰れ | claim_key を canonical scope 軸から生成 | R3/DE-0022 | scope 軸で分離 |
| **L4** validation_mode 既定 DECLARED | derive-or-UNRESOLVED。source_class → observation_kind → typed path、mode⊥polarity | DE-0008/0018/0025/0026/0029/0030 | evidence_path_derivation + mode_polarity_orthogonality **JUDGE_VERIFIED**(JREV-0004) |
| **R2** CORRECTION/COMPLETION | CR-1..4 / CP-1..3(transition legality guard) | DE-0019 | mutation_legality **JUDGE_VERIFIED**(JREV-0002) |
| **R3** claim_key gaming | canonicalize_scope(case/区切り/alias) | DE-0022 | surface 封鎖(JREV-0002/0003) |
| **R5** ABSENCE→SPECIFIED 混同 | absence_validation 別軸、ABSENCE は mode 体系外 | DE-0018 | R7 で polarity 部分を supersede、ABSENCE 分離は維持 |
| **R6** source_class 単独導出 | observation_kind gate(同一観測 PRIMARY+DECLARATION) | DE-0026 | source_class_only_hole_closure **JUDGE_VERIFIED**(JREV-0003) |
| **F** polarity fail-open | 未知/欠落/typo → Gate0 reject + derive UNRESOLVED | DE-0028 | negative_basis と併せ **JUDGE_VERIFIED** |
| **R7** mode/polarity 結合 | mode⊥polarity、negative_basis 別軸(Gate0 enum) | DE-0029 | mode_polarity_orthogonality + negative_basis_required **JUDGE_VERIFIED**(JREV-0004) |
| **R8** evidence 袋 veto | eligible typed SUPPORTS path 導出、大域 GENERATED veto 撤廃(単調) | DE-0030 | evidence_path_derivation **JUDGE_VERIFIED**(JREV-0004) |
| **恒久対策** | 全 guard(9個)が non_guarantees 宣言 | DE-0020 | T12(guard の known_omissions) |
| **RC-3/RC-4** | event log から任意時点 view を決定的再構築 | — | verify_rebuild PASS |

test: sor **41/41** / enforce 13/13 / adversarial 25/25 / RC-3・RC-4 PASS。

---

## 2. 📋 DEFERRED_ACCEPTED — 条件付き / 境界

| finding | 状態 | 条件 |
|---|---|---|
| **R4** leg_authenticity | 脆弱性確認済・現脅威モデルで未現実化 | **LegIntent を RD 自律化より前に(DE-0023)**。取得ラッパー実装時ではなく **順序制約**。injected RD が leg 捏造可能な状態で RD を自律化すると ETB(§16.2)防衛線が一枚死ぬ |
| **R1** write authority prevention | 検出水準は成立(GRANT event / audit)。**prevention は騙らない** | 署名 / プロセス分離まで(AB-0012)= Phase 1b。単一プロセスで capability forge は検出不能 |

---

## 3. ⏭️ Phase 1b — 明示的 deferral(semantic layer = LLM が入る領域)

| 項目 | 現状 | 送り先 |
|---|---|---|
| **取得境界 / retrieval / LegIntent 実装** | 未実装。証拠は手投入(demo)。「調べてで自律」は不成立 | Phase 1b(R4 順序制約付き) |
| **GC-6 後段 semantic lint**(H2/H4b statement→scope 束縛) | GC-7 は構造 scope キーのみ。自然文 statement→scope 落とし込みは RD self-report | Phase 1b |
| **本物 Gate4 adjudicator** | Claude-in-loop / driver-injected finding | Phase 1b(benchmark B / AM-13、35B 移行) |
| **意味的 claim 同一性** | surface のみ(R3)。version algebra(0.11 vs >=0.11)/ entity 同一性は未 | Phase 1b(AB-0009 / Entity Registry) |
| **MEASURED / REPRODUCED 導出** | UNRESOLVED へ倒す(Phase 1a 安全側) | Phase 1b(F3a: Activity/run type + Measurement/Reproduction link) |
| **taint-lineage** | generated が抽出に関与する taint 伝播は未表現 | Phase 1b(R8 残余、DERIVED_FROM_GENERATED) |
| **root-of-trust の葉**(observation_kind/negative_basis/source_class/polarity 値の真正性) | 全て RD 供給の leaf self-report。enum/存在は検査、値の真正性は未 | Phase 1b(署名/プロセス分離) |
| **L1** GC-8 過剰ブロック / **L2** scale O(N·M) / **L3** RC-4 test 強化 / **L5** ts 境界 | 低優先 | Phase 1b / backlog |
| **BA-NEG-001** negative_basis 二重防御 / **BA-REL-001** gate1 relation_type | trust boundary 内、contracts 宣言済 | apply_outcome が code-trust でなくなる / Gate1 意味責任拡張時に再訪 |

---

## 4. ⚠️ Phase 1a に残る *構造* blocker

**無し(構造層)。** DE-0005 が挙げた「コードが正しい値を計算して捨てる/誤 source を読む」型の構造欠陥は
H1/H3/H4/M3/M4 で全て enforce 済み。以降の JREV は semantic contract(R5–R8)の精緻化で、いずれも閉鎖。

残るのは **境界判断1件**(§6)。

---

## 5. 反復した設計現象:信用の根が一段ずつ下りた

各修正が信用の根を一段下へ動かした。これは欠陥でなく、prevention の根が Phase 1b(署名/プロセス分離)で
あることの構造的帰結——**各層で『葉は RD 供給』を非保証として正直に宣言する**のが Phase 1a の規律。

```
validation_mode:
  自己申告 mode(既定 DECLARED)         [L4 撤廃]
    → provenance 導出(source_class)     [R5/R6]
    → observation_kind の同一観測 gate    [R6]
    → eligible typed SUPPORTS path        [R8]   ← 設計『Evidence Relation first-class』に実装が追いついた
    → (葉)observation_kind/source_class の値の真正性 = RD 供給  [Phase 1b: 署名]

write authority:
  physical sole-writer → GRANT event 検出 → issuer 検査(self-grant) [R1/DE-0024]
    → (葉)issuer 欄の真正性 = self-report  [Phase 1b: 署名/プロセス分離]

polarity:
  制御分岐 fail-open → Gate0 enum + derive fail-closed [F]
    → (葉)正規 enum 値の意味的真正性 = RD 供給  [Phase 1b]
```

この「根が下りる」構造を毎回 non_guarantee に宣言してきたのが、guard の known_omissions(DE-0020)。

---

## 6. Taka 判断が要る:Phase 1a / 1b の境界線

構造層は完成した。**残る semantic layer(取得 / GC-6 / 本物 Gate4)を Phase 1a の *完成条件* とするか、
Phase 1b の *開始* とするか** が唯一の未決定。

- **案A: 構造 Phase 1a を「完了」と宣言** — semantic layer は Phase 1b。walking skeleton の当初目標
  (shape 貫通 + 差別化機構の enforce + 独立レビュー耐性)は満たした、という立場。以降は LLM が判断に入る
  新フェーズとして仕切り直す。
- **案B: semantic layer を Phase 1a の残タスクとする** — 取得/GC-6/Gate4 本物化まで含めて Phase 1a。
  memory の旧評価「Phase 1a 75–85%、残20%=semantic layer」を踏襲。

どちらでも **次の実作業は同じ**(取得境界 or GC-6 or Gate4 のいずれか)だが、R4 順序制約(LegIntent を
RD 自律化前)がどちらの案でも効くことだけは確定。

台帳: REVIEW_LEDGER JREV-0001..0004 / DESIGN_EVIDENCE_LEDGER DE-0001..0030 / audit_backlog AB-0001..0015 /
egl/contracts.py(9 guards)。
