"""CLI: write CURRENT_STATE.json from the mechanical builder (SLICE-1).

The ONLY writer. CURRENT_STATE.json is a regenerable/deletable projection (rollback = delete).
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from autonomy.current_state import build_current_state, REPO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "CURRENT_STATE.json"))
    a = ap.parse_args()
    state = build_current_state()
    with open(a.out, "w") as f:
        f.write(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"-> {a.out} | latest_de={state['latest_de']} n_de={state['n_de_entries']} "
          f"seals={len(state['seals'])} closed_branches={len(state['closed_branches'])} "
          f"validation_failures={len(state['validation_failures'])} "
          f"candidate_work={len(state['candidate_executable_work'])} spec_stale={state['spec_staleness']['stale']}")


if __name__ == "__main__":
    main()
