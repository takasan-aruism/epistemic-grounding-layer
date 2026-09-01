#!/usr/bin/env python3
"""★『値が閉じているのに schema で縛っていない』を 直すと どうなるかを 実測(★EVO-0020 T4)。

★★対象= `egl/structure/s_intent_probe_proto.py`(★T4 21件のうち ★値が閉じている 4件の1つ)。
★★対照= ★同じ prompt・同じ設問・同じ seed で ★schema を 付けた腕と 付けない腕。
  ★付けない腕は ★その面の 既存の 呼び方を そのまま 使う(★私が 書き換えない)。
★★測る= ①enum の 外に 出た 率 ②3 seed の 一致率 ③JSON が 取れた 率。

★★既存の 部品を 使う= prompt も 設問も 判定も ★向こうの module から 借りる(★作り直さない)。
"""
import json, os, sys, urllib.request
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, "/home/takasan/egl/structure")
sys.path.insert(0, "/home/takasan")
import s_intent_probe_proto as P
from twoder.detail_llm import map_bounded

MENU = P.RUN_CONFIGS[0][1]
THINK = False          # ★LLMK-0010= thinking は 予算そのもの ∴ 両腕とも 切る
MAXTOK = 512

SCHEMA = {"type": "object", "properties":
          dict([(ax, {"type": "string", "enum": list(vals)}) for ax, vals in P.AXES.items()] +
               [("strategy", {"type": "string", "enum": list(P.STRATEGIES)})]),
          "required": list(P.AXES) + ["strategy"], "additionalProperties": False}


def call(prompt, seed, with_schema, temp=0.7):
    body = {"model": P.MODEL, "messages": [{"role": "user", "content": prompt}],
            "seed": seed, "temperature": temp, "max_tokens": MAXTOK,
            "chat_template_kwargs": {"enable_thinking": THINK}}
    if with_schema:
        # ★実測(s2_extract の NOTE)= guided_json は 黙って 無視される。★効くのは response_format
        body["response_format"] = {"type": "json_schema", "json_schema":
                                   {"name": "intent_axes", "schema": SCHEMA, "strict": True}}
    req = urllib.request.Request(P.ENDPOINT, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        out = json.load(r)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason")


def main():
    # ★腕= (schema 有無) × (temperature)。★向こうの既定は 0.7 ∴ ★それを 基準に 置く
    ARMS = [(False, 0.7), (True, 0.7), (False, 0.0), (True, 0.0)]
    jobs = [(fx, s, w, t) for (w, t) in ARMS for fx in P.FIXTURES for s in P.SEEDS]
    print("★対照実験= 設問 %d本 × seed %d × 腕4 = %d回(★並列8)" % (
        len(P.FIXTURES), len(P.SEEDS), len(jobs)))

    def one(j):
        fx, s, w, t = j
        try:
            raw, fr = call(P._build_prompt(MENU, fx), s, w, t)
        except Exception as e:
            return {"fx": fx["id"], "seed": s, "schema": w, "temp": t,
                    "verdict": "ERROR", "err": repr(e)[:80]}
        parsed, verdict = P.parse_output(raw, fr)
        return {"fx": fx["id"], "seed": s, "schema": w, "temp": t, "verdict": verdict,
                "parsed": parsed, "finish": fr}

    rows = map_bounded(one, jobs, parallel=8)
    print()
    print("%-18s %6s %10s %12s %12s" % ("腕", "回数", "★OK", "★enum逸脱", "★3seed一致"))
    for (w, t) in ARMS:
        g = [r for r in rows if r["schema"] is w and r["temp"] == t]
        ok = sum(1 for r in g if r["verdict"] == "OK")
        de = sum(1 for r in g if r["verdict"] == "DIVERGE_ENUM")
        er = sum(1 for r in g if r["verdict"] == "ERROR")
        agree = tot = 0
        for fx in P.FIXTURES:
            vs = [r["parsed"] for r in g if r["fx"] == fx["id"] and r["verdict"] == "OK"]
            if len(vs) == len(P.SEEDS):
                tot += 1
                if all(v == vs[0] for v in vs):
                    agree += 1
        print("%-18s %6d %10s %12s %12s" % (
            ("schema無" if not w else "★schema有") + " temp=%.1f" % t, len(g),
            "%d/%d" % (ok, len(g)), "%d/%d" % (de, len(g)),
            "%d/%d" % (agree, tot) if tot else "測れない"))
        if er:
            print("           ★口が落ちた %d回= %s" % (er, [r.get("err") for r in g if r["verdict"] == "ERROR"][:1]))
    print()
    print("★★分母の鍵= 設問は 向こうの FIXTURES ／ 判定は 向こうの parse_output(★私が 作っていない)")
    print("★★3seed一致は ★3回とも OK だった 設問だけを 分母にした(★取れなかった 回を 一致に 数えない)")


if __name__ == "__main__":
    main()
