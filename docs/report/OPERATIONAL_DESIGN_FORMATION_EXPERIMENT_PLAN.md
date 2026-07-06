# Plan — Operational Design-Formation Experiment

状態: **REVIEWED — PASS_WITH_THREE_AMENDMENTS（2026-07-07）**。Phase 0 は Amendment A 適用で承認、
Phase 1 は Amendment B 適用で承認（DW dogfooding で build）。amendments を §A/§B/§C に記録。
発行: EGL Claude Code。review: GPT。

## 中心質問

現在 Taka / GPT / Claude が手で行っている「それ、そもそもこの情報を保持する仕組みが要るのでは?」という
**中間設計作業を、4-system loop 自身が観測事象だけから発生させられるか**を測る。

---

## 1. 凍結入力（これだけを system に与える。解決案は混入させない）

```
ORIGIN:            DW
OBSERVED EVENT:    Development Manager が利用可能な model / worker 選択を確信できず、
                   Qwen3.6 だけで十分かを確認する必要が生じた。
DECISION AFFECTED: worker assignment / auditor assignment / escalation
KNOWN IMPACT:      human が周辺の environment / model 情報を手動で補った。
```

### 🚫 実験前に system へ pre-seed 禁止（隔離。post-hoc 比較でのみ開封）
Operational Environment Registry / Environment Packet / static inventory ↔ current operational state 分離 /
HOST・GPU_RESOURCE・MODEL_DEPLOYMENT 等の object 案 / Watcher health monitoring。
— これらは human/GPT が既に考えた candidate。実験の input・prompt・schema・rule に一切入れない。

---

## 2. 正直な出発点（現状の reach）

中間設計を担う **RRI Research Intent 層（§19-29: Need Validation / Research Design / RDEC / Approved RQ Set）は
未実装**（GAP-XB-2）。EGL→DW KNOWLEDGE_PACKET emitter も bridge（GAP-XB-3）。
よって凍結入力を現状の system に流すと、形成に入る前に seam で止まる見込み。これを**手で自然言語補完して
成功にしない**（constraint #3）。止まった箇所は structured GAP として記録する（constraint #4）。

→ 実験は2段構成にする。

---

## 3. 手順

### Phase 0 — reach test（新規 code なし・観測のみ）
凍結入力を現状の DW→RRI→EGL 経路に通し、**どこで止まるか**だけを記録:
- 止まった system responsibility
- 欠けている object / contract / transition
- なぜ次へ進めないか

出力 = structured GAP のリスト（baseline）。ここで実験を止めても正当な結果（現状 reach の測定）。

### Phase 1 — minimal formation machinery（review 後にのみ実装）
Phase 0 が「設計 need 形成」まで到達しない場合、それを可能にする **最小の RRI Research Intent slice** を、
**解決案を pre-seed せずに**構築し、凍結入力だけを流して形成能力を測る:

1. **Blockage classification**: OPERATIONAL FINDING を `knowledge / implementation / policy / mixed` に分類。
2. **Need Validation（§19-20 NV1-6）**: `missing_knowledge_hint を root cause と信じない`。
   research が本当に要るか、単に adapter 未実装 / policy 未定義 の bottleneck でないかを判定。
3. **Research Design（最小）**: decision（worker/auditor assignment）から、進めるのに *何を知る必要があるか* の
   axis を、EGL の current knowledge / gaps / past failures を参照して形成。**解決 object を先に決めない。**
4. **不足構造の特定 → minimal design-change candidate**（scope 膨張なし。1案しか合理的でなければ1案）。
5. **Independent design audit**: 別 identity が scope expansion / faked path / missing_knowledge_hint-as-root /
   pre-seed leakage を攻撃。
6. **Decision packet を Taka へ**（§5 の形式）。

**形成を担うのは誰か（review 対象の要判断）**: 中間設計形成は判断タスク。**local model（Qwen3.6）を
RRI Research Intent worker として使い**、Claude は orchestrator + independent design auditor に徹する
（形成そのものを Claude がやると「Claude が中間設計した」になり中心質問を測れない）。
Claude が形成に介入した step 数は human-intervention metric として計上する。

---

## 4. Taka へ返す decision packet（長い設計書でなく、この形式）

```
OBSERVED PROBLEM
CLASSIFICATION            knowledge / implementation / policy / mixed
MISSING STATE OR CAPABILITY
WHY CURRENT SYSTEM COULD NOT RESOLVE IT
PROPOSED MINIMAL CHANGE
ALTERNATIVE               materially distinct な場合のみ
EXPECTED EFFECT
NEW TRUST ROOT / NON-GUARANTEE
REQUIRED HUMAN DECISION
```

---

## 5. 測定（gold answer 判定ではない）

- 問題を正しい責任層へ route できたか。
- research 不要な問題を research へ送らなかったか（Need Validation の効き）。
- missing knowledge / state を特定できたか。
- **人間が先に与えていない design need を形成できたか**（中心）。
- scope 膨張なく minimal change を提案できたか。
- Taka が追加した essential design axis 数。
- human intervention step 数（Claude の形成介入含む）。

複数案生成は quality metric に**しない**（constraint #6）。

---

## 6. Post-hoc 比較（実験後にのみ開封）

system proposal と、隔離した human/GPT candidate（versioned operational environment representation /
static inventory ↔ current operational state 分離 / DW への environment・capability packet）の
**一致 / 不一致**を測る。gold 判定でなく、system が独立に同じ / 異なる design need に到達したかの観測。

---

## 7. 実験を無効化する事象（事前明示）

- 凍結入力・prompt・schema・rule への pre-seed leakage。
- 未実装経路の自然言語補完（fake success）。
- missing_knowledge_hint を root cause として採用。
- 形成 machinery 自身の scope 膨張（env DB を最初から前提化）。
- Claude が形成の実質を代行（→ human-intervention が高騰し、中心質問は「未達」と記録）。

---

## 8. review で決めてほしいこと

1. Phase 0（観測のみ）を先に走らせてよいか（新規 code なし）。
2. Phase 1 の minimal RRI Research Intent slice を **build してよいか**、その contract
   （blockage 分類 enum / Need Validation checks / design-candidate schema）は解決案 pre-seed なしで妥当か。
3. 形成 worker = Qwen3.6・Claude = orchestrator+auditor の役割分担でよいか。
4. Phase 1 の build 自体を DW loop（dogfooding）で回すか、通常実装か。

承認まで実装・設計変更は行わない。

---

# AMENDMENTS（independent review 2026-07-07, PASS_WITH_THREE_AMENDMENTS）

## §A — Phase 0 は true reach test（narrated walk-through にしない）
Phase 0 は **現在実装済みの sanctioned interface のみ** を呼ぶ。実験継続のためだけに RESEARCH_NEED 後継 object /
Research Design object / Approved RQ Set / Knowledge Packet を **手で捏造しない**。実装済み interface が無ければ
その seam で止める。各 stop の記録形式:
```
STOP_ID / LAST_REAL_OBJECT / NEXT_REQUIRED_OBJECT / RESPONSIBLE_SYSTEM /
MISSING_INTERFACE_OR_TRANSITION / WHY_CONTINUATION_IS_UNSANCTIONED
```

## §B — Phase 1 は「Research Design」と「Design-Change Formation」を分離（最重要）
責任境界を明示。**RRI は what must be known、DW は what change to execute。**
```
RRI Research Intent worker  → BLOCKAGE CLASSIFICATION / NEED VALIDATION /
                              RESEARCH-DECISION AXES / MISSING STATE OR CAPABILITY /
                              RESOLUTION_REQUIREMENTS   ← RRI の最終 output はこれ（提案でない）
EGL                         → CURRENT KNOWLEDGE / OPEN GAPS / FAILURE PATTERNS / NON-GUARANTEES
DW Development Manager       → MINIMAL DESIGN-CHANGE CANDIDATE（grounded requirements を翻訳）
Independent Design Auditor   → attack scope / trust root / responsibility leakage
```
RRI worker(Qwen3.6)が env registry を直接提案してはならない。それは「local model が design を発明できる」の
測定にすぎず、「4-system loop が責任境界を通して design need を形成できる」を測れない。

## §C — Human intervention taxonomy（H0–H5）
```
H0 mechanical execution（command/handoff/run）      — design 介入に数えない
H1 format repair（schema/syntax、意味なし）          — 別集計
H2 routing（どの system が問題を持つか人が特定）
H3 missing-axis（essential な knowledge/state/capability axis を人が追加）
H4 design（人が minimal change / architecture を供給）
H5 adjudication（形成済み candidate から人が選ぶ）
```
Primary: **DESIGN_FORMATION_INTERVENTION = H2 + H3 + H4**。Secondary: TOTAL_SEMANTIC = H2+H3+H4+H5。
成功信号: **H3 = 0 かつ H4 = 0**（または human/GPT baseline より有意に低い）。

## §D — Role / model 分担（review §6 + Taka finding）
```
PLAN        → Claude Code(Development Manager) — design action は system role action として記録（隠れ orchestration にしない）
GENERATE    → Qwen3-Coder-Next（Coding Worker candidate）
AUDIT       → Qwen3.6（別 run/context）
REGENERATE  → Qwen3-Coder-Next
UPPER REVIEW→ Claude Code
Research Intent 形成 → Qwen3.6（Claude は形成 output を audit 前に書き換えない）
```
**model exists ≠ role validated**: Qwen3-Coder-Next は candidate、role validation は実 DW Task 結果から測る。
Manager と Auditor が同一 Claude の場合、run/context 分離を必須とし shared-weights 限界を記録。

## §E — Pre-seed leakage control（sealed artifact）
`experiments/HUMAN_CANDIDATE_SEALED.json`（sha256=`e7b289b3628f07eb0dc1b150fc174a591adbc5ef01c11be23c2957188ba37a04`）を
**Phase 0 前に封緘**。model context / prompt / retrieval corpus に入れない。system Decision Packet 凍結後にのみ開封。
⚠ 汚染: Claude(orchestrator)は会話中に candidate を既見。緩和=形成は Qwen、Claude の形成介入は H として計上。

## §F — Outcome 解釈（review §9）
```
O1 strong positive : missing operational state 特定 → resolution requirements 形成 → DW が bounded な
                     persistent/current capability 表現を独立提案 → 人が essential axis を足さない
O2 partial positive: missing state/capability は正しく特定、だが人が load-bearing axis を追加
O3 routing/formation failure: 汎用 web/model research へ送る、または「Qwen3.6 で十分か」を root question に据える
O4 architecture seam failure : 必要な object/transition が無く need を形成できない
```
**O4 は Phase 0 では実験失敗でない=reach baseline**。Phase 1 slice を正当化し得る。

## §G — Phase 1 を DW dogfooding で build（review §7, APPROVE）
Task Unit 分割（general autonomous design engine は作らない）:
```
TASK-ODF-01 Blockage classification contract
TASK-ODF-02 Need Validation narrow slice
TASK-ODF-03 Resolution Requirements / Research Axis output contract
TASK-ODF-04 EGL context intake for design formation
TASK-ODF-05 DW minimal design-candidate formation contract
TASK-ODF-06 Independent Design Audit finding contract
TASK-ODF-07 Decision Packet renderer
TASK-ODF-08 Frozen-input operational experiment
```

---

# PHASE 0 RESULT — reach test（§A 準拠, 2026-07-07, code なし・interface 監査）

凍結入力を現状 system の sanctioned interface のみで進めた。**最初の seam で停止**:

```
STOP_ID:                    ODF-STOP-01
LAST_REAL_OBJECT:           external OPERATIONAL EVENT（内部 object 化されていない）
NEXT_REQUIRED_OBJECT:       OPERATIONAL_FINDING → BLOCKAGE_CLASSIFICATION → RESEARCH_NEED（DW spec §7.17）
RESPONSIBLE_SYSTEM:         DW（operational-finding intake + RESEARCH_NEED 発行）
MISSING_INTERFACE:          DW workcell は TASK(goal+knowledge_packet)しか受けない。operational-finding intake も
                            RESEARCH_NEED emitter も未実装。
WHY_UNSANCTIONED:           継続には RESEARCH_NEED/OPERATIONAL_FINDING を手で捏造する必要=§A で禁止（narration）。
```
仮に ODF-STOP-01 を越えても次の seam で停止（**ODF-STOP-02**: RRI Need Validation / Research Design=§19-29 未実装、
GAP-XB-2）、さらに **ODF-STOP-03**: EGL KNOWLEDGE_PACKET emitter 未実装（GAP-XB-3）。

**判定: O4（architecture seam failure）= reach baseline。** 現状 system は observed event を内部 finding に
する intake すら持たず、design need 形成に入れない。→ **Phase 1 の minimal machinery（§G）が正当化される。**
これは実験失敗でなく「現在 human が中間設計をやる理由」の構造的裏取り。手で補完して成功にはしていない。
