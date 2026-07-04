# EGL Component Decomposition (Kickoff (a))

根拠は設計文書ではなく **実装コード + Run Ledger 実測**(MOR-1)。
2滴の operational stream(Drop1 EVIDENCE_INSUFFICIENT / Drop2 ABSENCE 正・負)から逆算。
本書は「次に何を component として立てるか」の地図。実 reorg は build-out として別途(review 後)。

---

## Components(コードの実サーフェスから)

### C1. Ledger (SoR) — `egl/core.py` 【P1-CORE】
append-only event log(正本)+ rebuildable SQLite view + Run Ledger + IDs。
- 契約: `append_event(run,evt,otype,oid,payload)` / `read_events(until_ts)` / `build_view(until_ts)`・`get`・`by_type` / `run_start`・`run_end` / `new_id`
- 不変条件: **RC-3**(view は events から決定的再構築, verify_rebuild PASS)/ **RC-4**(until_ts で time-travel)/ **OM-2**(全 write に run_id)
- 依存: なし(stdlib のみ)= 最下層
- build-out: 増分/キャッシュ projection(現状 `build_view` は全 events 再構築、`curate` が候補ごとに2-3回呼ぶ = O(events)/gate-run)。`claim_key`/`ESTABLISHED_AXES` は C2 へ移送

### C2. Ontology / Axis — 現状 `core.claim_key`+`ESTABLISHED_AXES`+ 暗黙 dict schema 【P1-CORE schema / P2+ 昇格】
object schema・claim_key 導出(AX-2 ESTABLISHED 軸のみ)・Axis Registry。
- 現状: object は**型なし dict**、schema 検査は `gate0` の REQUIRED キー列のみ
- build-out: 明示 schema 化 + Axis Registry(PROVISIONAL/ESTABLISHED, AX-1..6)独立化

### C3. Producer (RD write API) — `egl/pipeline.py` mk_* 【P1-CORE】
object を event として materialize する RD 側 write 面。
- 契約: `mk_source` / `mk_observation`(Raw+Norm)/ `mk_fragment` / `mk_relation` / `mk_gap` / `mk_search_plan` / `mk_search_leg` / `mk_search_conclusion`。全て run_id を刻む
- ⚠️ **candidate 生成だけ driver が `append_event` 直呼び=バイパス**(seam 6)。要 `mk_candidate`
- 依存: C1

### C4. Search / Coverage — `gates.evaluate_coverage`+`COVERAGE_PROFILES`+`pipeline.mk_search_leg/conclusion` 【P1-CORE】
coverage profile(CP-1)・leg 実行・COMPLETED/SEARCH_INCOMPLETE 判定(SC-1)・**ABSENCE 可否ゲート(SC-2)**。
- ⚠️ 現状 gates.py と pipeline.py に**分散(tangle)**(seam 4)→ `search.py` へ抽出候補
- 依存: C1

### C5. Curator / Admission Control — `gates`(0-3,decide,gc7)+`curator.curate`+`pipeline.apply_outcome`+`judge` 【P1-CORE】
5 sub-seam に分かれる:
- **5a Static Gates[code]**: `gate0_schema` `gate1_evidence` `gate2_candidates` `gate3_authority` — view に対し **read-only**
- **5b Adjudicator[SWAP SEAM]**: `judge.build_packet` → `Adjudicator.adjudicate(packet,run)` → `Finding`。**Claude→35B の唯一の差し替え点(AM-13)**。入力=bounded context packet(EI-3)、出力=Finding(ENTAILMENT+SCOPE family + fragment_sufficient + common_run_id)
- **5c Decision Table[pure]**: `gates.decide(finding,gate2,importance)` → (outcome,reason)。DT-1 version 刻印
- **5d Applier[SOLE WRITER]**: `pipeline.apply_outcome` — **Global Claim を書く唯一の関数**。CU-1 を構造で強制
- **5e Orchestration**: `curator.curate` — 5a-d を配線。ABSENCE は 5b をスキップし SC-2 で成立
- 依存: C1,C2,C3,C4

### C6. Contracts / Lints — GC(gate1 内)+`gc7_lint` 【P1-CORE】
GC-1/4/8(`gate1_evidence`)・GC-7(`gc7_lint`)= 機械検証可能な grounding 契約。
- build-out: `contracts.py` へ集約、GC-2/3/5 追加

### C7. Role Harness / Drivers — `run.py`/`run2.py`+`judge.ClaudeAdjudicator` 【Phase1 で実 agent に置換】
RD role(gap 分解・observation・candidate 生成)+ Manager(importance = required_for 由来, K3)+ Adjudicator 注入(Claude-in-loop)。
- build-out: RD=agent、Manager=task 分類コード、Adjudicator=Claude/人間 endpoint →(benchmark B 後)35B

---

## 依存グラフ(実測・層状)
```
   Drivers(run/run2) ──inject──▶ Adjudicator(judge)   [SWAP: Claude→35B]
        │                              ▲
        ▼                              │
   Curator.curate ───────────────────┘
     ├─ Static Gates (gates 0-3)      [read-only]
     ├─ Decision Table (gates.decide) [pure]
     ├─ Applier (apply_outcome)       [SOLE WRITER, CU-1]
     └─ Search/Coverage (SC-2)
        │
   Producer (pipeline mk_*) ── Ontology (claim_key/axes)
        │                          │
        └────────── Ledger (core) ─┘        [SoR; RC-3/RC-4]
```

## コードが露呈した seam(= build-out の順序)
| # | seam | 根拠 | 種別 |
|---|---|---|---|
| 1 | **Adjudicator swap** | judge が isolate 済み。packet in / Finding out | 最重要・維持 |
| 2 | **Sole-writer**(apply_outcome のみ Claim を書く) | gates は read-only, write は1関数 | CU-1 死守 |
| 3 | **View/write 非対称**(read=build_view, write=append_event) | 全 module がこの型 | ETB-7 の物理根拠 |
| 4 | Search/Coverage tangle | gates と pipeline に分散 | refactor(`search.py`) |
| 5 | Ontology 誤配置 | claim_key/axes が core | refactor(Axis component) |
| 6 | Candidate write バイパス | driver が append_event 直呼び | refactor(`mk_candidate`) |
| 7 | **Activity 語彙の混同** | Run Ledger 実測: `CURATION` が rd-gap登録 と curator-審査 の両方 | RL-1 語彙(→ audit_backlog) |

## Phase-1 build-out(seam 順・review 後に着手)
1. seam 6 `mk_candidate`(write surface 統一)+ seam 4 `search.py` 抽出 = 機械的・behavior-preserving。tests(run/run2/verify)緑を維持
2. C2 明示 schema + Axis Registry(seam 5)= claim_key を C1 から剥がす
3. C5 の Adjudicator を Protocol 化(seam 1 を型で固定)→ benchmark B / 35B 差し替えの受け口
4. C6 `contracts.py` 集約 + GC-2/3/5
5. C1 増分 projection(build_view O(events) 解消)= 量が出てから(MOR: operational 根拠待ち)

## 意図的に立てない component(P2+ / MOR 待ち)
Entity Registry / Relation 8種フル / family分割 run(FI-4)/ second extraction(EI-4)/
benchmark B & 35B 移行(AM-13)/ validation_mode コード導出(AM-15)/ bootstrap partition(BP)/ vector index。
いずれも operational stream が必要性を示してから(MOR-1)。
