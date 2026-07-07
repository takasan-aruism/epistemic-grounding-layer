#!/usr/bin/env python3
"""Round B v2: abstract 条件を MASK_PIPELINE v2(token 漏れ修正)で再測。ordinary/concrete は v1 run から再利用。
abstract_v1 と abstract_v2 を並べて blind score し、token 漏れ減 + XDOMAIN/HIT の変化を比較。"""
import json, sys, hashlib, datetime, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe_mask as MP
from run_roundb import HELDOUT, RETRIEVED, chat, jl, BASE

def main():
    # re-seal v2(source 修正後)
    h = hashlib.sha256(MP.pipeline_source().encode()).hexdigest()
    Path("/home/takasan/egl/experiments/mask_pipeline_v2_seal.json").write_text(json.dumps(
        {"pipeline": MP.VERSION_V2, "sha256": h, "sealed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "fix": "token leak fixed (domain-only masking, natural generic phrases, article-collapse)", "supersedes": "MASK_PIPELINE_v1"}, ensure_ascii=False, indent=2))
    print(f"MASK_PIPELINE v2 re-sealed: {h[:20]}")
    v1 = json.load(open("/home/takasan/egl/experiments/roundb_run.json"))["heldout"]
    v1map = {x["id"]: x for x in v1}
    out = {"mask_pipeline": MP.VERSION_V2, "seal": h, "heldout": []}
    for ho in HELDOUT:
        r = RETRIEVED[ho["retr"]]
        prev = v1map[ho["id"]]["axes"]
        ab2 = jl(chat(BASE, f"A relevant past incident (abstracted): {MP.mask_v2(r)}\n\nUsing it if helpful:\n{ho['pre']}", seed=0))
        out["heldout"].append({"id": ho["id"], "domain": ho["domain"], "retr": ho["retr"], "missing_axis": ho["axis"],
                               "axes": {"ordinary": prev["ordinary"], "concrete": prev["concrete"],
                                        "abstract_v1": prev["abstract"], "abstract_v2": ab2}})
        print(f"[{ho['id']} {ho['domain']}] abstract_v2 done", flush=True)
    Path("/home/takasan/egl/experiments/roundb_v2_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    # token-leak 検出(placeholder token が答に literal 出現するか)
    LEAK = ["VERSION", "STATE", "SIZE", "GROUP", "PARAM", "RESERVE", "FLAG", "TRACK", "COMPONENT", "ACTOR", "NUMBER", "EVENT"]
    def leaks(axes): return sum(1 for a in axes for t in LEAK if t in a)
    l1 = sum(leaks(x["axes"]["abstract_v1"]) for x in out["heldout"])
    l2 = sum(leaks(x["axes"]["abstract_v2"]) for x in out["heldout"])
    # ESDE literal 検出(R=0 等が答に残るか)
    ESDE = ["R=0", "R>0", "birth-time", "CID", "E3", "CidSelf", "n_core", "phase+r", "ghost", "label finding"]
    def esde(axes): return sum(1 for a in axes for t in ESDE if t.lower() in a.lower())
    e_c = sum(esde(x["axes"]["concrete"]) for x in out["heldout"])
    e1 = sum(esde(x["axes"]["abstract_v1"]) for x in out["heldout"])
    e2 = sum(esde(x["axes"]["abstract_v2"]) for x in out["heldout"])
    print(f"\n=== token-leak (placeholder が答に literal 出現) ===")
    print(f"  abstract_v1: {l1}   abstract_v2: {l2}   (v2 で減れば修正成功)")
    print(f"=== ESDE literal 残存(R=0 等が答に) ===")
    print(f"  concrete: {e_c}   abstract_v1: {e1}   abstract_v2: {e2}")
    out["leak_metrics"] = {"token_leak_v1": l1, "token_leak_v2": l2, "esde_literal": {"concrete": e_c, "abstract_v1": e1, "abstract_v2": e2}}
    Path("/home/takasan/egl/experiments/roundb_v2_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
