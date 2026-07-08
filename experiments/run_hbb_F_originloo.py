#!/usr/bin/env python3
"""Phase 5 gate (i): origin-ID leave-one-out で F 再実行。
現行 5-gram LOO は F の self-recall(query 自身の documented lesson 想起)を取り逃した。
各 incident の origin marker(v-number+固有語)を含む pool unit を除外して F を再実行 → RECALL_SELF/TRANSFER 分離。"""
import json, sys, re, urllib.request, concurrent.futures as cf
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=260):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
HINTS = {"H0": "次にどう進めるべきか。", "H1": "現在の問題設定自体に、暗黙の追加前提はないか。",
  "H2": "定義と予測、機構と導入時期、局所とprogram、層/主体などを分離して再検討せよ。",
  "H3": "比較対象または観測変数を直接測り、現在のframeを反証できる実験を提案せよ。"}
DEPTH = {"H0": 4, "H1": 3, "H2": 2, "H3": 1}
T0 = json.load(open("/home/takasan/egl/experiments/hbb_t0_packets.json"))["packets"]
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
# origin marker: query 自身の documented source を pool から除外(origin-ID leave-one-out)
ORIGIN = {
 "HBB-02": ["動的均衡", "dynamic equilibrium", "K_sys"],
 "HBB-09": ["v5.1", "洗濯機", "27k", "E↔V", "選択なき循環"],
 "HBB-14": ["v1301", "run 長", "run長", "life→n_labels", "寿命同期", "トートロジー"],
 "HBB-16": ["v1304c", "M=20", "pooled 220", "検出力", "ICC", "前提ずれ床"],
 "HBB-22": ["τ=100", "n=5 38", "2ノード閉路"],
 "HBB-23": ["v1302", "#CW7", "Mantel", "plb スカラ", "仕込んだノブ"],
 "HBB-25": ["co-serve", "co serve"], "HBB-26": ["disposition", "rework"],
 "HBB-07": ["v9.13", "S≥0.20", "S>=0.20", "神の手", "age_r", "persistence birth"],
 "HBB-15": ["v12 ", "builder 交絡", "atom×atom", "STEP2"],
 "HBB-18": ["v10.11", "v10.5", "§35", "上位資料", "自明な再観察"],
 "HBB-19": ["v10.12", "smoke", "seed0", "seed 0", "符号反転"],
 "HBB-20": ["v9.14", "Layer A", "Layer B", "paired audit", "runtime 主体置換", "早すぎ"],
 "HBB-27": ["batch re-induction", "multi-membership"], "HBB-28": ["memory injection"],
 "HBB-29": ["Sleep Mode", "wake_up", "sleep"],
}
def toks(s): return re.sub(r"[^a-z0-9ぁ-んァ-ヶ一-龠 ]", " ", s.lower()).split()
def ng(ws, n): return set(tuple(ws[i:i+n]) for i in range(len(ws)-n+1)) if len(ws) >= n else set()
POOL = []
for p in ["/home/takasan/esde/ESDE-Research/docs/ESDE_失敗の記録.md", "/home/takasan/esde/ESDE-Research/docs/概念理解.md"]:
    src = Path(p).name
    for ln in Path(p).read_text().splitlines():
        s = ln.strip().strip("|").strip()
        if len(s) > 40 and not s.startswith("#") and not set(s) <= set("|-— "):
            POOL.append({"src": src, "text": s, "tw": toks(s)})
def retrieve_originloo(qid, k=3):
    qt = set(toks(T0[qid]["t0_stuck_frame"])); bw = toks(CAND[qid]["breakthrough_structure"]); B5 = ng(bw, 5)
    markers = [m.lower() for m in ORIGIN.get(qid, [])]
    scored = sorted(POOL, key=lambda u: -len(qt & set(u["tw"])))
    kept, excl_origin = [], []
    for u in scored[:60]:
        low = u["text"].lower()
        if any(m in low for m in markers):  # origin-ID leave-one-out: query 自身の source を除外
            excl_origin.append(u["text"][:70]); continue
        ov5 = (len(ng(u["tw"], 5) & B5) / len(B5)) if B5 else 0.0
        if ov5 >= 0.15 or len(qt & set(u["tw"])) < 3: continue
        kept.append(u)
        if len(kept) >= k: break
    return kept, excl_origin
def cell(args):
    iid, rung = args
    kept, excl = retrieve_originloo(iid)
    lessons = "\n".join(f"- (past, {u['src']}) {u['text'][:280]}" for u in kept) or "(no cross-incident lesson survived origin-ID leave-one-out)"
    sysp = "You are a research advisor with access to relevant past lessons/incidents. Use them if they help. Answer concisely: what to do next? Return 1-3 short concrete axes."
    resp = chat(sysp, f"RELEVANT PAST LESSONS:\n{lessons}\n\nSITUATION:\n{T0[iid]['t0_stuck_frame']}\n\n{HINTS[rung]}")
    return {"id": iid, "rung": rung, "depth": DEPTH[rung], "response": resp.strip()[:600],
            "retrieved": [u["text"][:70] for u in kept], "excluded_own_origin": excl[:5]}
def main():
    ids = json.load(open("/home/takasan/egl/experiments/hbb_split.json"))
    run_ids = ids["DEV"] + ids["VALIDATION"]
    cells = [(iid, rung) for iid in run_ids for rung in ("H0", "H1", "H2", "H3")]
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(cell, cells))
    Path("/home/takasan/egl/experiments/hbb_F_originloo_run.json").write_text(json.dumps({"results": res}, ensure_ascii=False, indent=2))
    nex = sum(1 for r in res if r["excluded_own_origin"])
    print(f"F origin-LOO re-run done. {nex} cells excluded >=1 own-origin unit. -> hbb_F_originloo_run.json")
if __name__ == "__main__":
    main()
