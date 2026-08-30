#!/usr/bin/env python3
"""ESDE 4視点を ★1視点ずつ Generator→機械→Auditor で 回す(★ITEM-2DER-EVO-0031)。

★追える形(Taka 指示)= candidate / relation perspective / target-source /
  reasoning / generator version / audit result を 1行に 持つ。
"""
import json, os, re, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perspectives_v0 as P

D = os.path.dirname(os.path.abspath(__file__))


def _call(prompt, max_tokens=512, seed=0):
    from twoder import detail_llm as DL
    return DL.call_for_detail(prompt, body=prompt, seed=seed, max_tokens=max_tokens)


def _json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _fmt(anchor):
    return {"anchor": anchor["anchor"], "parent": anchor.get("parent") or "(親は未登録)",
            "siblings": "\n".join("・" + s for s in anchor.get("siblings") or []) or "・(まだ無い)",
            "known": "\n".join("・" + s for s in anchor.get("known_relations") or []) or "・(まだ無い)",
            "task": (anchor.get("task_excerpt") or "(元TASKの記載なし)")[:600]}


def run(anchor, perspective, seeds=(0, 1, 2)):
    """★1視点だけ 回す(Taka 指示= Generator には 1回1視点)。"""
    gen, aud = P.PERSPECTIVES[perspective]
    f = _fmt(anchor)
    f["example"] = P.EXAMPLES[perspective]
    prompt = gen % f
    got, raw = [], []
    for s in seeds:
        r = _call(prompt, seed=s)
        o = _json(r.get("content") or "")
        raw.append({"seed": s, "tokens": r.get("completion_tokens"), "json": o is not None})
        a = (o or {}).get("answer")
        if isinstance(a, dict):
            a = [a]
        for x in (a or []):
            if isinstance(x, dict):
                got.append(x)
    # ★機械が 先に 見る(★LLM に 文字照合を させない= 実測で 0/6 だった)
    sib = set(anchor.get("siblings") or [])
    par = anchor.get("parent")
    rows, seen = [], {}
    for x in got:
        c = x.get("candidate") or x.get("upper")
        if not c:
            continue
        seen[c] = seen.get(c, 0) + 1
        rows.append({"candidate": c, "perspective": perspective,
                     "target": x.get("counterpart_of") or x.get("siblings") or anchor["anchor"],
                     "direction": x.get("direction"),
                     "reasoning": x.get("why"), "generator_version": P.VERSION,
                     "already_in_ledger": (c in sib or c == par)})
    for r in rows:
        r["votes"] = seen[r["candidate"]]
    # ★2票以上だけ 残す(ESDE 規律②)。★落とした物も 数える
    two = {r["candidate"]: r for r in rows if r["votes"] >= 2}
    dropped = sorted({r["candidate"] for r in rows if r["votes"] < 2})
    fresh = [r for r in two.values() if not r["already_in_ledger"]]
    # ★Auditor= ★機械が 通した物だけ 見せる(★1視点 専用の 基準)
    audited = {}
    if fresh:
        cand = "\n".join("%d. %s（%s）" % (i + 1, r["candidate"], r.get("reasoning") or "")
                         for i, r in enumerate(fresh))
        o = _json((_call(aud % dict(f, candidates=cand)).get("content") or ""))
        est = set((o or {}).get("established") or [])
        need = {x.get("n") for x in ((o or {}).get("needs_check") or []) if isinstance(x, dict)}
        for i, r in enumerate(fresh, 1):
            r["audit_result"] = ("PASS" if i in est else ("NEEDS_CHECK" if i in need else "UNJUDGED"))
        audited = {"json": o is not None, "established": len(est), "needs_check": len(need)}
    return {"anchor": anchor["anchor"], "perspective": perspective,
            "generator_version": P.VERSION, "raw": raw,
            "候補(のべ)": len(rows), "2票以上": len(two), "1票で落とした": len(dropped),
            "既に台帳に在る": sum(1 for r in two.values() if r["already_in_ledger"]),
            "新しい": len(fresh), "auditor": audited, "rows": fresh}


if __name__ == "__main__":
    anchor = json.load(open(sys.argv[1]))
    out = {}
    for p in ("EQUALITY", "SYMMETRY", "LINKAGE", "HIERARCHY"):
        t0 = time.perf_counter()
        out[p] = run(anchor, p)
        v = out[p]
        print("  %-10s のべ%2d 2票以上%2d 既存%2d ★新規%2d 監査PASS%2d  %.1f秒" % (
            p, v["候補(のべ)"], v["2票以上"], v["既に台帳に在る"], v["新しい"],
            sum(1 for r in v["rows"] if r.get("audit_result") == "PASS"),
            time.perf_counter() - t0))
    json.dump(out, open(os.path.join(D, "run_%s.json" % anchor["anchor"]), "w"), ensure_ascii=False)
