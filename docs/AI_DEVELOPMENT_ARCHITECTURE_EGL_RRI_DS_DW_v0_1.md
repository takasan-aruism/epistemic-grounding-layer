AI Development Architecture — EGL / RRI / DS / DW Integrated Development Specification v0.1
文書種別: Integrated Architecture / Development Specification
状態: PROPOSED / IMPLEMENTATION PLANNING BASELINE
対象: EGL, RRI, DS, DW
目的: AIを用いた長期研究・開発における認識、問い解釈、対話継続、開発実行を4つの責任系へ分離し、相互接続する全体開発方針を定義する。

0. Executive Summary
本開発は以下の4系統から構成する。

text
EGL
Epistemic Grounding Layer
= 何を知っているか / 何が未確定か

RRI
Request Resolution & Research Intent
= 今の問いをどう解釈し、何を調べるべきか

DS
Dialogue State & Continuity
= 対話が今どの状態にあり、何が継続・保留・終了しているか

DW
Dev Workcell
= その認識状態を使って、開発Taskをどう実行・監査・再作業するか
全体像:

text
Conversation / System Request
            │
            ▼
           DS
 Dialogue State / Continuity
            │
            ▼
           RRI
 Request Resolution / Research Intent
            │
            ▼
           EGL
 Evidence / Claim / Current Knowledge
            │
            ▼
           DW
 Plan / Generate / Audit / Rework / Review
            │
            ▼
       RESULT PACKET
            │
            └──────────────→ EGL
ただしこれは一方向pipelineではない。

text
DS → RRI
active thread / open branch / closure scope

RRI → DS
resolved intent / residual / correction / focus shift

RRI → EGL
approved RQ set

EGL → RRI
current claims / gaps / failure patterns

EGL → DW
knowledge packet

DW → EGL
observed results / test results / proposed claims / new gaps
4系統は独立責任を持つが、相互に履歴を供給する。

1. Development Principle
本開発の出発点は以下の経験則である。

text
AIに何を作らせるか
を先に考えるだけでは不十分。

先に、

text
誰が調べるか
誰が問いを解釈するか
誰が知識を採用するか
誰が実装するか
誰が疑うか
誰が再作業させるか
誰が終了を許可するか
何を履歴として残すか
を設計する必要がある。

したがって本開発は、

AI Development Systemを開発する前に、AI Development Organizationを設計する。

という方針を取る。

2. System Responsibilities
2.1 EGL — KNOW
EGLの責任:

text
Source
Acquisition
Observation
Evidence
Claim
Currentness
Historical state
Supersession
Knowledge Gap
Failure Pattern
Source Trace
Knowledge Admission
中心質問:

What is currently supported, what was historically believed, and what remains unresolved?

EGLは「どう実装するか」を決めない。

EGLは「ユーザーが本当は何を聞きたいか」を主責任としない。

EGLはGlobal Knowledgeの採用責任を持つ。

2.2 RRI — MEAN / ASK
RRIの責任:

text
Raw Request resolution
Intent fluctuation assessment
Premise assessment
Context binding
Interpretation strategy
Resolved Intent
Research Need validation
Research Design
Research Axis generation
RQ generation
Research Design Audit
Approved RQ Set
Explainable transformation trace
中心質問:

text
What are we treating this request as meaning?

What must be known to serve that intent or decision?
RRIはEGL Researchの前段である。

既存仕様:

EGL Request Resolution & Research Intent Specification v0.2

を現行設計参照とする。

本統合仕様ではRRIの詳細再定義は行わない。

2.3 DS — CONTINUE
DSの責任:

text
Dialogue event recording
Thread reconstruction
Active thread detection
Branch relation
Dialogue state transition
Closure assessment
Partial closure
Open residual preservation
Reference candidate resolution
Dialogue continuity
Dialogue state reconstruction
Context selection support for RRI
中心質問:

What dialogue is currently continuing, what has been closed, and what unresolved branches must remain available?

DSは単なるshort / mid / long memory systemではない。

記憶を時間長で分類するのではなく、

text
OPEN
ACTIVE
PARTIALLY_CLOSED
CLOSED
DORMANT
REOPENED
SUPERSEDED
という対話状態を扱う。

2.4 DW — DO
DWの責任:

text
Task Unit creation
Task planning
Implementation Packet
Worker assignment
Implementation execution coordination
Independent Audit
Finding management
Rework
Retry
Escalation
Upper Review
Completion workflow
Result Packet generation
中心質問:

Given the current grounded state, how should this development task be executed and challenged?

DWはKnowledge Admissionを行わない。

DWはGlobal Knowledge DBを更新しない。

DWが返すのは:

text
observed results
implementation runs
test results
attacker findings
review results
proposed claims
new gap candidates
まで。

3. Current Development Status
EGL
状態:

text
structural spine complete candidate
Phase1a closed
Phase1b acquisition first slice established
Gate4 / ETB narrow structural properties established
SELF_GROUNDING baseline and adversarial round completed
permanent review mechanisms introduced
EGLは今後、RRI / DS / DW開発の実運用履歴を扱う。

RRI
状態:

text
Specification v0.2 exists
implementation not yet completed
主要追加:

text
Request Resolution Layer
Intent Fluctuation
Premise Assessment
Intent ≠ Research Focus
Research Need Validation
Research Design Audit
Explainable Transformations
優先度:

text
HIGH
DS
状態:

text
concept identified
formal specification not yet implemented
優先方針:

text
Phase 0:
event schema / raw logging first

Later:
state reconstruction intelligence
DW
状態:

text
repository created
role concept defined
formal implementation specification draft required
初期構成:

text
Claude Code
= Development Manager

Qwen coding model
= Coding Worker

Qwen analyst / separate model
= Independent Auditor / Attacker

Claude Code
= Upper Review

Python
= workflow enforcement

GPT / Claude upper tier
= Exceptional Adjudicator
4. Development Order
Recommended order:

text
1. DS Phase 0
   Event schema / raw dialogue logging

2. RRI implementation
   Request Resolution + Research Intent

3. DW walking skeleton
   Task Unit workflow

4. RRI and DW development history recorded through EGL

5. DS intelligence
   Dialogue state reconstruction using accumulated data

6. DS → RRI context binding integration

7. Full RRI → EGL → DW → EGL loop
This is not:

text
complete DS
↓
complete RRI
↓
complete DW
Instead:

text
DS records data early

RRI becomes intelligent early

DW becomes operational

EGL stores the history

DS intelligence is evaluated on accumulated interaction history
5. EGL as Development Memory for RRI / DS / DW
All three remaining projects should use EGL for:

text
design decisions
implementation reports
test results
review findings
scope corrections
failed assumptions
failure patterns
open gaps
current / historical state separation
Example RRI:

text
OBSERVATION
RRI Test B required user intent correction

REVIEW FINDING
Context resolution narrowed intent too early

INFERENCE
Recent-context weighting may be too strong

OPEN GAP
How much dialogue state should Context Binding consume?
Example DS:

text
OBSERVATION
PARTIALLY_CLOSED thread was auto-closed

FAILURE
Open residual branch lost

OPEN GAP
Closure residual preservation rule insufficient
Example DW:

text
OBSERVATION
Qwen Coder failed initial cross-module implementation

AUDIT
3 meaningful findings

REWORK
2 closed, 1 remained

ESCALATION
Claude Code required
Repeated operational patterns may become Failure Pattern candidates.

6. DS Specification Draft v0.1
6.1 Name
Working name:

text
Dialogue State & Continuity
DS
Repository may be separate or initially integrated as a dedicated module.

The architectural responsibility must remain separate from RRI.

6.2 Core Problem
Current LLM conversation handling usually relies on:

text
recent raw context
summary memory
long-term memory
This is insufficient for long-running conversations.

The main problem is not only:

text
What happened before?
It is:

text
What dialogue is still continuing?

Which branch is active?

Which branch was closed?

What was only partially answered?

Which unresolved topic may be referred to by:
「あの件」
「前のやつ」
「そこじゃなくて」
「もう一点」
「戻るけど」
A dialogue can be old and still active.

A dialogue can be recent and already closed.

Therefore:

text
temporal recency
≠
dialogue continuity
6.3 Core Thesis
DS treats dialogue as a stateful graph of threads and branches.

text
Conversation Stream
↓
Dialogue Events
↓
Thread / Branch Candidates
↓
State Transition Candidates
↓
Dialogue State Reconstruction
↓
Current Dialogue State
The system must not equate:

text
answer delivered
=
thread closed
Closure is scope-sensitive.

6.4 Primary DS Objects
Initial objects:

text
UTTERANCE
DIALOGUE_EVENT
THREAD_CANDIDATE
DIALOGUE_THREAD
DIALOGUE_BRANCH
STATE_TRANSITION
CLOSURE_ASSESSMENT
REFERENCE_CANDIDATE
DIALOGUE_STATE_SNAPSHOT
6.5 UTTERANCE
Raw human / assistant message.

Immutable.

json
{
  "utterance_id": "UTT-0001",
  "speaker": "USER",
  "raw_text": "",
  "timestamp": "",
  "preceding_utterance_ref": null,
  "conversation_id": ""
}
No interpretation is stored in UTTERANCE.

6.6 DIALOGUE_EVENT
Interpretive event generated from one or more utterances.

json
{
  "dialogue_event_id": "DEV-0001",
  "utterance_refs": [
    "UTT-0001"
  ],
  "event_type": "PROVISIONAL_ANALYSIS",
  "thread_candidates": [],
  "transition_candidate": "CONTINUE",
  "focus_candidate": "",
  "closure_candidate": null,
  "actor": "",
  "model": "",
  "status": "PROVISIONAL"
}
Initial analysis is provisional.

Do not directly mint final thread state from a single LLM response.

6.7 DIALOGUE_THREAD
A continuing dialogue unit.

json
{
  "thread_id": "DTH-0001",
  "topic_summary": "EGL request interpretation architecture",
  "state": "OPEN",
  "active_focus": "dialogue state handling",
  "parent_thread_ref": null,
  "open_branch_refs": [],
  "closed_branch_refs": [],
  "closure_scope": [],
  "closure_residual": [],
  "last_transition_ref": ""
}
Important:

topic_summary is a compressed label.

It is not the full source of truth.

Thread identity must remain traceable to utterance / event history.

6.8 DIALOGUE_BRANCH
A subproblem, unresolved axis, or focus branch within a thread.

Example:

text
Thread:
RRI architecture

Branches:
- Intent Fluctuation
- Explainability
- Dialogue State dependency
- Development order
schema:

json
{
  "branch_id": "DBR-0001",
  "thread_id": "DTH-0001",
  "branch_summary": "",
  "state": "OPEN",
  "opened_by_event_ref": "",
  "closed_by_event_ref": null,
  "residual": []
}
6.9 Dialogue States
Initial states:

text
OPEN
ACTIVE
PARTIALLY_CLOSED
CLOSED
DORMANT
REOPENED
SUPERSEDED
UNRESOLVED
OPEN
Thread exists and has unresolved scope.

ACTIVE
Current dialogue is primarily operating on this thread.

PARTIALLY_CLOSED
Some scope resolved; meaningful residual remains.

CLOSED
Current known scope is sufficiently resolved for normal continuation.

Closure does not mean globally final truth.

DORMANT
Not currently active, but continuity remains valid.

REOPENED
Previously closed / dormant thread becomes active again.

SUPERSEDED
Thread framing itself has been replaced by a later framing.

UNRESOLVED
State cannot be safely determined.

6.10 Closure Assessment
Closure is not binary inference from answer delivery.

Minimum inputs:

text
question determinacy
resolved intent
answer scope
remaining branches
intent residual
user correction
user continuation
explicit acceptance
Closure assessment:

json
{
  "closure_assessment_id": "CLS-0001",
  "thread_id": "DTH-0001",
  "determinacy": "OPEN",
  "answered_scope": [],
  "remaining_scope": [],
  "closure_candidate": "PARTIALLY_CLOSED",
  "basis_refs": [],
  "revision_triggers": []
}
Examples:

Windows 10 release date:

text
DETERMINATE
answer supplied
no meaningful residual

→ CLOSED candidate
Putin future trajectory:

text
OPEN
multi-axis
time horizon unresolved

→ PARTIALLY_CLOSED or OPEN
6.11 Closure Principle
text
Answer correctness
≠
Dialogue closure
A correct answer may close a narrow factual request.

A correct answer to an open question may only close the answered scope.

Therefore:

text
CLOSED
must include closure_scope
Example:

json
{
  "state": "PARTIALLY_CLOSED",
  "closure_scope": [
    "short-term military trajectory",
    "current economic pressure"
  ],
  "closure_residual": [
    "domestic regime stability",
    "succession",
    "medium-term foreign policy"
  ]
}
6.12 Dialogue Transitions
Initial transition types:

text
OPEN_THREAD
CONTINUE
FOCUS_SHIFT
OPEN_BRANCH
CLOSE_BRANCH
PARTIAL_CLOSE
CLOSE_THREAD
REOPEN
INTENT_CORRECTION
REFERENCE_RESOLUTION
SUPERSEDE
DORMANT
Transitions must be history-bearing.

Do not silently overwrite current state.

6.13 Reference Resolution
DS supports references such as:

text
あの件
前のやつ
それ
そこじゃなくて
さっきの
もう一点
戻るけど
This is not a keyword search problem.

It is:

text
Dialogue State Pointer Resolution
Candidate ranking may use:

text
active thread
recent focus
open branches
partially closed branches
recent intent corrections
entity overlap
semantic relation
temporal distance
Output:

json
{
  "reference_resolution_id": "REF-0001",
  "utterance_ref": "UTT-0102",
  "reference_text": "あの件",
  "candidate_threads": [
    {
      "thread_ref": "DTH-0007",
      "rank": 1,
      "basis": [
        "ACTIVE_THREAD",
        "RECENT_OPEN_BRANCH"
      ]
    }
  ],
  "resolution_status": "RESOLVED_WITH_RESIDUAL"
}
6.14 DS → RRI Contract
DS provides:

text
ACTIVE_THREAD_SET
OPEN_BRANCH_SET
PARTIAL_CLOSURE_SET
REFERENCE_CANDIDATES
RECENT_INTENT_CORRECTIONS
RECENT_FOCUS_SHIFTS
Example:

json
{
  "packet_type": "DIALOGUE_STATE_PACKET",
  "schema_version": "0.1",
  "active_threads": [],
  "open_branches": [],
  "partially_closed_threads": [],
  "reference_candidates": [],
  "recent_intent_corrections": [],
  "recent_focus_shifts": []
}
RRI uses this for Context Binding.

DS does not decide final Resolved Intent.

6.15 RRI → DS Contract
RRI returns:

text
RESOLVED_INTENT
RETAINED_ALTERNATIVES
INTENT_RESIDUAL
USER_INTENT_CORRECTION
RESEARCH_FOCUS
ANSWER_SCOPE
These are state transition signals.

6.16 DS Explainability
Every meaningful thread-state transformation should be reconstructable.

Minimum:

text
input events
previous state
new state
basis
remaining uncertainty
revision trigger
Do not require long narrative.

6.17 DS Phase 0
Immediate implementation.

Goal:

Start collecting reconstructable dialogue data before full DS intelligence exists.

Implement:

text
UTTERANCE
DIALOGUE_EVENT
provisional thread candidates
transition candidate
focus candidate
closure candidate
model / run metadata
raw append-only logging
All interpretation fields remain:

text
PROVISIONAL
Initial DS does not need to make authoritative dialogue state decisions.

6.18 DS Phase 1
Dialogue State Reconstruction.

Input:

text
UTTERANCE history
DIALOGUE_EVENT candidates
RRI outputs
user corrections
Output:

text
DIALOGUE_THREAD
DIALOGUE_BRANCH
STATE_TRANSITION
DIALOGUE_STATE_SNAPSHOT
Primary test model:

text
Qwen3.6
Goal:

Determine whether structured dialogue-state representation allows a local model to approach high-tier model context resolution quality.

6.19 DS Benchmark
Compare:

Baseline
text
Claude / GPT
+ raw long conversation history
DS System
text
Qwen3.6
+ Dialogue State Packet
+ bounded recent raw utterances
Challenge cases:

text
あの件
前のやつ
それじゃなくて
もう一点
戻るけど
前に逆だっただろ
そこは終わった
まだその話
Metrics:

text
Reference Resolution Accuracy
Wrong Thread Selection Rate
User Correction Rate
Closure Error Rate
Open Branch Loss Rate
False Reopen Rate
Context Tokens Used
Answer Waste Before Correction
Cross-Run State Stability
6.20 DS Initial Acceptance Criteria
Raw utterances are immutable and append-only.

Initial LLM analysis is provisional.

Answer delivery does not automatically close a thread.

CLOSED / PARTIALLY_CLOSED include scope.

OPEN residual branches can remain available after topic focus shifts.

State transitions are history-bearing.

User correction can revise thread state without overwriting history.

DS can produce a bounded Dialogue State Packet for RRI.

Reference resolution can return multiple candidates and residual uncertainty.

Qwen3.6 + DS can be compared against a raw-history high-tier model baseline.

7. DW Specification Draft v0.1
7.1 Name
Repository:

text
dev-workcell
System name:

text
DW
Dev Workcell
7.2 Core Problem
Historical ESDE development repeatedly showed:

text
Claude Code designs / implements
↓
tests pass
↓
Taka says:
「本当に？」
「懐疑的に見て」
「もう一回壊せ」
↓
new defect found
↓
result changes
This indicates that normal AI development flow:

text
TASK
↓
IMPLEMENT
↓
TEST PASS
↓
DONE
terminates too early.

DW exists to mechanize:

text
GENERATE
↓
AUDIT
↓
REGENERATE
↓
UPPER REVIEW
at every Task Unit.

Primary experimental question:

Can the system replace Taka’s repeated manual skepticism instruction with a structured development team workflow?

7.3 DW Core Thesis
Every meaningful development task is executed by a workcell.

text
PLAN
↓
GENERATE
↓
AUDIT
↓
REGENERATE
↓
UPPER REVIEW
↓
COMPLETE
The generator does not self-certify completion.

The Development Manager does not bypass mandatory audit.

Python / deterministic code owns workflow legality.

7.4 Roles
Initial roles:

text
Development Manager
Claude Code

Coding Worker
Qwen coding model

Independent Auditor / Attacker
Qwen analyst / separate model / separate weights

Reworker
Original Coding Worker

Upper Reviewer
Claude Code

Exceptional Adjudicator
GPT / Claude upper tier

Workflow Gate
Python deterministic state machine
Role principle:

text
generator
≠
auditor
Prefer:

text
different weights
different context
different run
7.5 Development Manager
Claude Code in DW acts as:

text
Development Manager
Responsibilities:

text
read EGL Knowledge Packet
understand current project state
define narrow Task goal
create Implementation Packet
select Worker
select Audit strategy
review Findings
decide rework
propose escalation
perform Upper Review
generate Result Packet
Claude Code should not default to implementing all code itself.

Direct senior implementation is reserved for:

text
repeated worker failure
architecture-sensitive change
cross-module migration
novel integration
explicit escalation
7.6 Task Unit
All development activity belongs to a Task Unit.

Objects:

text
TASK
PLAN
IMPLEMENTATION_PACKET
IMPLEMENTATION_RUN
TEST_RESULT
FINDING
REVISION
UPPER_REVIEW
COMPLETION
RESULT_PACKET
All objects reference:

text
task_id
7.7 TASK
json
{
  "task_id": "TASK-0001",
  "project_id": "RRI",
  "goal": "",
  "state": "CREATED",
  "knowledge_packet_ref": "",
  "risk_class": "NORMAL"
}
7.8 Task States
Initial states:

text
CREATED
PLANNING
WAITING_FOR_RESEARCH
READY_FOR_IMPLEMENTATION
IMPLEMENTING
READY_FOR_AUDIT
AUDIT_FAILED
REWORK
READY_FOR_UPPER_REVIEW
JUDGE_REQUIRED
COMPLETE
BLOCKED
Transitions are deterministic-policy controlled.

7.9 EGL → DW Knowledge Packet
Minimum input:

json
{
  "packet_type": "KNOWLEDGE_PACKET",
  "schema_version": "0.1",
  "task_context": "",
  "current_claims": [],
  "historical_claims": [],
  "open_gaps": [],
  "related_failure_patterns": [],
  "non_guarantees": [],
  "operational_capabilities": [],
  "source_trace": []
}
DW must preserve:

text
validation mode
property scope
currentness
non-guarantee
7.10 Implementation Packet
Manager output.

Minimum:

json
{
  "implementation_packet_id": "IP-0001",
  "task_id": "TASK-0001",
  "goal": "",
  "current_assumptions": [],
  "relevant_open_gaps": [],
  "forbidden_assumptions": [],
  "related_failure_patterns": [],
  "acceptance_criteria": [],
  "expected_files_or_scope": [],
  "escalation_conditions": []
}
The Implementation Packet is the operational translation of EGL Knowledge State.

7.11 Standard Team Unit Workflow
PLAN
Claude Code reads:

text
Task
Knowledge Packet
project state
Creates:

text
narrow goal
current assumptions
relevant gaps
forbidden assumptions
related failures
acceptance criteria
GENERATE
Coding Worker receives Implementation Packet.

Worker:

text
inspect repo
implement requested scope
run tests
return diff
return run information
return problems
AUDIT
Independent Auditor receives:

text
original Task
Implementation Packet
implementation diff
test results
relevant EGL Failure Patterns
Auditor is instructed to attack.

Priority:

text
requirement not actually implemented
dead guard
disconnected value
self-report primitive
acceptance test not load-bearing
scope expansion
historical failure recurrence
unrequested change
REGENERATE
Original Worker receives accepted Findings.

Worker:

text
address Findings
rerun tests
report unresolved Findings
UPPER REVIEW
Claude Code reviews:

text
original Task
EGL context
initial implementation
Findings
revision
test results
Determines:

text
finding closed
finding remains
new gap
additional attack required
escalation required
completion candidate
COMPLETE
Python confirms mandatory process occurred.

Claude Code cannot unilaterally bypass missing audit.

Generate Result Packet.

Return to EGL.

7.12 FINDING
Free-form audit alone must not control workflow.

Structured Finding:

json
{
  "finding_id": "FND-0001",
  "task_id": "TASK-0001",
  "finding_type": "REQUIREMENT_NOT_IMPLEMENTED",
  "severity": "MAJOR",
  "target_ref": "",
  "description": "",
  "basis_refs": [],
  "proposed_action": "REWORK"
}
Initial finding types:

text
REQUIREMENT_NOT_IMPLEMENTED
DEAD_GUARD
DISCONNECTED_VALUE
SELF_REPORT_PRIMITIVE
NON_LOAD_BEARING_TEST
SCOPE_EXPANSION
HISTORICAL_FAILURE_RECURRENCE
UNREQUESTED_CHANGE
CONTRACT_VIOLATION
TEST_GAP
ARCHITECTURE_RISK
OTHER
7.13 Rework
Rework must preserve:

text
original implementation
findings
accepted findings
rejected findings
revision diff
new tests
remaining findings
Findings are not silently removed.

7.14 Upper Review
Upper Reviewer asks:

text
Was the original Task actually addressed?

Were accepted Findings closed?

Did rework create new scope?

Do tests prove the claimed property?

Does the result remain within EGL non-guarantees?

Is another attack round required?

Is Claude Code senior implementation required?

Is exceptional adjudication required?
Upper Review produces structured verdict.

7.15 Completion
Completion is a workflow state, not a prose claim.

Minimum Completion prerequisites for standard workflow:

text
Implementation Run exists
Test Result exists
Independent Audit exists
Findings have dispositions
Required Rework completed or explicitly unresolved
Upper Review exists
Result Packet valid
Python owns enforcement.

7.16 DW → EGL Result Packet
json
{
  "packet_type": "RESULT_PACKET",
  "schema_version": "0.1",
  "task_id": "",
  "implementation_runs": [],
  "test_results": [],
  "attacker_findings": [],
  "revisions": [],
  "upper_review": {},
  "observed_results": [],
  "proposed_claims": [],
  "new_gap_candidates": [],
  "completion_status": ""
}
Important:

text
proposed_claims
≠
accepted claims
DW cannot declare:

text
FACT VERIFIED
CURRENT KNOWLEDGE
EGL performs admission.

7.17 DW Research Need
If DW cannot make a decision due to missing knowledge:

text
WORKER_ASSIGNMENT
AUDITOR_ASSIGNMENT
ESCALATION
TASK PLANNING
DW emits:

text
RESEARCH_NEED
DW does not author final RQ set.

RRI performs Need Validation and Research Design.

7.18 Operational Capability State
DW Manager requires current knowledge of:

text
compute
models
runtimes
tool access
repo access
role capability
role validation
operational cost
escalation services
Important separation:

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
DW must not infer role suitability from model existence.

7.19 Retry / Escalation Policy
Initial policy should be narrow and measurable.

Example:

text
first worker failure
→ rework

same finding class repeats
→ second audit / manager review

repeated worker failure
→ Claude Code escalation candidate

architecture-sensitive or cross-module migration
→ senior review before implementation or early escalation

unresolved MAJOR finding
→ COMPLETE forbidden

novel property claim
→ external adjudication candidate
Exact thresholds are versioned policy.

7.20 DW Explainability
Every major task transformation should be reconstructable.

Examples:

text
Knowledge Packet
→ Implementation Packet

Finding
→ Rework decision

Repeated failure
→ Escalation

Upper Review
→ Completion candidate
Minimum explanation fields:

text
input
decision
basis
rejected alternatives
remaining uncertainty
revision trigger
Do not store long managerial chain-of-thought.

7.21 DW Initial Metrics
Primary experiment:

Can DW reduce Taka manual skepticism intervention?

Metrics:

text
First-Pass Acceptance Rate
Independent Finding Count
Finding Severity
Rework Rate
Post-Audit Result Change Rate
Known Failure Pattern Recurrence
Scope Violation Count
Unrequested Change Count
Retry Count
Claude Escalation Rate
Taka Intervention Count
Taka Skepticism Prompt Count
Meaningful Defect Discovery Before Human Intervention
Additional:

text
Qwen Worker vs Claude direct implementation cost
tokens
wall time
GPU time
external API cost
7.22 First Real Workload
Use real projects:

text
RRI
DS Phase 0
DW self-development
and later ESDE.

Do not begin with artificial coding benchmark only.

First 5–10 Tasks should be real development Tasks.

7.23 DW Self-Development
DW should eventually develop DW.

However:

text
DW self-development result
still returns to EGL.

DW cannot self-certify global truth.

7.24 DW Initial Acceptance Criteria
Every implementation activity belongs to a Task Unit.

Task state transitions are deterministic-policy controlled.

Standard workflow cannot COMPLETE without Independent Audit.

Generator and Auditor are separate roles / runs.

Findings are structured.

Findings remain linked through Rework.

Upper Review receives original Task, Knowledge Packet, implementation, Findings, revision, and test results.

Claude Code cannot bypass mandatory workflow gates.

DW can emit RESEARCH_NEED when planning is knowledge-blocked.

DW cannot author final Approved RQ Set.

Result Packet separates observed results and proposed claims.

DW cannot directly write EGL Global Knowledge.

First 5 real development Tasks can run end-to-end.

Taka intervention count is measurable.

Meaningful defect discovery before human skepticism prompt is measurable.

8. Cross-System Contracts
8.1 DS → RRI
text
DIALOGUE_STATE_PACKET
Contains:

text
active threads
open branches
partially closed threads
reference candidates
recent intent corrections
recent focus shifts
8.2 RRI → DS
text
RESOLUTION_SIGNAL
Contains:

text
resolved intent
retained alternatives
intent residual
intent correction
research focus
answer scope
8.3 RRI → EGL
text
APPROVED_RQ_SET
8.4 EGL → DW
text
KNOWLEDGE_PACKET
8.5 DW → EGL
text
RESULT_PACKET
8.6 DW → RRI
text
RESEARCH_NEED
When a development decision is knowledge-blocked.

9. Shared Explainability Principle
Across RRI, DS, EGL, and DW:

Every meaningful transformation must be reconstructable from short structured records and references.

Common transformation pattern:

text
INPUT
↓
TRANSFORMATION
↓
OUTPUT
Required trace:

text
input refs
output refs
basis refs
operation / decision
retained uncertainty
excluded scope or alternatives
revision trigger
This is not chain-of-thought storage.

It is structural explainability.

10. Shared Failure Pattern Candidate
The current cross-project recurring failure:

text
IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION
Definition:

A narrow behavior, observation, test, or implementation establishes X, but a human or LLM description compresses it into broader X+ not directly supported by the underlying evidence.

Known pattern forms:

text
implementation X
→ guarantee X+

test X
→ property X+

answer scope X
→ intent resolved X+

branch answered X
→ thread closed X+

model installed X
→ role usable X+
RRI / DS / DW should all treat this as relevant.

11. Shared Data Strategy
All systems should distinguish:

text
raw event
provisional analysis
adjudicated state
current derived view
Do not overwrite raw history with derived interpretation.

12. Repository Strategy
Recommended repositories:

text
epistemic-ledger
= EGL + RRI modules

dev-workcell
= DW

dialogue-state
= DS
RRI remains tightly coupled to EGL because it directly uses:

text
RQ
Knowledge Gap
SearchPlan
Failure Pattern
Knowledge State
Therefore RRI should remain in the EGL repository as a separate module.

DW remains separate repository.

DS may begin as a Phase 0 logging module, but should become logically independent once reconstruction intelligence begins.

13. Immediate Next Actions
Action 1
Register this integrated development architecture in EGL.

Action 2
Implement DS Phase 0.

Minimum:

text
UTTERANCE
DIALOGUE_EVENT
provisional thread candidate
transition candidate
focus candidate
closure candidate
raw append-only storage
run metadata
Action 3
Start RRI implementation from v0.2.

Action 4
Start DW walking skeleton.

Minimum:

text
Task Unit
state machine
Knowledge Packet
Implementation Packet
Finding
Result Packet
standard workflow
Qwen worker adapter
Qwen auditor adapter
Claude Manager contract
Action 5
Use EGL to manage RRI / DS / DW development history from the first real implementation Task.

14. Development Evaluation
The combined system should ultimately answer four different failure questions.

EGL
text
Did we believe something stronger than the evidence?
RRI
text
Did we solve the wrong question?
DS
text
Did we lose what conversation was still continuing?
DW
text
Did we terminate development before it had been independently challenged?
The four systems are complementary.

A failure in any one can invalidate downstream work.

text
Wrong Dialogue State
↓
Wrong Intent

Wrong Intent
↓
Wrong Research

Wrong Research Grounding
↓
Wrong Knowledge

Wrong Development Workflow
↓
Bad Implementation accepted too early
Therefore:

text
DS
→ RRI
→ EGL
→ DW
is the primary logical dependency chain.

Operationally, however, development should proceed incrementally:

text
DS records
RRI interprets
EGL grounds
DW executes
while all four systems use EGL to accumulate design and failure history.

15. Final Development Position
The current project is no longer one monolithic AI agent.

It is an AI work system composed of four responsibilities.

text
DS
continuity

RRI
meaning and research intent

EGL
epistemic grounding

DW
development execution
The immediate goal is not to complete all four before use.

The goal is:

text
start recording DS data now

make RRI intelligent next

make DW operational

use EGL to preserve and reuse everything learned
The expected long-term loop:

text
Dialogue State
↓
Resolved Intent
↓
Approved Research Questions
↓
Grounded Knowledge
↓
Development Task
↓
Implementation / Audit / Rework
↓
Observed Result
↓
EGL
↓
next dialogue / next task
The system should gradually reduce four human interventions:

text
「あの件だよ」

「そういう意味じゃない」

「前に逆だっただろ」

「本当に？ 懐疑的に見て」
DS, RRI, EGL, and DW each target one of these failure modes.

That is the current integrated development architecture.
