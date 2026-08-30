#!/usr/bin/env python3
"""ESDE が 渡した 本番 anchor pack で 4視点を 回す(★ITEM-2DER-EVO-0031)。

★視点ごとに ★渡す材料が 違う(ESDE が 分けて くれた)= ★そのまま 使う。★私が 混ぜ直さない。
"""
import json, os, re, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perspectives_v0 as P

D = os.path.dirname(os.path.abspath(__file__))
PACK = "/home/takasan/egl/data/esde_anchor_pack_for_inference_control.json"


def _call(prompt, max_tokens=512, seed=0):
    from twoder import detail_llm as DL
    return DL.call_for_detail(prompt, body=prompt, seed=seed, max_tokens=max_tokens)


def _json(t):
    m = re.search(r"\{.*\}", t or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _fields(pack, persp):
    """★視点ごとに ★ESDE が 分けた 材料だけ 渡す(★兄弟を 渡さない 視点が 在る)。"""
    inp = pack["input_by_perspective"][persp]
    a = pack["anchor"]["name"]
    par = (pack["input_by_perspective"]["HIERARCHY"]["parents_now"] or ["(親は未登録)"])[0]
    if persp == "EQUALITY":
        sib, known = inp["siblings_same_parent"], []
    elif persp == "SYMMETRY":
        sib = inp["siblings_for_context"]
        known = ["%s と %s（%s）" % (a, x.get("other"), x.get("observation_kind"))
                 for x in inp["existing_symmetry"]]
    elif persp == "LINKAGE":
        sib = []                                   # ★兄弟を 渡さない(ESDE が そう 分けた)
        known = ["%s ← %s（%s: %s）" % (a, x.get("other"), x.get("observation_kind"),
                                        (x.get("basis") or "")[:40])
                 for x in inp["cross_family_only"]] + \
                ["2ホップ先: " + s for s in inp["two_hop_neighbours"]]
    else:
        sib, known = inp["parents_now"], []
    return {"anchor": a, "parent": par,
            "siblings": "\n".join("・" + s for s in sib) or "・(この視点では 渡していない)",
            "known": "\n".join("・" + s for s in known) or "・(まだ無い)",
            "task": (pack.get("task_excerpt") or "")[:900]}


def run(pack, persp, seeds=(0, 1, 2)):
    gen, aud = P.PERSPECTIVES[persp]
    f = _fields(pack, persp)
    f["example"] = P.EXAMPLES[persp]
    got, raw = [], []
    for s in seeds:
        r = _call(gen % f, seed=s)
        o = _json(r.get("content") or "")
        raw.append({"seed": s, "tokens": r.get("completion_tokens"), "json": o is not None})
        a = (o or {}).get("answer")
        if isinstance(a, dict):
            a = [a]
        for x in (a or []):
            if isinstance(x, dict):
                got.append(x)
    # ★機械が 先に 見る= ★台帳に 在るか は 文字照合(★LLM に 聞かない)
    ledger = set()
    for v in pack["input_by_perspective"].values():
        for key in ("siblings_same_parent", "siblings_for_context", "two_hop_neighbours", "parents_now"):
            ledger |= set(v.get(key) or [])
        for x in (v.get("existing_symmetry") or []) + (v.get("cross_family_only") or []):
            ledger.add(x.get("other"))
    ledger.add(pack["anchor"]["name"])
    votes, rows = {}, []
    for x in got:
        c = x.get("candidate") or x.get("upper")
        if not c:
            continue
        votes[c] = votes.get(c, 0) + 1
        rows.append({"candidate": c, "perspective": persp,
                     "target": x.get("counterpart_of") or x.get("siblings") or pack["anchor"]["name"],
                     "direction": x.get("direction"), "reasoning": x.get("why"),
                     "generator_version": P.VERSION, "already_in_ledger": c in ledger})
    two = {r["candidate"]: r for r in rows if votes[r["candidate"]] >= 2}
    fresh = [r for r in two.values() if not r["already_in_ledger"]]
    audited = {}
    if fresh:
        cand = "\n".join("%d. %s（%s）" % (i + 1, r["candidate"], r.get("reasoning") or "")
                         for i, r in enumerate(fresh))
        o = _json((_call(aud % dict(f, candidates=cand)).get("content") or ""))
        est = set((o or {}).get("established") or [])
        need = {x.get("n") for x in ((o or {}).get("needs_check") or []) if isinstance(x, dict)}
        for i, r in enumerate(fresh, 1):
            r["audit_result"] = "PASS" if i in est else ("NEEDS_CHECK" if i in need else "UNJUDGED")
        audited = {"json": o is not None, "established": len(est), "needs_check": len(need)}
    return {"perspective": persp, "generator_version": P.VERSION, "raw": raw,
            "候補(のべ)": len(rows), "2票以上": len(two), "1票で落とした": len(rows) - sum(votes[c] for c in two),
            "既に台帳に在る": sum(1 for r in two.values() if r["already_in_ledger"]),
            "新しい": len(fresh), "auditor": audited, "rows": fresh}


if __name__ == "__main__":
    pack = json.load(open(PACK))
    out = {"task_id": pack["task_id"], "anchor": pack["anchor"]["name"], "results": {}}
    for p in ("EQUALITY", "SYMMETRY", "LINKAGE", "HIERARCHY"):
        t0 = time.perf_counter()
        v = run(pack, p)
        out["results"][p] = v
        print("  %-10s のべ%2d 2票以上%2d 既存%2d ★新規%2d PASS%2d  %.1f秒" % (
            p, v["候補(のべ)"], v["2票以上"], v["既に台帳に在る"], v["新しい"],
            sum(1 for r in v["rows"] if r.get("audit_result") == "PASS"), time.perf_counter() - t0))
    json.dump(out, open(os.path.join(D, "run_anchor_契約設計.json"), "w"), ensure_ascii=False)
