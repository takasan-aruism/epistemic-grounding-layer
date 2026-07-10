"""SLICE-6 observation surface: regenerate docs/STATE.md (human-readable) from CURRENT_STATE.
Committed (not gitignored) so the client reads it via `git pull` + cat/less/GitHub. No browser/python
needed client-side. Deterministic modulo as_of. Contract: docs/autonomy_slice6_prereg_v0.1.md.
"""
import sys, os, argparse
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from autonomy.current_state import build_current_state, REPO


def render_md(st):
    seals = st["seals"]
    n_ok = sum(1 for s in seals if s["status"] == "OK")
    n_mis = sum(1 for s in seals if s["status"] == "MISMATCH")
    ncomp = sum(len(v) for v in st["component_files"].values())
    L = []
    L.append("# 2DER autonomous loop — STATE (client-readable)\n")
    L.append(f"_as_of {st['as_of']} · schema {st['schema_version']} · owner=Taka · "
             "correction/adjudication surface (not a product)_\n")
    L.append("> Observe here (`git pull` then read). To correct, run `autonomy/amend.sh` "
             "then `git commit && git push` (see `docs/CLIENT_USAGE.md`). Corrections are "
             "append-only machine events, not text edits.\n")

    L.append("## A · System state\n")
    L.append(f"- latest DE: **{st['latest_de']}** ({st['n_de_entries']} entries)")
    L.append(f"- components: {ncomp} · seals OK: {n_ok}/{len(seals)}"
             + (f" · **{n_mis} MISMATCH**" if n_mis else ""))
    L.append(f"- closed branches: {len(st['closed_branches'])} (heuristic) · "
             f"validation failures: {len(st['validation_failures'])} · "
             f"candidate work: {len(st['candidate_executable_work'])}")
    L.append(f"- spec: {'STALE' if st['spec_staleness']['stale'] else 'synced'} "
             f"(spec@{st['spec_staleness']['spec_latest_de']} / ledger@{st['spec_staleness']['ledger_latest_de']})")
    L.append(f"- UNOWNED: {', '.join(st['unowned_constructs'])}\n")

    L.append("## C · Taka decision queue\n")
    if st["authority_pending"]:
        for a in st["authority_pending"]:
            L.append(f"- **{a['action']}** `{a['target_object']}` — {a.get('content')}"
                     + (f" _(reason: {a['reason']})_" if a.get("reason") else "") + f" · {a['event_id']}")
    else:
        L.append("- _no active Taka holds/redirects._")
    L.append("\n### Candidate executable work (mechanical) — correct here\n")
    if not st["candidate_executable_work"]:
        L.append("- _none pending._")
    for w in st["candidate_executable_work"]:
        tgt = w.get("kind")
        held = f" **[HELD {w['held_by']}]**" if w.get("held_by") else ""
        L.append(f"- P{w.get('priority')} `{w.get('kind')}`{held} — ref: `{w.get('ref')}`")
        L.append(f"  - correct: `autonomy/amend.sh TAKA_HOLD {tgt} \"reason\"` · "
                 f"`... TAKA_REDIRECT {tgt} \"do this instead\"` · "
                 f"`... TAKA_PRIORITY_OVERRIDE {tgt} 9`")

    L.append("\n## Applied Taka corrections (downstream effects)\n")
    if st["taka_overlay_effects"]:
        for e in st["taka_overlay_effects"]:
            L.append(f"- {e}")
    else:
        L.append("- _none applied yet._")

    L.append("\n## E · Detail\n")
    if st["validation_failures"]:
        L.append(f"<details><summary>validation failures ({len(st['validation_failures'])})</summary>\n")
        for f in st["validation_failures"]:
            L.append(f"- {f.get('artifact')} — {f.get('kind')} {f.get('detail','')}")
        L.append("</details>\n")
    L.append(f"<details><summary>closed branches ({len(st['closed_branches'])}, CLAUDE-DERIVED heuristic)</summary>\n")
    for c in st["closed_branches"]:
        L.append(f"- {c['de']} — {c['decision']}")
    L.append("</details>\n")

    L.append("## D · Correction actions (append-only machine events)\n")
    L.append("`TAKA_CORRECTION` `TAKA_PRIORITY_OVERRIDE` `TAKA_HOLD` `TAKA_REJECT` "
             "`TAKA_REDIRECT` `TAKA_AUTHORITY_RECLASSIFICATION` `TAKA_CONTEXT_ADDITION`\n")
    L.append("origin tags — MECHANICAL (parsed fact) · CLAUDE-DERIVED (heuristic) · TAKA-OWNED (owner authority). "
             "Program disposition / value·UX / new premise = TAKA-GATED.\n")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "docs" / "STATE.md"))
    a = ap.parse_args()
    md = render_md(build_current_state())
    Path(a.out).write_text(md)
    print(f"-> {a.out} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
