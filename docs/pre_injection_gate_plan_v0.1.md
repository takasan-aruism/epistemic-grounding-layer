# Pre-Injection Applicability / NULL-Injection Gate — Walking-Slice Plan v0.1

Status: **PLAN — pre-implementation, subject to independent review** (per Taka directive). Date 2026-07-08.
Not implemented. This plans the walking slice B/C/D/E and its RRI/EGL/DW responsibility mapping.

## 0. Origin & design hypothesis
Round B v2 produced two signals (EGL DE-0091/0092/0093):
1. Abstracting a memory representation eliminated **literal** cross-domain transfer (concrete 22 → abstract_v2 0,
   deterministic; DE-0093 tested scope).
2. **Memory injection did not beat NULL/ordinary** (ordinary HIT 9 > memory conditions 8) — injection can *lower*
   expected value when the task/frame mismatch.

A memory/incident/meta-frame is a **reasoning prior** (it steers content-branching), unlike an **output constraint**
(JSON / numbering / length). A reasoning prior at low applicability is a distortion source.

**Design hypothesis (NOT admitted as a theory claim — a hypothesis formed from Round B):**
`Net(C, Q) ≈ useful-guidance(Applicability(Q,C)) − distortion(Mismatch(Q,C))`.

**Core question:** *Can we decide, BEFORE injecting a reasoning prior into the main reasoning context, whether it is
worth injecting for this task?* Separate two decisions: **(1) inject memory at all?** and **(2) if so, which
representation / abstraction level?** Do not move toward "always use meta-frame".

## 1. Responsibility boundaries (DD-ARCH-6/7)
| concern | owner |
|---|---|
| forming the pre-injection applicability question; output-constraint vs reasoning-prior distinction; gate decision **design** (YES/NO/UNKNOWN); research design of the gate experiment | **RRI** |
| the memory/frame library + currentness; the **evidence-status metadata** the gate may read (task evidence status, whether historically-relevant missing-axis classes exist) — **without exposing frame content** | **EGL** |
| implementing + running the gate experiment, controls, deterministic measurement; the gate classifier as an **experiment artifact** (not admitted as policy) | **DW** |
| routing task → gate → (NULL path \| memory-retrieval path) as a legal transition | **Director** |
The gate is an **RRI applicability-selection layer**, tested by DW, over an EGL-owned library. No component
maintains an alternative memory SoR; the gate admits no knowledge.

## 2. Hard constraint — the gate runs before content exposure
The gate MUST decide before the main reasoning LLM sees any frame/incident/lesson **content**.
**Forbidden (any of these invalidates the slice):**
- putting all meta-frames into the prompt and asking "decide if useful";
- showing a retrieved incident and *then* judging relevance;
- claiming a fair NULL comparison in the same context that already read memory content.

## 3. Gate input allow-list (initial slice)
Gate candidate may read ONLY (derived from the base-model FIRST PASS + EGL metadata):
- task / resolved intent; task domain / object class; requested decision type;
- base-model first-pass answer **structure** (not the memory);
- unresolved / contradiction / path-closing signals;
- EGL evidence status for the task;
- whether the base answer already contains the historically-relevant **missing-axis classes**.
**NOT passed to the gate:** meta-frame body, incident body, lesson body.

## 4. B — Pre-injection gate decision (design slice)
First decision: `MEMORY_INJECTION_NEEDED? = YES | NO | UNKNOWN`.
- `NO` → `NULL_INJECTION` (answer from base reasoning only).
- `YES` → proceed to memory candidate retrieval / applicability design → then representation choice
  (`CONCRETE_INCIDENT` / `ABSTRACT_INCIDENT` / `META_FRAME`) — decision (2), separate.
- `UNKNOWN` → bounded comparison / probe; **do not auto-inject**.
No general scheduler in this slice.

## 5. C — Gate experiment design
Corpus: Round B held-out set + additional incidents (span the 5 domains). Procedure:
1. Run ordinary / base-model first pass; observe task state (allow-list §3 only).
2. Gate candidate (RRI-designed) emits YES/NO/UNKNOWN from task state — **no memory content**.
3. Independently, run NULL and best-memory conditions to get the *ground truth* of which tasks NULL actually won
   vs memory helped (this ground truth is computed post-hoc; the gate never sees it).
- **Primary Q:** can the gate route the task classes where **NULL actually won** to `NO` *before* injection?
- **Secondary Q:** can it keep the subtle tasks where memory helped at `YES`?

## 6. D — Controls
- **CONTROL A** — always NULL.
- **CONTROL B** — always inject the best-retrieved memory.
- **CONTROL C** — LLM relevance prompt AFTER memory content exposure ("use this memory if relevant").
- **TREATMENT** — pre-injection gate, **no memory content exposure**.
Goal: measure whether the pre-injection gate beats the plain "use if relevant" prompt (CONTROL C) — i.e., whether
deciding *before* content exposure avoids the branch-bias that CONTROL C already incurs by reading the content.

## 7. Metrics (no composite score)
`NULL_WIN_correctly_gated_NO`, `MEMORY_HELPFUL_correctly_gated_YES`, `false_positive_injection`,
`false_negative_memory_suppression`, `UNKNOWN_rate`, downstream `HIT` / `USEFUL`,
`XDOMAIN_LITERAL` (deterministic, sealed policy 396977dc), `XDOMAIN_SEMANTIC` (secondary), `OVER_TRIGGER`,
`H3_intervention`. Kept as raw dimensions.

## 8. E — Round C (deferred until gate pilot)
After the gate pilot: 4-arm `NULL / CONCRETE / ABSTRACT_v2 / FULL-PREDICATE META-FRAME` to measure the
**abstraction-degree curve** — but NOT by injecting all four equivalently into every task. Instead: measure the
abstraction curve on the tasks the gate routes to `YES`, and measure the gate's NULL routing on the rest. The two
decisions (inject? / which representation?) stay separated.

## 9. Preregistered interpretation (fixed before the gate pilot runs)
- gate routes NULL-win tasks to NO AND keeps memory-helpful tasks YES, beating CONTROL C → **provisional positive:
  pre-injection applicability is decidable from task state without content exposure**.
- gate ≈ CONTROL C → deciding before content exposure adds nothing over "use if relevant".
- gate ≈ CONTROL B (always inject) → task-state signals don't discriminate; injection policy is not gateable here.
- gate over-suppresses (false_negative high) → task-state signals miss the subtle memory-helpful cases.

## 10. Non-claims
No general scheduler. No "always use meta-frame". No admission of the design hypothesis as theory. One pilot does
not establish a self-improvement or general-metacognition claim. Semantic cross-domain safety remains NOT
established (DE-0093); only literal-transfer elimination is established in tested scope.

## 11. Open questions for the independent reviewer
1. Is "historically-relevant missing-axis classes present in base answer?" (§3) computable **without** leaking frame
   content into the gate? (Leaning: EGL returns only class *labels* + a boolean, never the frame body.)
2. UNKNOWN handling: bounded probe design — how bounded, and does the probe itself risk content exposure?
3. Ground-truth (§5.3) is post-hoc; is the NULL-vs-memory ground truth itself reliable given Qwen's lenient HIT
   scoring? (May need the deterministic XDOMAIN_LITERAL as the more trustworthy axis for the primary Q.)
