#!/usr/bin/env python3
"""ESDE Phase1 8段を 1文書で 回す(★ITEM-2DER-EVO-0052 / 設計は ESDE)。

★受入= ①8段とも Generator+Auditor が動く ②切れたら『切れた』を欄に出す
       ③2票以上/1票落とし/監査を件数で ④STEP7 は空を空として返す
       ⑤9項目を数で ⑥★台帳へは書かない。
"""
import json, os, re, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import steps_v0 as S

D = os.path.dirname(os.path.abspath(__file__))


def _call(prompt, seed=0):
    from twoder import detail_llm as DL
    return DL.call_for_detail(prompt, body=prompt, seed=seed, max_tokens=S.MAX_TOKENS)


def _parse(r):
    """★返り→(obj, 状態)。★切れたら『切れた』を 返す(★0件と 混ぜない= 受入②)。"""
    c = r.get("content") or ""
    fin = r.get("finish_reason")
    m = re.search(r"\{.*\}", c, re.S)
    if m:
        try:
            return json.loads(m.group(0)), ("OK" if fin != "length" else "TRUNCATED_BUT_PARSED")
        except Exception:
            pass
    return None, ("★TRUNCATED(finish=length)" if fin == "length" else "★PARSE_FAILED(finish=%s)" % fin)


def _key(x):
    if not isinstance(x, dict):
        return str(x)
    for k in ("existence", "axis_name", "event"):
        if x.get(k):
            return str(x[k])
    return "|".join(str(x.get(k, "")) for k in ("a", "b", "upper", "lower", "source", "target"))


def run_step(doc, step, prev=None, seeds=(0, 1, 2)):
    gen, aud = S.STEPS[step]
    f = {"doc": doc, "cand": json.dumps(prev or [], ensure_ascii=False)[:1500]}
    votes, states, toks = {}, [], []
    for sd in seeds:
        t0 = time.perf_counter()
        r = _call(gen % f, seed=sd)
        o, st = _parse(r)
        states.append(st); toks.append(r.get("completion_tokens"))
        a = (o or {}).get("answer")
        if isinstance(a, dict):
            a = [a]
        for x in (a or []):
            votes[_key(x)] = votes.get(_key(x), [0, x])
            votes[_key(x)][0] += 1
    two = [v[1] for v in votes.values() if v[0] >= 2]
    one = [v[1] for v in votes.values() if v[0] == 1]
    # ★機械が 見る= source_quote が 原文に 在るか(★LLM に 聞かない)
    quoted = sum(1 for x in two if isinstance(x, dict) and x.get("source_quote")
                 and x["source_quote"] in doc)
    audit = {"通した": 0, "要確認": 0, "却下": 0, "状態": None}
    if two:
        cand = "\n".join("%d. %s" % (i + 1, json.dumps(x, ensure_ascii=False)[:200])
                         for i, x in enumerate(two))
        o, st = _parse(_call(aud % {"doc": doc, "cand": cand}))
        audit["状態"] = st
        a = (o or {}).get("answer")
        if isinstance(a, dict):
            a = [a]
        for x in (a or []):
            v = (x or {}).get("verdict")
            if v == "PASS":
                audit["通した"] += 1
            elif v == "NEEDS_CHECK":
                audit["要確認"] += 1
            elif v == "REJECT":
                audit["却下"] += 1
    return {"step": step, "generator_version": S.VERSION,
            "seed別の状態": states, "tokens": toks,
            "★切れた回数": sum(1 for s in states if "TRUNCATED" in s),
            "2票以上": len(two), "1票で落とした": len(one),
            "引用が原文に在る": quoted, "監査": audit, "rows": two}


def main(path):
    doc = open(path, encoding="utf-8").read()
    out = {"doc": os.path.basename(path), "chars": len(doc), "results": {}}
    prev = None
    for st in S.ORDER:
        t0 = time.perf_counter()
        v = run_step(doc, st, prev=prev)
        out["results"][st] = v
        if st == "STEP7_TRANSFORMATIVE":
            prev = v["rows"]
        a = v["監査"]
        print("  %-24s 2票%2d 落%2d 引用%2d 監査 通%2d 要%2d 却%2d ★切れ%d  %.1f秒" % (
            st, v["2票以上"], v["1票で落とした"], v["引用が原文に在る"],
            a["通した"], a["要確認"], a["却下"], v["★切れた回数"], time.perf_counter() - t0))
    json.dump(out, open(os.path.join(D, "phase1_%s.json" % os.path.basename(path)[:24]), "w"),
              ensure_ascii=False)
    tot = sum(v["★切れた回数"] for v in out["results"].values())
    print("\n★⑨返りが切れた回数の合計= %d / %d回(8段 × 3seed)" % (tot, 8 * 3))
    print("★④STEP7 が 空を 空として 返せたか= %s" % (
        "★空(切れていない)" if out["results"]["STEP7_TRANSFORMATIVE"]["2票以上"] == 0
        and out["results"]["STEP7_TRANSFORMATIVE"]["★切れた回数"] == 0 else "★空ではない/切れた"))


if __name__ == "__main__":
    main(sys.argv[1])
