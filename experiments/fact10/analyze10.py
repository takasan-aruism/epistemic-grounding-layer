#!/usr/bin/env python3
"""★10テーマの FACT 出力を ★EVO-0054 の 受入3条件で 数える。

★受入(★Monitor が 書いた 逐語)=
  ①subject が 2種以下へ 潰れる回 = 0
  ②finish=stop の 完走 = 4/4
  ③主題が subject の 率 < 60%
★★私は ★4回ではなく ★10テーマ 1回ずつ 回す ∴ ①②は ★テーマ横断で 数える。
★鍵は Monitor の check_fact.py と 揃える(★facts / subject / id)。
"""
import collections, json, os, re, sys

D = "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad/fact"


def parse(txt):
    s = txt.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
    try:
        return json.loads(s), "OK"
    except Exception:
        # ★切れた場合= ★facts の 完結した 要素だけ 拾う(★0件と 混ぜない)
        got = re.findall(r'\{[^{}]*"subject"[^{}]*\}', s)
        rows = []
        for g in got:
            try:
                rows.append(json.loads(g))
            except Exception:
                pass
        return {"facts": rows}, "★部分回収(%d件)" % len(rows)


def main():
    cases = {c["id"]: c for c in json.load(open(D + "/cases.json"))}
    run = json.load(open(D + "/run10.json")) if os.path.exists(D + "/run10.json") else {}
    print("%-4s %-20s %-12s %6s %6s %7s %7s %s" % (
        "id", "テーマ", "型", "FACT", "subj種", "主題率", "finish", "解析"))
    rows = []
    for cid in sorted(cases, key=lambda x: int(x[1:])):
        p = "%s/out/%s.txt" % (D, cid)
        if not os.path.exists(p):
            print("%-4s %-20s ★未了" % (cid, cases[cid]["theme"][:20]))
            continue
        obj, st = parse(open(p, encoding="utf-8", errors="replace").read())
        facts = obj.get("facts") or []
        subs = [f.get("subject") for f in facts if isinstance(f, dict) and f.get("subject")]
        c = collections.Counter(subs)
        theme = cases[cid]["theme"]
        # ★主題率= ★主題の 語を 含む subject の 割合(★完全一致では 拾えない)
        main_n = sum(v for k, v in c.items() if theme[:3] in str(k))
        rate = 100.0 * main_n / len(subs) if subs else 0.0
        fin = (run.get(cid) or {}).get("finish")
        rows.append({"id": cid, "theme": theme, "type": cases[cid]["type"],
                     "facts": len(facts), "subj_kinds": len(c), "main_rate": round(rate, 1),
                     "finish": fin, "parse": st, "top": c.most_common(3)})
        print("%-4s %-20s %-12s %6d %6d %6.1f%% %7s %s" % (
            cid, theme[:20], cases[cid]["type"][:12], len(facts), len(c), rate, fin, st))
    if not rows:
        return
    json.dump(rows, open(D + "/analyze10.json", "w"), ensure_ascii=False)
    print()
    print("★★受入3条件(★分母 %d テーマ)" % len(rows))
    collapse = [r for r in rows if r["subj_kinds"] <= 2]
    print("  ①subject が 2種以下へ 潰れた = %d/%d %s" % (
        len(collapse), len(rows), [r["id"] for r in collapse] or ""))
    done = [r for r in rows if r["finish"] == "stop"]
    print("  ②finish=stop の 完走     = %d/%d %s" % (
        len(done), len(rows), [r["id"] for r in rows if r["finish"] != "stop"] or ""))
    over = [r for r in rows if r["main_rate"] >= 60]
    print("  ③主題率 60%% 以上         = %d/%d %s" % (
        len(over), len(rows), [(r["id"], r["main_rate"]) for r in over] or ""))
    ok = [r for r in rows if r["subj_kinds"] > 2 and r["finish"] == "stop" and r["main_rate"] < 60]
    print("  ★★3条件を 同時に 満たした = %d/%d %s" % (len(ok), len(rows), [r["id"] for r in ok]))


if __name__ == "__main__":
    main()
