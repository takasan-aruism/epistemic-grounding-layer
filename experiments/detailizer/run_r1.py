#!/usr/bin/env python3
"""Rotation 1 を 母集団で 走らせ ★機械で 検算する(★ITEM-2DER-EVO-0037)。

★責務の分離(Taka 指示 §11)= ★LLM が 意味を 判断し ★機械が 保存則を 検算する。
★使い方: run_r1.py <prompt_version> [--limit N]
"""
import json, os, re, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

POP = "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad/detail_pop.json"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _call(prompt, max_tokens=4096):
    """★:8005 を 実走。★thinking は 切る(★LLMK-0010 の 実測)。"""
    from twoder.runtime_supervisor import qwen_raw_call as Q
    return Q(prompt, max_tokens=max_tokens, seed=0, enable_thinking=False, timeout=300)


def _parse_json(text):
    """★返りから JSON を 取り出す。★取れなければ None(★捏造しない)。"""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def mechanical_check(goal, cands):
    """★決定論の 検算。★LLM に 点数を 付けさせない(Taka 指示 §11)。"""
    # ★★v1 から= ★位置を LLM に 出させない ∴ ★機械が 決める(★重なりを 避けて 順に 探す)。
    n = len(goal)
    rows, covered = [], bytearray(n)
    cursor = 0
    for c in cands:
        if c.get("start") is None and c.get("source_text"):
            t = c["source_text"]
            i = goal.find(t, cursor)
            if i < 0:
                i = goal.find(t)                  # ★前に 戻ってでも 探す(★順序は 保証しない)
            if i >= 0:
                c["start"], c["end"] = i, i + len(t)
                cursor = i + len(t)
        s, e = c.get("start"), c.get("end")
        r = {"candidate_id": c.get("candidate_id"), "in_range": False,
             "text_matches": False, "start": s, "end": e}
        if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= n:
            r["in_range"] = True
            r["text_matches"] = (goal[s:e] == (c.get("source_text") or ""))
            for j in range(s, e):
                covered[j] = 1
        rows.append(r)
    ids = [c.get("candidate_id") for c in cands]
    return {"候補": len(cands), "範囲内": sum(1 for r in rows if r["in_range"]),
            "原文と一致": sum(1 for r in rows if r["text_matches"]),
            "id重複": len(ids) - len(set(ids)),
            "被覆文字": sum(covered), "原文文字": n,
            "被覆率": round(100.0 * sum(covered) / n, 1) if n else 0.0,
            "行": rows}


def main(argv):
    ver = argv[0] if argv else "v0"
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
    P = __import__("prompts_%s" % ver)
    pop = json.load(open(POP))
    tids = sorted(pop)[:limit] if limit else sorted(pop)
    results = {}
    for tid in tids:
        goal = pop[tid]["goal"]
        if not goal:
            results[tid] = {"skip": "goal が 空"}
            continue
        t0 = time.perf_counter()
        r = _call(P.R1_GENERATOR % goal)
        obj = _parse_json(r.get("content") or "")
        cands = (obj or {}).get("candidates") or []
        results[tid] = {"秒": round(time.perf_counter() - t0, 1),
                        "tokens": r.get("completion_tokens"),
                        "json取れた": obj is not None,
                        "finish": r.get("finish_reason"),
                        "候補": cands, "検算": mechanical_check(goal, cands)}
        m = results[tid]["検算"]
        print("  %-24s 候補%2d 範囲内%2d 一致%2d 被覆%5.1f%% %5.1f秒 %s" % (
            tid, m["候補"], m["範囲内"], m["原文と一致"], m["被覆率"],
            results[tid]["秒"], "" if obj is not None else "★JSON 取れず"))
    path = os.path.join(OUT_DIR, "r1_%s.json" % ver)
    json.dump(results, open(path, "w"), ensure_ascii=False)
    ok = [v for v in results.values() if "検算" in v]
    if ok:
        import statistics
        cov = [v["検算"]["被覆率"] for v in ok]
        print("\n★R1 %s (分母 %d TASK)" % (ver, len(ok)))
        print("   被覆率 中央値 %.1f%% ／ 平均 %.1f%%" % (statistics.median(cov), statistics.mean(cov)))
        print("   JSON 取れた %d/%d ／ 範囲内 %d/%d ／ 原文と一致 %d/%d" % (
            sum(1 for v in ok if v["json取れた"]), len(ok),
            sum(v["検算"]["範囲内"] for v in ok), sum(v["検算"]["候補"] for v in ok),
            sum(v["検算"]["原文と一致"] for v in ok), sum(v["検算"]["候補"] for v in ok)))
    print("★書いた:", path)


if __name__ == "__main__":
    main(sys.argv[1:])
