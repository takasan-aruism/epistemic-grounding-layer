#!/usr/bin/env python3
"""HBB SEALED run (local 11, HBB-04/30 = GPT handoff). Arms A/B/C/D/F × 4 rungs (rung独立).
A base / B skepticism / F retrieval(origin-LOO + per-query leak audit) / C AFE(6 Aruism ops) /
D Formal(sealed 5 axiom + FE-EPSILON + EMP-OBSERVER = 7 probes). E = C∪D derived post-hoc.
frozen probe sets (seal 565899c9/2e301c52/38111563). leak-controlled input = SEALED T0 only."""
import json, sys, re, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl/experiments")
from run_afe_walking import ADMITTED as AFE_OPS, run_operator, aggregate, orchestrate
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=260):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None
def jl(t):
    i, j = t.find("["), t.rfind("]")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]
    except Exception: return [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]
HINTS = {"H0": "次にどう進めるべきか。", "H1": "現在の問題設定自体に、暗黙の追加前提はないか。",
  "H2": "定義と予測、機構と導入時期、局所とprogram、層/主体などを分離して再検討せよ。",
  "H3": "比較対象または観測変数を直接測り、現在のframeを反証できる実験を提案せよ。"}
DEPTH = {"H0": 4, "H1": 3, "H2": 2, "H3": 1}
T0 = json.load(open("/home/takasan/egl/experiments/hbb_sealed_t0.json"))["packets"]
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
# Formal probe ensemble (frozen): 5 sealable axiom + FE-EPSILON + EMP-OBSERVER
FML = json.load(open("/home/takasan/egl/experiments/formal_esde_operators.json"))
EMP = json.load(open("/home/takasan/egl/experiments/formal_empirical_observer_probe.json"))
FORMAL = [{"operator_id": p["probe_id"], "structural_function": p["structural_function"],
           "probe_contract": {"primary_question": p["primary_question"], "secondary_questions": [], "forbidden_expansions": p["forbidden"]}}
          for p in (FML["sealable_axiom_grounded_probes"] + FML["provisional_probes_flagged"] + [EMP])]
# F retrieval pool + origin-LOO markers
def toks(s): return re.sub(r"[^a-z0-9ぁ-んァ-ヶ一-龠 ]", " ", s.lower()).split()
def ng(ws, n): return set(tuple(ws[i:i+n]) for i in range(len(ws)-n+1)) if len(ws) >= n else set()
POOL = []
for p in ["/home/takasan/esde/ESDE-Research/docs/ESDE_失敗の記録.md", "/home/takasan/esde/ESDE-Research/docs/概念理解.md"]:
    for ln in Path(p).read_text().splitlines():
        s = ln.strip().strip("|").strip()
        if len(s) > 40 and not s.startswith("#") and not set(s) <= set("|-— "):
            POOL.append({"text": s, "tw": toks(s)})
ORIGIN = {"HBB-01": ["vacancy", "余白", "future=vacancy"], "HBB-03": ["genesis", "nlp", "qwq", "内部言語", "external"],
 "HBB-05": ["birth", "label", "persistence", "individuation"], "HBB-06": ["v9.13", "s≥0.20", "s>=0.20", "r=0", "n=2 67", "見かけ構造"],
 "HBB-08": ["v6", "物理層", "床", "circulation", "取り込み", "reformation"], "HBB-10": ["v9.18", "v_unified", "kuramoto", "統合", "物理同期"],
 "HBB-11": ["v1110", "v1113", "異系", "node id", "番号コピー"], "HBB-12": ["v10.2", "v1101", "集団平均", "dominant atom", "方向反転", "#33"],
 "HBB-13": ["v1109", "self-fulfilling", "loop", "shuffle", "順序構造"], "HBB-17": ["v1304c", "r_density", "icc", "lens"],
 "HBB-24": ["v4.5", "v4.7", "latent boost", "spatial mismatch", "incorporation"],
 "HBB-04": ["afe", "hybrid filter", "meta-frame", "metaframe", "a-condition", "json-leak", "b/d tradeoff", "axis-level", "local->program", "local_completion", "program_completion"],
 "HBB-30": ["6x", "6倍", "約6", "ternary", "binary", "三値", "二値", "emergence", "創発", "v3.3.1"]}
def retrieve(qid, k=3):
    qt = set(toks(T0[qid]["t0_stuck_frame"])); bw = toks(CAND[qid]["breakthrough_structure"]); B5 = ng(bw, 5)
    markers = [m.lower() for m in ORIGIN.get(qid, [])]
    kept, dropped = [], []
    for u in sorted(POOL, key=lambda u: -len(qt & set(u["tw"])))[:60]:
        low = u["text"].lower()
        if any(m in low for m in markers): continue                       # origin-ID LOO
        ov5 = (len(ng(u["tw"], 5) & B5) / len(B5)) if B5 else 0.0
        if ov5 >= 0.15 or len(qt & set(u["tw"])) < 3:
            if ov5 >= 0.15: dropped.append(u["text"][:60]); continue
            continue
        kept.append(u)
        if len(kept) >= k: break
    return kept, dropped
def cell(args):
    iid, arm, rung = args
    fr = T0[iid]["t0_stuck_frame"]; hint = HINTS[rung]; prov = {}
    if arm == "A":
        out = jl(chat("You are advising on an ongoing research project. What is the single most important thing to do next? Return 1-3 short concrete axes.", f"SITUATION:\n{fr}\n\n{hint}"))
    elif arm == "B":
        out = jl(chat("You are a skeptical research advisor. The current conclusion may be wrong. Find what to check that could show the current frame is mistaken. Return 1-3 short concrete axes.", f"SITUATION:\n{fr}\n\n{hint}"))
    elif arm == "F":
        kept, dropped = retrieve(iid); prov = {"retrieved": [u["text"][:60] for u in kept], "leak_dropped": dropped}
        lessons = "\n".join(f"- (past) {u['text'][:260]}" for u in kept) or "(no cross-incident lesson survived origin-ID leave-one-out)"
        out = jl(chat("You are a research advisor with relevant past lessons. Use them if they help. What to do next? Return 1-3 short concrete axes.", f"RELEVANT PAST LESSONS:\n{lessons}\n\nSITUATION:\n{fr}\n\n{hint}"))
    elif arm in ("C", "D"):
        ops = AFE_OPS if arm == "C" else FORMAL
        frame = fr + "\n\n(hint) " + hint
        with cf.ThreadPoolExecutor(max_workers=len(ops)) as ex:
            sigs = list(ex.map(lambda o: run_operator(o, frame), ops))
        cands = aggregate(sigs); out = orchestrate(frame, cands)
        prov = {"n_signal": sum(1 for s in sigs if s.get("verdict") == "SIGNAL"), "n_cand": len(cands),
                "signal_ops": [s["operator_id"] for s in sigs if s.get("verdict") == "SIGNAL"]}
    return {"id": iid, "scope": CAND[iid]["intervention_scope"], "arm": arm, "rung": rung, "depth": DEPTH[rung],
            "output": out if isinstance(out, list) else [], "provenance": prov}
def main():
    ids = list(T0.keys())
    cells = [(iid, arm, rung) for iid in ids for arm in ("A", "B", "F", "C", "D") for rung in ("H0", "H1", "H2", "H3")]
    print(f"SEALED run: {len(ids)} incidents × 5 arms × 4 rungs = {len(cells)} cells")
    res = []
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for i, r in enumerate(ex.map(cell, cells)):
            res.append(r)
            if (i + 1) % 20 == 0: print(f"  {i+1}/{len(cells)}", flush=True)
    Path("/home/takasan/egl/experiments/hbb_sealed_run.json").write_text(json.dumps({"results": res}, ensure_ascii=False, indent=2))
    print("-> hbb_sealed_run.json")
if __name__ == "__main__":
    main()
