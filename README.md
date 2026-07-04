# Epistemic Grounding Layer — Phase 1a Walking Skeleton

有効文書: 親 v0.1 + unified v0.2 + Amendment v0.2.1 + v0.2.2 + Kickoff Decision Record。
本コードは Kickoff (b) walking skeleton の骨組み。実 RQ を1本、最小構成で貫通する。

## 走らせ方
```
python3 run.py             # Drop 1: EVIDENCE_INSUFFICIENT 経路(stream をリセット)
python3 run2.py            # Drop 2: ABSENCE 経路 正/負(Drop 1 に append)
python3 verify_rebuild.py  # RC-3(再構築一致)/ RC-4(time-travel)受入試験
```

## 通した2つの型(walking skeleton の定石: 型の違う2本)
**Drop 1 — EVIDENCE_INSUFFICIENT(断片が claim に足りない不足の型)**
RQ:「NVFP4 は dual RTX5090 の持続 agent 負荷で安定か」
- C1(sm120で動く)→ Gate4(Claude)→ **ACCEPT**(残差 operational_stability)
- C2(持続負荷で安定)→ 証拠が語らない → **EVIDENCE_INSUFFICIENT**(EI-6)→ gap 差し戻し
- **DF-4**: required gap OPEN → ACTIONABLE(SOLVED 封鎖)/ **GC-7**: 「stable」への飛躍を遮断

**Drop 2 — ABSENCE(調査完遂したが世界に無い不在の型。NOT_FOUND ≠ DOES_NOT_EXIST)**
RQ:「TRT-LLM は SM120 向け NVFP4 を公式明記しているか」
- **正**: 必須3ソース全 check → COMPLETED → **ABSENCE 生成**(NOT_FOUND / AB-2 statement に coverage 参照 / AB-3 14日短TTL)
- **負**(通らない試験): repo leg timeout 模擬 → SEARCH_INCOMPLETE → **ABSENCE を SC-2 が構造ブロック**(偽の不在は作れない)

## 設計対応(実装済みの規則)
| module | 実装 |
|---|---|
| `egl/core.py` | append-only event log(正本)/ SQLite view(RC-3 再構築可)/ time-travel(RC-4)/ Run Ledger(OM-2)/ ESTABLISHED軸 claim_key(AX-2) |
| `egl/judge.py` | Gate4 = Claude-in-loop(K-2, CB-5)/ bounded context packet(EI-3)/ finding enum(AM-11 UNJUDGEABLE)/ ENTAILMENT+SCOPE 2family(FI-3)/ common_run_id(FI-5)/ FRAGMENT_INSUFFICIENT(EI-6) |
| `egl/gates.py` | Gate0-3[code] / GC-1,GC-4,GC-8(taint)/ dedup全走査(CS-1)/ SC-2(ABSENCE)/ Decision Table(SN-4 自動縮小せず差し戻し)/ GC-7 lint |
| `egl/pipeline.py` | Gap/Search/Obs/Fragment/Candidate/Relation 構成子(全 run_id 刻印)/ Gate5 apply(CU-1 codeのみwrite)/ EVIDENCE_INSUFFICIENT→gap再OPEN(G4-7) |

## 意図的に未実装(1b 以降 / MOR で運用証拠待ち)
Entity Registry / Relation 8種フル / Axis 昇格 / family分割run(FI-4)/ second extraction(EI-4)/
benchmark B & 35B移行(AM-13)/ validation_mode コード導出(AM-15)/ bootstrap partition(BP)本格 /
vector index。**これらは operational stream が必要性を示してから(MOR-1)。**

## SoR
`data/events.jsonl` = 正本(append-only)。`data/state.sqlite` = 導出 view(いつでも捨てて再構築可)。
`DESIGN_EVIDENCE_LEDGER.jsonl` = 設計変更の証拠台帳(DE-0001..0004 seed 済み, AM-19)。
