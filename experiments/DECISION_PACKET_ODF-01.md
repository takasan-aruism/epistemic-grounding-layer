# Decision Packet — ODF-01

Task: Operational Design-Formation Experiment（frozen input のみ）。実験日: 2026-07-07。
形成: RRI Research Intent = Qwen3.6（uncontaminated）。翻訳: DW Manager = Claude（⚠ sealed 既見=contaminated）。
audit: Qwen3.6 別 run。**この packet は seal 開封前に凍結**（下記 §post-hoc は凍結後に追記）。

---

## OBSERVED PROBLEM
DW Development Manager が利用可能な model / worker 選択を確信できず、Qwen3.6 だけで十分かを確認する必要が生じ、
人間が周辺の environment / model 情報を手で補った。

## CLASSIFICATION
**implementation（+ policy 要素）** — 「良い model を research する」knowledge 問題**ではない**。
system の Need Validation が `research_required=False` と判定し、alternative causes に
「availability 状態を出す automation 機構の欠如」「model registry と assignment の非統合」
「複数候補時の default model 選択 policy 未定義」を挙げた（= mixed: implementation 主 + policy）。

## MISSING STATE OR CAPABILITY（system 形成、pre-seed なし）
現在どの model/worker が available/serving か・各々の **role-validation 状態**・resource(GPU) residency・
過去の effectiveness を表す **state が保持されていない**。DW はこれを人手依存で補っている。

## WHY CURRENT SYSTEM COULD NOT RESOLVE IT
Phase 0（O4）の通り、現状 system は observed event を内部 finding にする intake すら持たない
（ODF-STOP-01: DW に operational-finding intake / RESEARCH_NEED emitter が無い）。RRI Research Intent も
本実験のため最小 slice を新設して初めて形成に入れた。**運用能力(model/worker availability + validation)を
保持する object が EGL/DW に存在しない。**

## PROPOSED MINIMAL CHANGE（DW Manager, ⚠contaminated, audit で narrow 済）
DW が worker/auditor assignment 時に参照する **bounded な「現在 available/serving な model と、その
role-validation 状態」の記録**。⚠ independent audit が RRI 出力に scope_expansion / responsibility_leakage を
検出したため、**automated mapping / audit-coverage metrics / full inventory 等は除外し、
assignment 決定に load-bearing な最小(availability + role-validation state)に絞る**。
health monitoring（Watcher）や汎用 env DB は含めない。

## ALTERNATIVE（materially distinct）
**policy-only 変更**: availability が実は既知で、単に「複数候補時の default worker 選択 policy」が
未定義なだけなら、state 保持機構でなく policy 明文化で足りる可能性。system の NV がこの alternative を surface した。
どちらが root かは §required decision。

## EXPECTED EFFECT
DW が assignment/escalation を、人手供給の environment/model 情報に依存せず decide できる方向。
（effectiveness は NOT_PROVEN のまま。）

## NEW TRUST ROOT / NON-GUARANTEE
- availability/validation 記録は **representation**（stale/誤り得る）。**role-validation は実 Task 結果からのみ**
  （model exists ≠ role validated を継承）。health monitor ではない。
- 形成は single-Qwen3.6・1 event・1 run。DW Manager 翻訳は contaminated（Claude が seal 既見）。
- RRI 出力は audit で scope_expansion/responsibility_leakage 指摘あり=requirements 境界を一部越えた。

## REQUIRED HUMAN DECISION
1. root は missing-mechanism（implementation）か missing-policy か（= minimal change の種類）。
2. 記録の trust 境界 / staleness 方針。
3. 実装するなら Coder-Next serve 後に **DW dogfooding** で build するか。

---

## §post-hoc — sealed human candidates との比較（packet 凍結後・seal 開封、hash 一致で intact）

seal 内容: (1) versioned operational environment representation / (2) static inventory vs current operational
state separation / (3) DW への environment・capability packet / (axis) Qwen3-Coder-Next。

| human/GPT candidate | system(Qwen RRI, pre-seed なし)が形成したもの | 一致 |
|---|---|---|
| versioned operational environment representation | 「available models + serving endpoints の inventory」+「historical effectiveness を retain」 | **一致** |
| static inventory vs current operational state 分離 | 「available models(静的)」と「current role-validation 状態 / GPU residency(動的)」を分離 | **一致** |
| DW への environment/capability packet | 「assignment 決定が X を *知る* 必要」まで形成（packet=HOW は RRI が prescribe せず=正しい責任境界） | **部分**(need は形成、HOW は DW Manager 側) |
| axis: Qwen3-Coder-Next（具体 model） | 「available models を知る必要」の一般形は形成したが、**具体 model 名は surface できず** | **不一致**（人が供給=H3） |

**注目**: system は「利用可能 model を知らない」ことを自ら missing-state と特定した。その同じ理由で
具体 model（Coder-Next）を名指せない=自己整合的。inventory が無いから inventory の中身を言えない。

## §measurement

- 正しい責任層へ route: **YES**（implementation/policy、research でない）。
- research 不要を research へ送らない: **YES**（research_required=False）。
- missing knowledge/state を特定: **YES**（強く）。
- **人が先に与えていない design need を形成: YES**（env-state 表現の axis を pre-seed なしで、human candidate 2/3 に一致）。
- scope 膨張なく minimal: **NO** — independent audit が scope_expansion / responsibility_leakage を検出、DW Manager が narrow。
- **H2(routing)=0**（system 自力で route）。
- **H3(missing-axis)**: env-state 表現 axis=**0**（system 形成）／ 具体 model(Coder-Next) axis=**1**（before-state, 人供給, DW DE-0004）。
- **H4(design)**: minimal change は DW Manager(Claude, ⚠contaminated) が narrow=system role action（clean な「system 形成」でも clean な「人追加」でもない、汚染付き）。

## §outcome（§F）
**O1-leaning（strong positive）with caught scope-drift + before-state H3=1。**
中心質問「4-system loop 自身が中間設計 need を発生させられるか」への narrow な回答:
**この event では YES**——system は問題だけから、human/GPT が独立に出した structural design need（env-state 表現 +
静的/動的 分離）を pre-seed なしで形成した。ただし (a) requirements 境界を越え（audit が捕捉）、(b) 具体 model
axis は人依存（H3=1）。single event / single run / single model / DW-Manager 翻訳は contaminated。一般化しない。
