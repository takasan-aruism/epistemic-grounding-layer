#!/usr/bin/env python3
"""★意図が 明細に 登記されているかを 測る(★Taka 指示 2026-08-30)。

★文字の一致は 測らない= ★正しさの証拠に ならない(Taka 逐語)。
★測るのは ★『頼んだつもりの こと』が ★明細のどれかに 書かれているか。
★自己採点を 避ける形= ★偽の意図(本文に 書いていない こと)を 混ぜる。
  ★偽を『在る』と 言う器は ★信用できない ∴ ★判定器そのものを 同時に 測る。
"""
import json, os, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_r1 import _call, _parse_json
import corpus_v1 as C

D = os.path.dirname(os.path.abspath(__file__))

JUDGE = """あなたの仕事は、ある項目が明細のどれかに書かれているかを判定することです。

明細を読み、項目ごとに、その内容を述べている明細があるかを判定してください。
述べている明細がある項目は found に入れ、その明細の番号を書いてください。
述べている明細がない項目は not_found に入れてください。

出力は次の JSON だけにしてください。
{"found":[{"item":1,"detail_no":2}],"not_found":[3]}

明細:
---
%s
---

項目:
---
%s
---"""


def current_details(text):
    from twoder import requirement_structure as RS
    return [it.get("source_text") for it in (RS.structure(text) or []) if it.get("source_text")]


def llm_details(text, ver="v1"):
    P = __import__("prompts_%s" % ver)
    obj = _parse_json((_call(P.R1_GENERATOR % text).get("content") or ""))
    return [c.get("source_text") for c in ((obj or {}).get("candidates") or []) if c.get("source_text")]


def judge(details, items):
    d = "\n".join("%d. %s" % (i + 1, t) for i, t in enumerate(details)) or "(明細なし)"
    q = "\n".join("%d. %s" % (i + 1, t) for i, t in enumerate(items))
    obj = _parse_json((_call(JUDGE % (d, q), max_tokens=1500).get("content") or ""))
    if obj is None:
        return None
    found = {x.get("item") for x in (obj.get("found") or []) if isinstance(x, dict)}
    return found


def main(argv):
    which = argv[0] if argv else "current"
    res, T = {}, {"intent": 0, "hit": 0, "fake": 0, "fake_hit": 0, "judge_fail": 0}
    print("%-5s %-8s %-14s %-14s" % ("id", "明細数", "意図が在る", "★偽を在ると誤答"))
    for c in C.CASES:
        it = C.INTENTS[c["id"]]
        dets = current_details(c["text"]) if which == "current" else llm_details(c["text"])
        items = it["intents"] + it["distractors"]
        f = judge(dets, items)
        if f is None:
            T["judge_fail"] += 1
            res[c["id"]] = {"judge": "失敗"}
            print("%-5s %-8d ★判定器が JSON を返さない" % (c["id"], len(dets)))
            continue
        n = len(it["intents"])
        hit = {i for i in f if 1 <= i <= n}
        fake = {i for i in f if i > n}
        T["intent"] += n; T["hit"] += len(hit)
        T["fake"] += len(it["distractors"]); T["fake_hit"] += len(fake)
        res[c["id"]] = {"明細数": len(dets), "意図": n, "在った": len(hit),
                        "偽": len(it["distractors"]), "偽を在ると誤答": len(fake),
                        "落ちた意図": [it["intents"][i - 1] for i in range(1, n + 1) if i not in hit]}
        print("%-5s %-8d %-14s %-14s" % (c["id"], len(dets), "%d/%d" % (len(hit), n),
                                         "%d/%d" % (len(fake), len(it["distractors"]))))
    json.dump(res, open(os.path.join(D, "intent_%s.json" % which), "w"), ensure_ascii=False)
    print("\n★意図の登記(分母= 意図 %d件 / 偽 %d件 / TASK 10本) ― 対象= %s" % (T["intent"], T["fake"], which))
    print("   ★意図が 明細に 在った : %d/%d = %.0f%%" % (T["hit"], T["intent"], 100.0 * T["hit"] / T["intent"]))
    print("   ★偽を 在ると 誤答     : %d/%d = %.0f%%  (★0%% が 正しい)" % (
        T["fake_hit"], T["fake"], 100.0 * T["fake_hit"] / T["fake"]))
    print("   判定器が JSON を返さなかった: %d/10" % T["judge_fail"])


if __name__ == "__main__":
    main(sys.argv[1:])
