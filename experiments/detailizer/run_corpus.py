#!/usr/bin/env python3
"""試験母集団10本で ★現行(決定論)と ★LLM(R1+Audit)を 同じ分母で 比べる(★ITEM-2DER-EVO-0037)。"""
import json, os, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_r1 import _call, _parse_json, mechanical_check
import corpus_v1 as C

D = os.path.dirname(os.path.abspath(__file__))


def baseline(text):
    """★現行の 明細生成を そのまま 当てる(★写さない= 本物を 呼ぶ)。"""
    from twoder import requirement_structure as RS
    # ★★2026-08-30 直した= ★返りは list で ★本文の欄は `source_text`。
    #   ★前は `.get("items")` と `.get("text")` で 引いて ★全件 0件 と 出していた= ★鍵違い。
    #   ★0件を そのまま 報告しかけた(★今日 何度も 踏んだ型)。
    return [it.get("source_text") for it in (RS.structure(text) or []) if it.get("source_text")]


def cover(text, pieces):
    n = len(text); cv = bytearray(n)
    for p in pieces:
        i = text.find(p.strip())
        if i >= 0:
            for j in range(i, min(n, i + len(p.strip()))):
                cv[j] = 1
    return round(100.0 * sum(cv) / n, 1) if n else 0.0


def main(argv):
    ver = argv[0] if argv else "v1"
    P = __import__("prompts_%s" % ver)
    rows, res = [], {}
    print("%-5s %-22s %5s %5s %5s %6s %6s" % ("id", "種別", "期待", "現行", "LLM", "現行%", "LLM%"))
    for c in C.CASES:
        b = baseline(c["text"])
        t0 = time.perf_counter()
        r = _call(P.R1_GENERATOR % c["text"])
        obj = _parse_json(r.get("content") or "")
        cands = (obj or {}).get("candidates") or []
        m = mechanical_check(c["text"], cands)
        res[c["id"]] = {"期待": c["expected_details"], "現行件数": len(b), "LLM件数": len(cands),
                        "現行被覆": cover(c["text"], b), "LLM被覆": m["被覆率"],
                        "原文と一致": m["原文と一致"], "候補": cands, "秒": round(time.perf_counter() - t0, 1)}
        v = res[c["id"]]
        print("%-5s %-22s %5d %5d %5d %5.1f%% %5.1f%%" % (
            c["id"], c["kind"][:22], v["期待"], v["現行件数"], v["LLM件数"], v["現行被覆"], v["LLM被覆"]))
        rows.append(v)
    json.dump(res, open(os.path.join(D, "corpus_%s.json" % ver), "w"), ensure_ascii=False)
    import statistics
    print("\n★母集団10本(分母10)")
    print("   被覆率 中央値: 現行 %.1f%% ／ LLM %.1f%%" % (
        statistics.median([r["現行被覆"] for r in rows]), statistics.median([r["LLM被覆"] for r in rows])))
    print("   件数の 合計  : 期待 %d ／ 現行 %d ／ LLM %d" % (
        sum(r["期待"] for r in rows), sum(r["現行件数"] for r in rows), sum(r["LLM件数"] for r in rows)))
    print("   原文と一致   : %d/%d" % (sum(r["原文と一致"] for r in rows), sum(r["LLM件数"] for r in rows)))
    print("   ★件数が 期待と 一致: 現行 %d/10 ／ LLM %d/10" % (
        sum(1 for r in rows if r["現行件数"] == r["期待"]), sum(1 for r in rows if r["LLM件数"] == r["期待"])))


if __name__ == "__main__":
    main(sys.argv[1:])
