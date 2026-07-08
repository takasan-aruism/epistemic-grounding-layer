#!/usr/bin/env python3
"""HBB Phase 4 baseline: arms A(Base)/B(skepticism)/F(retrieval) × DEV/VAL(16) × Hint ladder H0-H3.
§13.3: 各 rung は新規 context-clean session(rung 独立=主指標 Independent Hint Sufficiency)。
F: retrieval over frozen sources, leave-one-out + per-query leak audit(breakthrough に高 overlap する unit を drop)。
provenance 全記録(外部 spot-check 前提)。leak-controlled: input = T0 packet(pre-intervention)のみ。"""
import json, sys, re, urllib.request, concurrent.futures as cf
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=260):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
# preregistered hints (§4.1, class 非依存・答えを名指ししない)
HINTS = {"H0": "次にどう進めるべきか。", "H1": "現在の問題設定自体に、暗黙の追加前提はないか。",
  "H2": "定義と予測、機構と導入時期、局所とprogram、層/主体などを分離して再検討せよ。",
  "H3": "比較対象または観測変数を直接測り、現在のframeを反証できる実験を提案せよ。"}
DEPTH = {"H0": 4, "H1": 3, "H2": 2, "H3": 1}
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
T0 = json.load(open("/home/takasan/egl/experiments/hbb_t0_packets.json"))["packets"]
# retrieval pool: frozen sources を line/row 単位へ
def toks(s): return re.sub(r"[^a-z0-9ぁ-んァ-ヶ一-龠 ]", " ", s.lower()).split()
def ng(ws, n): return set(tuple(ws[i:i+n]) for i in range(len(ws)-n+1)) if len(ws) >= n else set()
POOL = []
for p in ["/home/takasan/esde/ESDE-Research/docs/ESDE_失敗の記録.md", "/home/takasan/esde/ESDE-Research/docs/概念理解.md"]:
    src = Path(p).name
    for ln in Path(p).read_text().splitlines():
        s = ln.strip().strip("|").strip()
        if len(s) > 40 and not s.startswith("#") and not set(s) <= set("|-— "):
            POOL.append({"src": src, "text": s[:300], "tw": toks(s)})
def retrieve(qid, k=3):
    """token-overlap 上位、leave-one-out + per-query leak audit(query breakthrough に 5-gram>=0.15 は drop)。"""
    qt = set(toks(T0[qid]["t0_stuck_frame"])); bw = toks(CAND[qid]["breakthrough_structure"]); B5 = ng(bw, 5)
    scored = sorted(POOL, key=lambda u: -len(qt & set(u["tw"])))
    kept, dropped = [], []
    for u in scored[:40]:
        ov5 = (len(ng(u["tw"], 5) & B5) / len(B5)) if B5 else 0.0
        if ov5 >= 0.15 or len(qt & set(u["tw"])) < 3:  # leak-suspect or too-weak
            if ov5 >= 0.15: dropped.append({"text": u["text"][:80], "overlap5": round(ov5, 3)})
            continue
        kept.append(u)
        if len(kept) >= k: break
    return kept, dropped
ARMS = {
  "A": lambda t0, hint: ("You are advising on an ongoing research project. Given the current situation, answer concisely: what is the single most important thing to do next? Return 1-3 short concrete axes.", f"SITUATION:\n{t0}\n\n{hint}"),
  "B": lambda t0, hint: ("You are a skeptical research advisor. The current conclusion may be wrong. Find what to check that could show the current frame is mistaken. Return 1-3 short concrete axes.", f"SITUATION:\n{t0}\n\n{hint}"),
}
def run_cell(args):
    iid, arm, rung = args
    t0 = T0[iid]["t0_stuck_frame"]; hint = HINTS[rung]; prov = {}
    if arm == "F":
        kept, dropped = retrieve(iid); prov = {"retrieved": [u["text"][:80] for u in kept], "leak_dropped": dropped}
        lessons = "\n".join(f"- (past, {u['src']}) {u['text']}" for u in kept) or "(no sufficiently-similar past lesson survived the leak audit)"
        sysp = "You are a research advisor with access to relevant past lessons/incidents. Use them if they help. Answer concisely: what to do next? Return 1-3 short concrete axes."
        u = f"RELEVANT PAST LESSONS:\n{lessons}\n\nSITUATION:\n{t0}\n\n{hint}"
    else:
        sysp, u = ARMS[arm](t0, hint)
    resp = chat(sysp, u)
    return {"id": iid, "class": CAND[iid]["class"], "arm": arm, "rung": rung, "depth": DEPTH[rung], "response": resp.strip()[:600], "provenance": prov}
def main():
    ids = json.load(open("/home/takasan/egl/experiments/hbb_split.json"))
    run_ids = ids["DEV"] + ids["VALIDATION"]
    cells = [(iid, arm, rung) for iid in run_ids for arm in ("A", "B", "F") for rung in ("H0", "H1", "H2", "H3")]
    print(f"HBB baseline: {len(run_ids)} incidents × 3 arms × 4 rungs = {len(cells)} independent sessions")
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run_cell, cells))
    Path("/home/takasan/egl/experiments/hbb_baseline_run.json").write_text(json.dumps({"hints": HINTS, "results": res, "pool_size": len(POOL)}, ensure_ascii=False, indent=2))
    fdrop = sum(len(r["provenance"].get("leak_dropped", [])) for r in res if r["arm"] == "F")
    print(f"done. retrieval leak-audit dropped {fdrop} unit-instances across F cells. -> hbb_baseline_run.json")

if __name__ == "__main__":
    main()
