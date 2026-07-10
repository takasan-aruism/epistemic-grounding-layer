# PREREG — SLICE-6 client-usable surface via git (2DER autonomous loop v0)

**why:** Claude Code operates the DEV environment; Taka (client) is a SEPARATE environment. SLICE-1/5 tools are dev-local (python CLI + local HTML) and NOT client-usable. Taka's client has **git CLI** and uses **GitHub as the transport** (answered 2026-07-10). Client has **no python, browser optional**.
**class:** AUTO-WITH-SMALL-ADAPTER, reversible. **authority:** none (surface only). **rollback:** git revert / delete files.
**claim ceiling:** a git-transported observe+correct surface. NOT autonomous decision-making, NOT evidence promotion, NOT a hosted service. C≠H.

## Frozen contract
- **Observation surface:** `autonomy/state_report.py` regenerates a human-readable **`docs/STATE.md`** (Markdown) from `build_current_state()`. Committed (NOT gitignored) so the client reads it via `git pull` + `cat`/GitHub. Deterministic modulo `as_of`.
- **Correction surface:** `autonomy/amend.sh` — **pure POSIX/bash, no python** — appends ONE well-formed Taka event to `AUTONOMY_LEDGER.jsonl` (owner=Taka, AE-##### high-water via awk, ISO ts via `date`, JSON-escaped content). Client runs `amend.sh ACTION TARGET CONTENT [REASON]` then `git commit && git push`. The 7 actions match `amend.py`.
- **Transport:** `AUTONOMY_LEDGER.jsonl` is TRACKED (append-only shared correction log). Client appends via `amend.sh` + git; dev `git pull` → `build_state.py` overlay applies (SLICE-5, already built) → `state_report.py` regenerates `docs/STATE.md` → commit. Loop closed over git.
- **Compatibility invariant:** an event produced by `amend.sh` MUST be loadable by `current_state.load_taka_events()` and drive the overlay identically to `amend.py` events (shell↔python round-trip).
- **read-only invariant:** neither tool writes to the knowledge SoR (`data/events.jsonl`) or `DESIGN_EVIDENCE_LEDGER.jsonl`. `amend.sh` writes only `AUTONOMY_LEDGER.jsonl`; `state_report.py` writes only `docs/STATE.md`.
- `docs/CLIENT_USAGE.md` documents the client workflow.

## Tests (`test_autonomy_client.py`)
- T1 `state_report` produces non-empty Markdown containing latest DE + decision queue; deterministic modulo as_of.
- T2 **round-trip:** run `amend.sh TAKA_HOLD <kind> reason` against a temp ledger → `load_taka_events()` parses it → overlay marks the work item held (shell event == python event behavior).
- T3 `amend.sh` rejects an unknown action (non-zero exit).
- T4 `amend.sh` JSON is valid (each appended line `json.loads`-parses to a dict with the 9 event keys + owner==Taka).
- T5 `amend.sh` is read-only to SoR/DE ledger (md5 unchanged).
- T6 two `amend.sh` appends → 2 lines, monotonically increasing AE ids (append-only).

## Gate
independent audit (author≠auditor): shell↔python compatibility · read-only · no fabricated authority · self-contained STATE.md · JSON validity/escaping → VALID なら record + commit.
