#!/usr/bin/env python3
"""★残りを ★並列で 回す(★私が 自分で 測った 推奨8 を 自分で 使う)。★ITEM-2DER-EVO-0054。

★私の 誤り= ★昨日 EVO-0038 で『長い出力は 並列8 が 最速(4→8 +47% / 8→16 -57%)』と
  ★自分で 実測して 仕様に 書き、★detail_llm.map_bounded まで 用意しながら、
  ★今回 for ループの 直列で 回した。★道具が 手元に 在るのに 使わなかった。
"""
import json, os, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run10 import run                      # ★同じ呼び方を 使う(★写さない)
from twoder import detail_llm as DL

D = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    cases = json.load(open(D + "/cases.json"))
    todo = [c for c in cases if not os.path.exists("%s/out/%s.txt" % (D, c["id"]))]
    lim = 16464
    print("★残り %d件を ★並列 %d で 回す" % (len(todo), DL.RECOMMENDED_PARALLEL))
    t0 = time.time()

    def one(c):
        src = open("%s/src/%s.txt" % (D, c["id"]), encoding="utf-8", errors="replace").read()[:lim]
        r = run(c["id"], src)
        r["theme"] = c["theme"]; r["type"] = c["type"]; r["src_chars"] = len(src)
        print("  %-4s %-20s %-10s %5.0f秒 出力%6d字" % (
            c["id"], c["theme"][:20], r["finish"], r["sec"], r["chars"]))
        return (c["id"], r)

    out = DL.map_bounded(one, todo)
    el = time.time() - t0
    res = json.load(open(D + "/run10.json")) if os.path.exists(D + "/run10.json") else {}
    for x in out:
        if x:
            res[x[0]] = x[1]
    json.dump(res, open(D + "/run10.json", "w"), ensure_ascii=False)
    print("\n★並列 %d件= ★合計 %.0f秒(★壁時計)" % (len(todo), el))
    print("★直列なら 1件 %.0f秒 × %d = %.0f秒 だった見込み" % (
        max((x[1]["sec"] for x in out if x), default=0), len(todo),
        sum(x[1]["sec"] for x in out if x)))
