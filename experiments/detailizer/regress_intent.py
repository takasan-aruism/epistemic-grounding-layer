#!/usr/bin/env python3
"""★回帰試験を ★意図の登記で 回す(★ITEM-2DER-EVO-0037 受入⑨・★Taka 裁定 2026-09-01)。

★★Taka 逐語=『試験いらんでしょ。★文字の一致率みたって しょうもない』
  ∴ ★被覆率・追跡可能率・引用の原文一致は ★使わない。
  ∴ ★見るのは ★『頼んだ事が 明細に 在るか』だけ。

★★新しく 作らない= ★既存の run_intent.judge / current_details / llm_details を 呼ぶ。
★★対照を 必ず 付ける(★これが 無いと 器の 甘さと 区別できない)=
  ・★偽の意図(★本文に 書いていない 事)を 混ぜ ★『在る』と 言わないかを 見る。
  ★実測(2026-08-31)= 偽 0/20 = 0%。★これを 下回ったら 器が 壊れた 印。
"""
import json, os, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_intent import judge, current_details, llm_details
import corpus_v1 as C

D = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(D, "regress_intent_baseline.json")


def _one(c, which, ver):
    """★1件= ★明細を 作る → ★意図と偽を 混ぜて 判定させる。★件ごとに 独立 ∴ ★並列に できる。"""
    it = C.INTENTS[c["id"]]
    dets = current_details(c["text"]) if which == "current" else llm_details(c["text"], ver)
    items = it["intents"] + it["distractors"]
    f = judge(dets, items)
    n = len(it["intents"])
    if f is None:
        return {"id": c["id"], "落ちた": True, "意図": n, "偽": len(it["distractors"])}
    return {"id": c["id"], "落ちた": False, "意図": n, "偽": len(it["distractors"]),
            "在った": len({i for i in f if 1 <= i <= n}),
            "偽を在ると誤答": len({i for i in f if i > n})}


def measure(which="current", ver="v2", parallel=8):
    """★1周= 母集団10本の ★意図の登記率 と ★偽の誤答率。★正解は 作文者の 意図(★出所を 添える)。

    ★★並列= 8(★私の 実測 2026-08-30= 長い出力で 4→14.9s / ★8→7.9s / 16→12.4s)。
    ★★分母の鍵= ★意図 35(★作文者=私の意図表 corpus_v1.INTENTS) ／ ★偽 20。
      ★以前 報告した 38 は ★Qwen が 出した 意図表を 鍵に した 別の 数 ∴ ★混ぜない。
    """
    from twoder.detail_llm import map_bounded
    rows = map_bounded(lambda c: _one(c, which, ver), C.CASES, parallel=parallel)
    hit = sum(r.get("在った", 0) for r in rows)
    tot = sum(r["意図"] for r in rows if not r["落ちた"])
    fh = sum(r.get("偽を在ると誤答", 0) for r in rows)
    ft = sum(r["偽"] for r in rows if not r["落ちた"])
    fail = sum(1 for r in rows if r["落ちた"])
    return {"対象": which if which == "current" else "%s(%s)" % (which, ver),
            "意図が在った": "%d/%d" % (hit, tot),
            "登記率": round(100.0 * hit / tot, 1) if tot else 0.0,
            "★偽を在ると誤答": "%d/%d" % (fh, ft),
            "★誤答率": round(100.0 * fh / ft, 1) if ft else 0.0,
            "判定器が落ちた": fail, "件別": {r["id"]: r for r in rows},
            "★分母の鍵": "★作文者(私)の意図表 corpus_v1.INTENTS= 意図35 / 偽20 (★Qwen 作の 38 とは 別鍵)"}


def main(argv):
    which = "llm" if "--llm" in argv else "current"
    ver = "v1" if "--v1" in argv else "v2"
    t0 = time.perf_counter()
    now = measure(which, ver)
    now["秒"] = round(time.perf_counter() - t0, 1)
    print("★回帰試験(★意図の登記・★分母 10本)")
    print("  対象=%-8s ★意図が在った %-8s = %5.1f%%  ／ ★偽を在ると誤答 %-6s = %.1f%%  (%.0f秒)" % (
        now["対象"], now["意図が在った"], now["登記率"],
        now["★偽を在ると誤答"], now["★誤答率"], now["秒"]))
    if now["判定器が落ちた"]:
        print("  ★判定器が JSON を返さなかった: %d/10" % now["判定器が落ちた"])
    if "--save" in argv:
        base = json.load(open(BASE)) if os.path.exists(BASE) else {}
        base[now["対象"]] = now
        json.dump(base, open(BASE, "w"), ensure_ascii=False)
        print("\n★基準として 保存した(対象=%s)" % now["対象"])
        return
    if not os.path.exists(BASE):
        print("\n★基準が 無い= --save で 先に 作る")
        return
    old = json.load(open(BASE)).get(now["対象"])
    if not old:
        print("\n★この対象の 基準が 無い"); return
    d = now["登記率"] - old["登記率"]
    df = now["★誤答率"] - old["★誤答率"]
    print("\n★前回との 差")
    print("  登記率 %.1f%% → %.1f%% (%+.1fpt)" % (old["登記率"], now["登記率"], d))
    print("  ★誤答率 %.1f%% → %.1f%% (%+.1fpt)  ★上がったら 器が 壊れた 印" % (
        old["★誤答率"], now["★誤答率"], df))
    print("\n★判定: %s" % (
        "★★壊れた= 偽を 通し始めた" if df > 0 else
        ("★落ちた= 意図を 拾えなくなった" if d < 0 else "★前と 同じか 良い")))


if __name__ == "__main__":
    main(sys.argv[1:])
