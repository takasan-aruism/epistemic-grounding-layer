EGL Request Resolution & Research Intent Specification v0.2
対象: Epistemic Grounding Layer (EGL)
文書種別: Architecture / Implementation Specification
状態: PROPOSED — implementation review ready
置換対象: EGL_RESEARCH_INTENT_LAYER_SPEC_v0.1.md
主目的: 人間または外部systemから来る問いを、意図の揺れ・前提不安定性・文脈接続を評価した上で解釈し、その解釈から必要な調査を設計・監査し、説明可能な変換系列としてEGL Researchへ渡す。

0. Core Thesis
EGLが正しい証拠を集めても、入口で問いの意図を誤れば、完全に間違った仕事を高精度で実行する。

text
wrong intent
↓
excellent research design
↓
excellent acquisition
↓
excellent evidence
↓
excellent answer
これはEGLにおける最大級のwaste failureである。

したがってResearchの開始点は、

何を検索するか

ではない。

まず、

この問いを何として扱うべきか。
その解釈はどの程度安定しているか。
問いに含まれる暗黙前提は成立しているか。

を解く。

その後、

そのGoal / Decisionを進めるには何を知る必要があるか。

をResearch Designする。

EGL v0.2では以下の三段を明示的に分離する。

text
Request Resolution Layer
WHAT DO WE THINK THE REQUEST MEANS?

Research Intent Layer
WHY DO WE THINK THESE QUESTIONS MUST BE ANSWERED?

EGL Research
WHY DO WE THINK THESE CLAIMS ARE SUPPORTED?
全層の共通原則:

Every meaningful transformation must be explainable.

1. Explainability Constitution Adaptation
本仕様はESDE Explainability Constitutionの以下の原則をEGLへ移植する。

ESDE側のExplainability operational concept:

short description, stable over time, with reproducible structure

また、設計変更は以下で正当化される。

text
Observation
↓
Bottleneck
↓
Minimal Change
↓
Re-observation
EGLではこれを「変換の説明可能性」へ適用する。

対象変換:

text
Raw Request
→ Resolved Intent

Resolved Intent
→ Research Axes

Research Axes
→ RQ Set

Search Result
→ Observation

Observation
→ Evidence Fragment

Evidence
→ Claim

Claim Set
→ Knowledge Packet

Knowledge Packet
→ DW Task Plan
各矢印でscope expansion、premise drift、narrative substitutionが起こり得る。

したがって各重要変換は最低限、

text
INPUT
OUTPUT
BASIS
RETAINED UNCERTAINTY
ALTERNATIVES OR EXCLUDED SCOPE
REVISION TRIGGER
を短いstructured recordで説明可能でなければならない。

長いchain-of-thoughtの保存は要求しない。

要求するのは、

後続actorが短い記述とreferenceから、なぜその変換が行われたかを再構成できること。

2. Anti-Drift Rule for EGL Metadata
ESDE Explainability Constitutionでは、Claimは以下の少なくとも一つを満たす必要がある。

experiment designを変える
observable metric shiftを予測する
ambiguityを減らすmeasurementを与える
EGLではこの原則をmetadata / assessment fieldsにも適用する。

新しいfield、score、classificationは少なくとも以下の一つを変えなければならない。

text
interpretation strategy
clarification behavior
research scope
required / optional RQ assignment
search behavior
safe unknown behavior
answer rendering
revision trigger
workflow state
例:

text
intent_fluctuation_score = 0.73
がworkflowを一切変えないなら、これはnoise-metricである。

初期実装では抽象的なsingle scalar intent_fluctuation_score を必須にしない。

まずdecision-relevant categorical axesを使用する。

3. Top-Level Architecture
text
                    HUMAN RAW REQUEST
                            │
                            ▼
                 REQUEST RESOLUTION LAYER
                 ├─ Context Binding
                 ├─ Intent Fluctuation Assessment
                 ├─ Premise Assessment
                 ├─ Interpretation Strategy
                 ├─ Optional Intent Probe
                 └─ Explainable Resolution
                            │
                            ▼
                    RESEARCH_REQUEST
                            │
                            │
                            ├──────────────────────┐
                            │                      │
                            ▼                      │
                    RESEARCH INTENT LAYER          │
                    ├─ Research Design             │
                    ├─ Research Axes               │
                    ├─ RQ Candidates               │
                    ├─ Design Audit                │
                    ├─ Revision                    │
                    └─ Approved RQ Set             │
                            ▲                      │
                            │                      │
                    RESEARCH_NEED                  │
                    SYSTEM-ORIGINATED ─────────────┘
                            │
                            ▼
                     EGL RESEARCH
                  Search / Acquisition
                  Observation / Evidence
                  Claim / Knowledge State
重要:

Human-originated requestとSystem-originated needは入口が非対称である。

Human languageにはintent fluctuationがある。

Structured system needには別種のerrorがある。

したがって、

text
HUMAN
RAW_REQUEST
→ REQUEST RESOLUTION
→ RESEARCH_REQUEST

SYSTEM
RESEARCH_NEED
→ NEED VALIDATION
→ RESEARCH INTENT
とする。

4. Request Resolution Layer
4.1 Responsibility
Request Resolution Layerの責任:

Human Raw Requestを、EGLが調査対象として扱えるResolved Intentへ変換する。

この層はResearch Questionを作らない。

検索もしない。

ただしintentまたはpremiseの確認に必要なbounded micro-probeは許可する。

5. RAW_REQUEST
Human inputを改変せず保存する。

json
{
  "request_id": "REQ-0001",
  "request_type": "RAW_REQUEST",
  "origin": "HUMAN",
  "raw_text": "プーチンの今後の動向は？",
  "context_refs": [],
  "timestamp": ""
}
Raw Requestはimmutable。

後続の解釈で上書きしない。

6. Context Binding
最初にRaw Requestが現在contextとどの程度接続しているかを見る。

初期classification:

text
HIGH
MEDIUM
LOW
UNRESOLVED
例:

text
「これDW担当に投げれば分かる？」
→ HIGH

「前のv1304の件どうなった？」
→ HIGH

「白樺は木材として価値がある？」
→ LOW

「プーチンの今後は？」
→ current conversation dependent
Context Binding record:

json
{
  "context_binding_id": "CBIND-0001",
  "request_id": "REQ-0001",
  "anchoring": "HIGH",
  "supporting_context_refs": [
    "CTX-0041",
    "CTX-0042"
  ],
  "excluded_context_refs": [],
  "residual": "Domestic-politics interpretation remains plausible."
}
Context anchoringは「現在contextが正しい」というClaimではない。

解釈に使用したcontext relationを記録する。

7. Intent Fluctuation Assessment
Intent Fluctuationは、

同じRaw Requestから、合理的な複数のユーザー意図が成立する程度。

を扱う。

初期実装では一個のscoreに圧縮しない。

最低限4軸で評価する。

7.1 Context Anchoring
text
HIGH
MEDIUM
LOW
UNRESOLVED
7.2 Answer Determinacy
合理的な回答空間の狭さ。

text
DETERMINATE
BOUNDED
OPEN
UNRESOLVED
例:

text
Windows 10の一般提供開始日
→ DETERMINATE

白樺の木材価値
→ BOUNDED

プーチンの今後の動向
→ OPEN
7.3 Intent Breadth
Raw Requestが指し得る目的空間。

text
NARROW
MULTI_AXIS
UNDERCONSTRAINED
UNRESOLVED
7.4 Premise Stability
問いが暗黙に前提とするentity / event / prior artifact / stateの成立可能性。

text
STABLE
UNCERTAIN
SUSPECT
UNRESOLVED
例:

text
「あれどこにあったっけ？」
は対象物の存在を暗黙前提にしている。

見つからない場合:

text
absence of retrieval
≠
proof of nonexistence
したがってpremise自体を検査対象にできる。

8. Fluctuation Assessment Object
json
{
  "assessment_id": "IFA-0001",
  "request_id": "REQ-0001",
  "context_anchoring": "LOW",
  "answer_determinacy": "OPEN",
  "intent_breadth": "UNDERCONSTRAINED",
  "premise_stability": "STABLE",
  "major_intent_branches": [
    "MILITARY_UKRAINE",
    "DOMESTIC_POLITICS",
    "ECONOMIC_REGIME_STABILITY",
    "FOREIGN_POLICY"
  ],
  "assessment_residual": [
    "Time horizon unspecified."
  ]
}
このobject自体はClaim admission対象ではない。

Request interpretation activityのoutput。

9. Interpretation Strategy
Fluctuation Assessmentに応じてstrategyを選ぶ。

初期strategy:

text
DIRECT
CONTEXT_RESOLVE
CHOICE
BOUNDED_MULTI_VIEW
INTENT_PROBE
PREMISE_PROBE
DEFER
9.1 DIRECT
問いが安定し、answer spaceが狭い。

例:

text
Windows 10の発売開始日は？
不要なmulti-axis expansionをしない。

9.2 CONTEXT_RESOLVE
Raw Request単体では複数解釈可能だが、current contextにdominant branchがある。

例:

直前12 turnがUkraine warで、

text
プーチンの今後の動向は？
なら、

text
selected interpretation:
RUSSIA_UKRAINE_WAR_TRAJECTORY
を選び得る。

ただしalternativesをretained uncertaintyとして残す。

9.3 CHOICE
主要branchが複数あり、dominant interpretationを安全に選べない。

例:

text
プーチンの今後
context anchoring LOW。

選択肢提示を許可する。

9.4 BOUNDED_MULTI_VIEW
複数branchを見ること自体がrequestに合理的であり、budget内で短く比較可能。

必ずbranch budgetを持つ。

「全部盛り長文」をdefaultにしない。

9.5 INTENT_PROBE
本調査前に、intent解釈を改善するための極小probeを行う。

例:

text
「あれどこにあったっけ？」
candidate artifact/entity search。

9.6 PREMISE_PROBE
問いの暗黙前提が疑わしい場合。

例:

text
「以前作ったWatcher仕様どこ？」
Watcher仕様の存在を前提に回答しない。

bounded searchでcandidate existenceを確認。

9.7 DEFER
malformed request、insufficient context、policy-required clarification等。

10. Interpretation Explanation Contract (IEC)
全Resolved IntentはIECを持つ。

最低限:

text
INPUT
SELECTED INTERPRETATION
BASIS
RESIDUAL
ALTERNATIVES
REVISION TRIGGER
schema:

json
{
  "iec_id": "IEC-0001",
  "request_id": "REQ-0001",
  "selected_interpretation": "RUSSIA_UKRAINE_WAR_TRAJECTORY",
  "strategy": "CONTEXT_RESOLVE",
  "basis_refs": [
    "CTX-0041",
    "CTX-0042"
  ],
  "basis_summary": [
    "Recent conversation is dominated by Russia-Ukraine war analysis.",
    "Immediately preceding branch concerns Russian military and economic losses."
  ],
  "residual": [
    "Domestic political trajectory remains plausible.",
    "Time horizon remains unspecified."
  ],
  "alternatives": [
    "DOMESTIC_POLITICS",
    "FOREIGN_POLICY"
  ],
  "revision_triggers": [
    "USER_SCOPE_CORRECTION",
    "CONTEXT_CONTRADICTION"
  ]
}
禁止:

text
selected_intent = X
reason = "model judged X most likely"
basisはobservable context refs、explicit user statement、probe result等へ紐付く。

11. RESOLVED_INTENT
Request Resolution成功時に生成。

json
{
  "resolved_intent_id": "RINT-0001",
  "request_id": "REQ-0001",
  "primary_intent": "RUSSIA_UKRAINE_WAR_TRAJECTORY",
  "intent_status": "RESOLVED_WITH_RESIDUAL",
  "strategy": "CONTEXT_RESOLVE",
  "iec_ref": "IEC-0001",
  "retained_intent_branches": [
    "DOMESTIC_POLITICS",
    "FOREIGN_POLICY"
  ]
}
intent_status:

text
RESOLVED
RESOLVED_WITH_RESIDUAL
MULTI_INTENT
CLARIFICATION_REQUIRED
PREMISE_UNRESOLVED
DEFERRED
12. Intent ≠ Research Focus
User IntentとResearch Focusを分離する。

例:

text
USER INTENT:
プーチンの今後の動向

Research discovers:
oil infrastructure damage and fiscal transmission are load-bearing

RESEARCH FOCUS:
economic-military sustainability
Research Focusは調査中に動いてよい。

User Intentを勝手に上書きしてはならない。

schema concept:

json
{
  "research_focus_id": "RFOC-0001",
  "resolved_intent_ref": "RINT-0001",
  "focus": "ECONOMIC_MILITARY_SUSTAINABILITY",
  "basis_claim_refs": [],
  "focus_status": "EMERGENT",
  "does_not_replace_user_intent": true
}
Final Answer / Knowledge PacketはUser Intentへ戻って答える。

Research Focusは説明軸。

13. Request Resolution Error Classes
実運用で最低限以下を記録する。

13.1 INTENT_UNDER_RESOLUTION
揺れの大きい問いを狭く固定しすぎた。

例:

text
SYSTEM:
military-only answer

USER:
いや国内政治の話
13.2 INTENT_OVER_RESOLUTION
安定した問いを過剰展開した。

例:

text
USER:
Windows 10発売日は？

SYSTEM:
RTM / OEM / GA / lifecycle interpretation choice...
User:

text
日付聞いてんだけど
13.3 PREMISE_HALLUCINATION
存在未確認のentity/artifact/stateを存在すると扱った。

13.4 CONTEXT_MISBINDING
無関係なrecent contextをrequest interpretationへ過剰適用した。

13.5 FOCUS_REPLACES_INTENT
調査中に見つかった面白いbranchがUser Intentを置換した。

14. Request Resolution Metrics
初期metrics:

text
User Intent Correction Rate

INTENT_UNDER_RESOLUTION Rate

INTENT_OVER_RESOLUTION Rate

Premise Hallucination Rate

Context Misbinding Rate

Focus-Replaces-Intent Rate

Answer Waste Before Correction

Research Waste Before Intent Correction
14.1 Answer Waste Before Correction
ユーザーが意図修正するまでに生成した不要回答量。

候補measurement:

text
tokens
answer sections
rendered claims
14.2 Research Waste Before Intent Correction
誤intentに対して消費した調査資源。

候補measurement:

text
SearchRun count
AcquisitionRun count
documents fetched
LLM tokens
wall time
external API cost
本仕様ではこれを主要waste metricとする。

15. Explainability Quality Properties for Request Resolution
Request Resolutionの説明可能性を初期は4 propertyで扱う。

15.1 TRACEABILITY
Resolved IntentからRaw Request / context / probeへ戻れる。

15.2 COMPRESSION
短いstructured explanationで解釈理由を再構成できる。

長い自由文説明を要求しない。

15.3 STABILITY
同じRaw Request + same bounded contextでseparate runが大きく異なるstrategy / primary intentを出し続けない。

完全一致を要求しない。

主要branch divergenceを測定する。

15.4 COUNTERFACTUAL SENSITIVITY
load-bearing context / premiseを変更した時、解釈または説明が適切に変化する。

例:

text
Context A:
Ukraine war discussion
→ Putin request resolved to war trajectory

Context B:
Kremlin succession discussion
→ same raw request should not remain automatically war trajectory
同じ出力を維持する場合:

text
context binding dead
or
explanation not load-bearing
候補finding。

16. Request Resolution Counter-Factual Tests
最低限:

text
CF-R1
Remove dominant context refs
→ CONTEXT_RESOLVE must not retain same basis unchanged

CF-R2
Replace Ukraine context with Kremlin succession context
→ selected interpretation or retained branches should change

CF-R3
Stable date question
→ adding irrelevant context must not force CHOICE

CF-R4
Existence-premise request with zero candidate results
→ system must not fabricate location

CF-R5
User explicit correction
→ previous Resolved Intent becomes revised / historical, not silently overwritten

CF-R6
Research Focus changes
→ User Intent remains unchanged unless user or valid revision trigger changes it
17. RESEARCH_REQUEST
Human-originated research enters Research Intent Layer only after Request Resolution.

json
{
  "request_type": "RESEARCH_REQUEST",
  "research_request_id": "RREQ-0001",
  "origin": "HUMAN",
  "raw_request_ref": "REQ-0001",
  "resolved_intent_ref": "RINT-0001",
  "intent_explanation_ref": "IEC-0001",
  "priority": "NORMAL"
}
禁止:

text
RAW_REQUEST → direct Research Design
Request Resolution-enabled profileではsanctioned bypassを持たない。

18. RESEARCH_NEED
System-originated research need。

例:

text
DW cannot perform WORKER_ASSIGNMENT.
schema:

json
{
  "request_type": "RESEARCH_NEED",
  "need_id": "RNEED-0001",
  "origin_system": "DW",
  "origin_task_id": "TASK-001",
  "decision_to_support": "WORKER_ASSIGNMENT",
  "blocked_state": "PLANNING",
  "known_context_refs": [],
  "missing_knowledge_hint": [
    "available coding worker capability"
  ],
  "required_for_progress": true
}
missing_knowledge_hintはRQでもfactでもない。

origin systemのdiagnostic hypothesis。

19. Need Validation
System Needにはhuman intent fluctuationは通常ない。

代わりに、

systemが自分のblock reasonを誤診している可能性

がある。

Need Validationは最低限以下を見る。

text
NV1
Decision identity exists and matches origin Task.

NV2
Blocked state is real in workflow state.

NV3
Known Knowledge State does not already satisfy the decision dependency.

NV4
missing_knowledge_hint is not treated as proven root cause.

NV5
Research is actually required; missing implementation or policy decision is not mislabeled as knowledge gap.

NV6
Origin scope has not expanded beyond Task authority.
Example:

text
DW says:
Need research on better coding models.

Actual state:
Qwen Coder adapter is broken and never invoked.

→ RESEARCH_NEED INVALID / IMPLEMENTATION_BOTTLENECK
Researchを始めない。

これはResearch Waste防止に重要。

20. Need Explanation Contract (NEC)
Validated RESEARCH_NEEDは以下を持つ。

text
ORIGIN DECISION
OBSERVED BLOCK
KNOWN STATE
WHY RESEARCH IS REQUIRED
ALTERNATIVE NON-RESEARCH CAUSES
REVISION TRIGGER
例:

json
{
  "nec_id": "NEC-0001",
  "need_id": "RNEED-0001",
  "origin_decision": "WORKER_ASSIGNMENT",
  "observed_block_refs": [
    "DWSTATE-001"
  ],
  "known_state_refs": [],
  "research_requirement_summary": "No current role-validation state exists for candidate coding workers.",
  "alternative_causes": [
    "worker adapter unavailable",
    "assignment policy undefined"
  ],
  "revision_triggers": [
    "existing valid capability profile discovered",
    "workflow defect identified"
  ]
}
21. Research Intent Layer
Request ResolutionまたはNeed Validation後に共通flowへ入る。

Input:

text
RESEARCH_REQUEST
or
VALIDATED RESEARCH_NEED
責任:

Goal / Decisionを進めるために、何を知る必要があるかを設計する。

22. Research Designer
Research Designerは検索query generatorではない。

主質問:

What must be known for this Goal / Decision to be resolved with fewer unsupported assumptions?

Input:

text
Resolved Intent or Validated Need
Current Knowledge State
Known Gaps
Relevant Failure Patterns
Applicable Non-Guarantees
Operational Capability State
Epistemic Task Profile
Research Budget
Output:

text
Research Design
Research Axes
RQ Candidates
Required / Optional split
Stop Conditions
Residual Questions
23. Research Design Explanation Contract (RDEC)
各Research Axis / Required RQは、

なぜ調べるのか

をdecision-linkedに説明する。

最低限:

text
SOURCE GOAL / DECISION
AXIS OR RQ
WHY REQUIRED
EXPECTED DECISION EFFECT
OMISSION RISK
STOP CONDITION
例:

json
{
  "rdec_id": "RDEC-0001",
  "decision": "WORKER_ASSIGNMENT",
  "axis": "STARTUP_COST",
  "why_required": "A role-capable model may be operationally impractical for frequent task switching.",
  "expected_decision_effect": "May change LOCAL_WORKER vs CLAUDE_ESCALATION assignment.",
  "omission_risk": "Select a capable but operationally unusable worker.",
  "stop_condition_ref": "STOP-001"
}
禁止:

text
axis = STARTUP_COST
reason = "useful information"
24. Research Axis
Research AxisはClaimではない。

「何を見るか」のplanning object。

例:

text
MODEL_AVAILABILITY
SERVING_STATUS
ROLE_CAPABILITY
ROLE_VALIDATION
GPU_RESIDENCY
CONCURRENCY
STARTUP_COST
TASK_LATENCY
各axisは最低限以下に紐付く。

text
supports_decisions
required / optional
safe_behavior_if_unknown
RDEC
Decisionを変えないaxisはRequiredにしない。

25. RQ Candidate
Research AxisからRQ Candidateを生成する。

RQ Candidateは未承認。

SearchPlanへ直接渡さない。

json
{
  "rq_candidate_id": "RQC-0001",
  "question": "",
  "derived_from_axes": [],
  "decision_relevance": "",
  "priority": "REQUIRED",
  "required_for_resolution": true,
  "known_claim_refs": [],
  "known_gap_refs": [],
  "rdec_refs": [],
  "stop_condition_ref": ""
}
26. Research Design Audit
Research Designerとは別context / separate run。

可能ならdifferent weights。

監査質問:

Does this RQ set actually support the stated intent or decision?

最低限:

text
A1 Decision coverage
A2 Missing axis
A3 Redundant axis
A4 Existing-knowledge bias
A5 Capability / operational separation
A6 Existence / usability / validation separation
A7 Decision relevance
A8 Stop-condition adequacy
A9 Unknown handling
A10 Historical failure recurrence
A11 Intent drift
A12 Research focus replacing request
A13 Explanation basis load-bearingness
A11:

Research DesignがResolved Intentより狭く/広く変形していないか。

A12:

emergent research interestがUser Intentを置換していないか。

A13:

RDEC basisをcounter-factualに外した場合、Required statusまたはaxis selectionが変わるか。

27. Research Design Finding
json
{
  "finding_id": "RDF-0001",
  "research_design_id": "RDES-0001",
  "finding_type": "MISSING_AXIS",
  "severity": "MAJOR",
  "target_axis_or_rq": null,
  "description": "",
  "basis_refs": [],
  "proposed_action": "ADD_AXIS"
}
finding_type:

text
MISSING_AXIS
REDUNDANT_RQ
SCOPE_OVERREACH
DECISION_GAP
UNSAFE_UNKNOWN_DEFAULT
EXISTING_KNOWLEDGE_BIAS
CATEGORY_COLLAPSE
STOP_CONDITION_MISSING
BUDGET_MISMATCH
FAILURE_PATTERN_RECURRENCE
INTENT_DRIFT
FOCUS_REPLACES_INTENT
NON_LOAD_BEARING_EXPLANATION
OTHER
Free-form audit summary aloneでworkflowを進めない。

28. Research Revision
Audit Findingsを受けてrevision。

以下を記録:

text
original design
audit findings
accepted findings
rejected findings
axis changes
RQ changes
residual findings
Findingをsilently discardしない。

29. APPROVED_RQ_SET
Audit / Revision後のみ生成。

json
{
  "approved_rq_set_id": "RQS-0001",
  "source_research_design_id": "RDES-0001",
  "source_revision_id": "RDRV-0001",
  "resolved_intent_ref": "RINT-0001",
  "validated_need_ref": null,
  "required_rqs": [],
  "optional_rqs": [],
  "deferred_rqs": [],
  "stop_conditions": [],
  "research_budget": {},
  "approval_status": "APPROVED"
}
Sanctioned path:

text
RESEARCH_REQUEST / VALIDATED NEED
↓
Research Design
↓
Audit
↓
Revision if needed
↓
Approved RQ Set
↓
SearchPlan
禁止:

text
RAW_REQUEST → SearchPlan
RESEARCH_NEED → SearchPlan
RDES draft → SearchPlan
RQ Candidate → SearchPlan
30. Research Focus Dynamics
Research中に新しいload-bearing axisが見つかる場合がある。

Research Focus may shift.

Focus shiftはActivityとして記録。

最低限:

text
previous focus
new focus
basis claim / observation refs
relationship to User Intent
scope effect
Focus shiftがUser Intentを超える場合:

text
DEFER branch
or
new Research Request candidate
勝手にcurrent answerの主題へ昇格しない。

31. Explainable Transformation Record
Request Resolution以降の全重要変換に共通形式を持たせる。

仮称:

text
EXPLAINABLE_TRANSFORMATION
schema:

json
{
  "transformation_id": "XFORM-0001",
  "transformation_type": "RAW_REQUEST_TO_RESOLVED_INTENT",
  "input_refs": [],
  "output_refs": [],
  "basis_refs": [],
  "operation": "",
  "basis_summary": [],
  "retained_uncertainty": [],
  "excluded_scope": [],
  "revision_triggers": [],
  "counterfactual_test_refs": []
}
initial transformation types:

text
RAW_REQUEST_TO_RESOLVED_INTENT
VALIDATED_NEED_TO_RESEARCH_DESIGN
RESOLVED_INTENT_TO_RESEARCH_DESIGN
DECISION_TO_RESEARCH_AXIS
RESEARCH_AXIS_TO_RQ
RQ_SET_TO_SEARCH_PLAN
OBSERVATION_TO_EVIDENCE
EVIDENCE_TO_CLAIM
CLAIM_SET_TO_KNOWLEDGE_PACKET
KNOWLEDGE_PACKET_TO_TASK_PLAN
既存EGL objectと重複する場合、別SoRを作らない。

EXPLAINABLE_TRANSFORMATIONはrelation / trace viewとして実装し、既存event/object refsを利用する。

32. Explainability Governance
Explainability fieldの追加自体もAnti-Drift対象。

各説明fieldは以下の少なくとも一つへ寄与する必要がある。

text
reconstruction
audit
counter-factual test
revision
workflow decision
scope control
寄与しない説明fieldはnoise-text候補。

Narrative explanationを大量保存することをExplainabilityとみなさない。

33. TASK-DRIVEN RESEARCH
DW等system-originated。

text
DW Task
↓
Decision point
↓
Observed block
↓
RESEARCH_NEED
↓
Need Validation
↓
Research Intent
↓
Approved RQ Set
↓
EGL Research
↓
Knowledge Packet
↓
DW resumes
原則自動。

Human confirmationはdefault requirementではない。

Escalation候補:

text
research budget exceed
high-risk profile
origin scope expansion
unresolved MAJOR audit finding
required evidence inaccessible
high-impact contradiction
34. USER-DRIVEN RESEARCH
text
Human Raw Request
↓
Request Resolution
↓
Resolved Intent
↓
Research Request
↓
Research Intent
↓
Approved RQ Set
↓
EGL Research
↓
Answer / Knowledge Packet
Wide requestの場合:

text
PRIMARY AXES
SECONDARY AXES
OUT OF INITIAL SCOPE
を分ける。

Clarificationを毎回要求しない。

Interpretation strategyがCHOICEの場合のみchoice UI / questionを候補とする。

35. Unknown Handling
Unknownをnegative factにしない。

Request Resolution:

text
PREMISE_UNRESOLVED
Research:

text
Knowledge Gap
Deferred RQ
Blocked Decision Dependency
Operational Capability:

text
NOT_TESTED
NOT_VERIFIED
UNRESOLVED
例:

text
Qwen3-Coder-Next role validation unresolved
≠

text
Qwen3-Coder-Next is not capable
36. Operational Capability First Use Case
Initial test:

DW Development ManagerがTask planning、worker assignment、audit assignment、retry、escalationを判断するために、どのOperational Capability情報を知る必要があるか。

Observed trigger:

text
DW asked whether Qwen3.6 alone is sufficient.
Important:

このtriggerから、

text
Research Qwen3.6 alternatives
を直接作らない。

まずNeed Validation:

text
Decision:
WORKER_ASSIGNMENT / AUDITOR_ASSIGNMENT / ESCALATION

Observed block:
No structured Operational Capability State available to DW.

Alternative causes:
DW role policy incomplete
model adapters unavailable
known environment exists outside EGL
Research Designはdecision pointからaxisを生成する。

candidate axes:

text
COMPUTE_RESOURCE
MODEL_AVAILABILITY
SERVING_STATUS
MODEL_RUNTIME
ROLE_CAPABILITY
ROLE_VALIDATION
CONTEXT_LIMIT
CONCURRENCY
GPU_RESIDENCY
STARTUP_COST
TASK_LATENCY
TOOL_ACCESS
REPOSITORY_ACCESS
SHELL_ACCESS
NETWORK_ACCESS
EXTERNAL_SERVICE_ACCESS
ESCALATION_POLICY
Auditは既知inventory categoryだけで軸が生成されていないかを見る。

37. Development Environment / Operational Capability State
Important separations:

text
INSTALLED
≠
AVAILABLE
≠
SERVABLE
≠
OPERATIONALLY_USABLE
≠
ROLE_VALIDATED
Capabilityとoperational costも分離。

Operational Capability Stateはversioned。

text
ENV-PROFILE-v1
ENV-PROFILE-v2
...
Task:

text
executed_under:
ENV-PROFILE-vN
を記録。

38. Research Design Retrospective
調査終了後に以下を観測。

text
Did the information support the intended decision?
What required axis was later found missing?
Which Required RQ was unused?
How many additional research rounds occurred?
What research axis did Taka manually add?
Did user correct the intended meaning?
Did research focus replace user intent?
Design failureはFailure Pattern候補。

initial candidates:

text
CAPABILITY_WITHOUT_OPERATIONAL_COST

EXISTENCE_TO_USABILITY_EXPANSION

RQ_FROM_KNOWN_CATEGORIES_ONLY

SEARCH_BEFORE_DECISION_MODEL

INTENT_UNDER_RESOLUTION

INTENT_OVER_RESOLUTION

PREMISE_HALLUCINATION

FOCUS_REPLACES_INTENT
Automatic admissionは禁止。

adjudicated operational findingから登録。

39. Role Separation
Initial roles:

text
Request Resolver
Qwen3.6 / suitable analyst model

Request Resolution Auditor
separate context / separate run

Research Designer
Qwen3.6 / suitable analyst model

Research Design Auditor
separate context / different weights where practical

Research Reviser
Designer or dedicated reviser

EGL Curation
existing curation / Gate4 path

Exceptional Adjudicator
Claude / GPT upper tier
同一model使用時もcontext separationを要求。

40. Deterministic Enforcement
Python / code owns:

text
schema validation
allowed workflow paths
mandatory Request Resolution for enabled human profiles
mandatory Need Validation for enabled system profiles
mandatory Research Design Audit
Finding preservation
revision linkage
Approved RQ Set validation
budget enforcement
stop-condition state
structured rejection
C-TOTALITY適用。

Malformed model output:

text
None
string
int
list/dict mismatch
missing key
wrong scalar type
nested wrong type
malformed enum
null required object
extreme nesting
Invariant:

text
no uncaught exception
no privileged default
no fail-open
structured problem / rejection / DEFER
41. Activity / Run Logging
Record:

text
Request Resolution Run
Intent Probe Run
Premise Probe Run
Request Resolution Audit Run
Need Validation Run
Research Design Run
Research Design Audit Run
Research Revision Run
Approved RQ Set creation
SearchPlan creation
Minimum:

text
actor
model
model version
runtime config
contract version
input refs
output refs
timestamp
LLM internal memory cannot create Observation.

Interpretation and Research Design outputs are planning / transformation records, not external facts.

42. RRL / RIL Acceptance Metrics
Request Resolution:

text
User Intent Correction Rate
Under-Resolution Rate
Over-Resolution Rate
Premise Hallucination Rate
Context Misbinding Rate
Focus-Replaces-Intent Rate
Answer Waste Before Correction
Research Waste Before Intent Correction
Research Intent:

text
Research Axis Human Add Rate
Required RQ Waste Rate
Post-Research Missing Knowledge Rate
Research Design Audit Yield
Repeated Research Rate
Decision Support Completion Rate
Unknown-to-False-Negative Error
Scope Expansion Rate
Explainability:

text
Transformation Trace Completeness
Explanation Reconstruction Success
Cross-Run Interpretation Stability
Counterfactual Sensitivity Pass Rate
Non-Load-Bearing Explanation Rate
43. Phase RRI-1 Initial Scope
Implement:

text
RAW_REQUEST
Context Binding
Intent Fluctuation Assessment
Interpretation Strategy
IEC
RESOLVED_INTENT
RESEARCH_REQUEST
RESEARCH_NEED
Need Validation
NEC
Research Design
Research Axis
RQ Candidate
RDEC
Research Design Audit
Research Revision
APPROVED_RQ_SET
EXPLAINABLE_TRANSFORMATION trace
workflow gates
budget enforcement
C-TOTALITY tests
Activity / Run logging
Do not implement yet:

text
single universal intent fluctuation score
automatic intent ontology generation
self-modifying interpretation policy
continuous autonomous research
Watcher-driven global expansion
automatic Failure Pattern admission
full user-personality inference
hidden psychoanalysis
unbounded context ingestion
Important:

Request Resolution must use task-relevant context.

It must not build broad psychological narratives about the user.

44. RRI-1 First Test Set
Test A — Stable factual request
text
Windows 10の発売開始日は？
Expected:

text
DETERMINATE
NARROW
DIRECT
No unnecessary choice expansion.

Test B — Open detached request
text
プーチンの今後の動向は？
No dominant context.

Expected:

text
OPEN
UNDERCONSTRAINED
CHOICE or BOUNDED_MULTI_VIEW
Test C — Open but context-bound request
Same raw request after Ukraine-war discussion.

Expected:

text
CONTEXT_RESOLVE
War trajectory may become primary.

Residual alternatives retained.

Test D — Premise unstable
text
前に作ったWatcher仕様どこ？
No verified artifact.

Expected:

text
PREMISE_PROBE
PREMISE_UNRESOLVED if not found
No fabricated path.

Test E — User correction
System resolves broad AI request to local coding tools.

User:

text
いや音声AIの話
Expected:

text
previous RINT retained as historical
new RINT created
INTENT_UNDER_RESOLUTION finding candidate
waste measured
Test F — Focus drift
User asks Putin broad trajectory.

Research finds oil infrastructure highly explanatory.

Expected:

text
Research Focus may shift
User Intent remains broad trajectory
final rendering returns to original intent
Test G — DW Need misdiagnosis
DW submits:

text
Need better coding model research.
Actual worker adapter is disconnected.

Expected:

text
Need Validation rejects research need
classification:
IMPLEMENTATION_BOTTLENECK
No research run.

45. RRI-1 Acceptance Criteria
RRI-1 first slice complete candidate when:

Human RAW_REQUEST and system RESEARCH_NEED are structurally distinct.

Enabled human profile cannot enter Research Design without Request Resolution.

Enabled system profile cannot enter Research Design without Need Validation.

Stable factual requests do not trigger unnecessary multi-branch expansion in tested cases.

Open / underconstrained requests do not silently collapse to a narrow branch without explainable basis in tested cases.

Existence-premise requests do not fabricate a target when bounded probe finds none.

Resolved Intent has IEC with traceable basis, residual, alternatives, revision trigger.

User Intent and Research Focus are structurally separate.

Required Research Axis / RQ has decision-linked RDEC.

Research Design Audit can emit structured INTENT_DRIFT / FOCUS_REPLACES_INTENT / NON_LOAD_BEARING_EXPLANATION findings.

RQ Candidate cannot directly enter SearchPlan through sanctioned workflow.

Audit Findings remain linked through revision.

malformed LLM output does not crash or fail-open deterministic guards.

Counter-factual context tests can demonstrate whether context basis is load-bearing.

Answer Waste Before Correction and Research Waste Before Intent Correction are measurable.

Initial DW Operational Capability Need can pass: Need Validation → Research Design → Audit → Approved RQ Set.

A false DW research diagnosis caused by an implementation bottleneck can be rejected before research begins.

46. Design Principles
P1
Do not search before resolving what the request is being treated as.

P2
Do not assume ambiguity merely because multiple technical interpretations exist.

P3
Do not assume stability merely because one interpretation is convenient.

P4
Intent fluctuation must change workflow behavior or it is noise-metadata.

P5
Question premise is not automatically true.

P6
Absence of retrieval is not proof of nonexistence.

P7
User Intent and Research Focus are separate objects.

P8
Research Need diagnostic hints are hypotheses, not root causes.

P9
RQ is derived from Goal / Decision, not from familiar search categories alone.

P10
Research Design itself must be independently audited.

P11
Every important transformation must have a short, traceable, revisable explanation.

P12
Explanation is not long narrative. It is reconstructable structure.

P13
An explanation basis should be counterfactually testable where practical.

P14
Non-load-bearing explanation fields are noise-text and should not guide decisions.

P15
Unknown is not negative.

P16
The costliest failure is excellent work on the wrong intent.

P17
Measure waste before correction.

P18
The final value is not research volume. It is reaching the intended decision with fewer unsupported assumptions and less wasted work.

47. Conclusion
EGL v0.2 adds two explicit pre-research responsibilities.

text
Request Resolution Layer
↓
What are we treating this request as meaning?

Research Intent Layer
↓
What must be known to serve that intent or decision?
Only then:

text
EGL Research
↓
How do we establish what is supported?
The central architectural addition is not ambiguity detection alone.

It is:

Intent, Research Questions, Evidence, and Claims are all outputs of transformations.

Each transformation may expand scope, replace a premise, or drift from its input.

Therefore each important transformation is treated as an explainable object with:

text
input
output
basis
retained uncertainty
excluded scope / alternatives
revision trigger
The system must be able to answer, in short structured form:

text
Why did we interpret the request this way?
Why did we decide these questions must be researched?
Why do we think these claims are supported?
If those transformations cannot be reconstructed, audited, revised, and counterfactually challenged, the system is not yet sufficiently grounded.

The immediate implementation target is the DW Operational Capability case.

The first practical objective is to prevent two forms of waste:

text
Human:
"お前何言ってんの？"

Human:
"日付聞いてんだけど"
Both are Request Resolution failures.

EGL should detect the difference before expensive research and long-form answer generation begin.
