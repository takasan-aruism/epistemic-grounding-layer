# Plan — Operational Design-Formation Experiment

状態: **AWAITING_INDEPENDENT_REVIEW**（実装・設計変更は本 plan の独立 review 後）。
発行: EGL Claude Code。宛先: 独立 review（GPT / Taka）。

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
