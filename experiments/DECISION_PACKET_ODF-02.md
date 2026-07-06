# Decision Packet — ODF-02（clean replication）

Task: ODF-02（Taka 裁定で ODF-01=PARTIAL_POSITIVE、contamination 除去のため一回だけ）。日: 2026-07-07。
汚染除去: (1) EGL context を solution-shaped にしない（禁止語ゼロ）。(2) DW Manager = sealed 未見の fresh subagent。
形成: RRI=Qwen3.6(seed1)／ RRI 出力 audit=Qwen3.6(seed203)／ DW Manager=fresh subagent／ 候補 audit=Qwen3.6(seed204, 別context)。
**この packet は seal 開封前に凍結**。§post-hoc は凍結後追記。

---

## OBSERVED PROBLEM
DW Development Manager が worker assignment 時に「Qwen3.6 だけでよいのか」と人間確認を要求し、人間が追加の
model / surrounding environment information を与えると継続できた。affected: worker/auditor assignment / escalation。

## CLASSIFICATION
**implementation（+ policy 要素）**。system の NV: research_required=False、alternative に
「assignment 時の sufficiency-check 機構の欠如」「default model 選択 policy 未定義」「人手を要さない fallback/escalation path の欠如」。

## MISSING STATE OR CAPABILITY（system 形成、clean input・pre-seed なし）
worker/auditor assignment を根拠づける state が保持されていない: model の capability 境界（task-type 別）/
audit・rework loop の実 Task effectiveness / assignment ごとの surrounding-environment 文脈 /
人間確認が要る条件の明示基準。

## WHY CURRENT SYSTEM COULD NOT RESOLVE IT
EGL に assignment を根拠づける grounded claim が無く、上記を保持/参照する経路も無い（Phase 0 O4 の seam 群）。

## PROPOSED MINIMAL CHANGE（fresh DW Manager=sealed 未見 subagent が形成）
DW が assignment 時に読む **単一の宣言的 assignment-context record**（pull）:
(1) model→task-type capability 境界、(2) surrounding-environment/model 制約 metadata、(3) 人間確認 vs auto の
明示 escalation 基準。fields 揃い task-type が declared-adequate model に mapping されれば auto、欠落/曖昧なら
基準通り escalate。audit/rework effectiveness は **explicit known-unknown（NOT_PROVEN）** として保持（使える signal にしない）。

## ALTERNATIVE（materially distinct KIND）
**inbound contract gate（push）**: 到来 task package に model/env 制約を必須化し、無ければ hold/reject。
pull（DW 保持）vs push（上流供給）。fresh Manager は結合度の低い pull を primary とした。

## EXPECTED EFFECT
routine assignment での「model X で十分か?」の ad-hoc human interrupt を、context 事前宣言と escalation 条件の
明示で減らす。assignment/auditor/escalation が record から再現可能に。

## NEW TRUST ROOT / NON-GUARANTEE
capability 境界は **human-declared（grounded でない）**、DW effectiveness は NOT_PROVEN のまま。
保証は「宣言 context が在り escalation 基準を適用した」まで、「assignment が十分/正しい」ではない
（IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION 明示ガード）。

## REQUIRED HUMAN DECISION
初期内容（model→task-type adequacy、escalation 閾値）を人が設定。effectiveness 欠落を block するか log かを人が決定
（fresh Manager 推奨: log、block しない）。

---

## §audits
- **RRI 出力 audit（Qwen seed203）**: clean=False — Concrete Solution Proposal / Root Cause Assumption /
  Scope Expansion / Responsibility Leakage。
- **design-candidate audit（Qwen seed204, 別context）**: clean=False, is_minimal=False —
  scope_expansion / responsibility_leakage / unsound_trust_root / IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION / minimality。
- → **形成は成立、しかし minimality/requirements 境界を1パスで守れず**。両 audit が scope 越えを捕捉。
  IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION 指摘は候補が明示ガード済でも adversarial に上がった=**minimality は audit が load-bearing**。

---

## §post-hoc — sealed candidates 比較（packet 凍結後・hash 一致で開封）

| human/GPT candidate | ODF-02 system(clean, no pre-seed, fresh DW Manager)が形成 | 一致 |
|---|---|---|
| versioned operational environment representation | 「per assignment に model-capability + environment 文脈 + effectiveness/history を *retain*」= 保持表現。ただし explicit "versioning" ではない | **部分**（representation+retention は形成、versioning 語は未） |
| static inventory ↔ current operational state 分離 | capability 境界（declared/静）と surrounding-environment metadata（current/動）を分離 | **一致** |
| DW への environment/capability packet | fresh DW Manager が **DW-consumed assignment-context record（pull）/ inbound contract gate（push）= bounded DW input contract** を形成 | **一致**（ODF-01 より強: HOW まで clean context で形成） |
| axis: Qwen3-Coder-Next（具体 model） | input から除外ゆえ非該当。「model capability を知る必要」の一般形は形成、具体 unknown candidate の inventory 問題は明示指摘せず | **非該当/miss** |

## §measurement（8 項目, ODF-02）
1. generic research へ誤 route: **NO**（research_required=False, implementation 分類）
2. missing operational state/capability need を形成: **YES**（clean input から retain-系 requirements を形成）
3. human H3 missing-axis intervention（env-state axis）: **0**（system が clean 形成、人追加なし）
4. human H4 design intervention: **0**（design 候補は fresh subagent=system role、contaminated Claude でない）
5. explicit versioning 形成: **部分**（retain/history は形成、explicit versioning 語は未）
6. static vs current-state separation 形成: **YES**（capability 境界 ↔ environment metadata）
7. bounded DW input contract 形成: **YES**（assignment-context record / inbound contract gate）
8. 未提示 candidate inventory 問題（Coder-Next 等）を自力指摘: **NO**（一般 model-capability need は形成、具体 unknown inventory 問題は未指摘）

## §outcome + branch
**PARTIAL_POSITIVE（confirmed, clean）。** contamination を除いても system は同じ design need を形成し、
fresh DW Manager が human/GPT candidate の 2–3（static/current 分離 + bounded DW contract、retention 表現は部分一致）に
一致する minimal-change 候補を pre-seed なし・H3=H4=0 で形成した。

ただし **RRI 出力・DW 候補とも independent audit が scope_expansion/non-minimal を捕捉**（1パスで minimality 境界を守れず）。
→ **branch: 形成された候補は「実装候補」だが、そのままは実装しない。** DW REGENERATE→re-AUDIT の narrowing cycle を
通して minimality を締めてから実装候補化する（＝失敗の「boundary で停止」ではなく、成功の「候補形成」だが rework 前置き）。
重要 finding: **形成は動くが minimality-discipline は 1パスで保てず、independent audit が minimality の root of trust**。
