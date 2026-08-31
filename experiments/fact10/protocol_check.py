#!/usr/bin/env python3
"""★プロトコルの 定義と 実態の ミスマッチを 検出する(★Taka 指示 2026-09-01)。

★Taka 逐語=『全部を登録できるのが正しい答えではない。
  ★プロトコルの定義と実態のミスマッチを検出する方が重要』
★∴ ★subj率は 使わない。★『約束したのに 守られていない』所だけを 数える。

★定義(★プロンプトの 逐語から)= ★機械で 検算できる ものだけ 拾う=
  D1 source_basis は SOURCE内の 記述を ★そのまま引用する
  D2 FACTへ 変換しなかった 記述は ★すべて residual に 残す
  D3 出力は ★facts と residual の 2つだけ
  D4 object_or_value は ★一つの値だけ(★説明文を 入れない)
  D5 context は ★成立範囲だけ(★不要なら null)
  D6 id は F001 形式
  D7 ★すべての語が SOURCE に 在る(★subject が SOURCE に 在るか で 見る)
"""
import collections, json, os, re, sys

D = "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad/fact"


def parse(txt):
    s = txt.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
    try:
        return json.loads(s), True
    except Exception:
        rows = []
        for g in re.findall(r'\{[^{}]*"subject"[^{}]*\}', s):
            try:
                rows.append(json.loads(g))
            except Exception:
                pass
        res = []
        for g in re.findall(r'\{[^{}]*"reason"[^{}]*\}', s):
            try:
                res.append(json.loads(g))
            except Exception:
                pass
        return {"facts": rows, "residual": res}, False


def check(cid, src):
    obj, whole = parse(open("%s/out/%s.txt" % (D, cid), encoding="utf-8", errors="replace").read())
    facts = [f for f in (obj.get("facts") or []) if isinstance(f, dict)]
    resid = [r for r in (obj.get("residual") or []) if isinstance(r, dict)]
    n = len(facts)
    if not n:
        return None
    norm = re.sub(r"\s+", "", src)

    def insrc(v):
        return re.sub(r"\s+", "", str(v or "")) in norm
    d1 = sum(1 for f in facts if f.get("source_basis") and insrc(f["source_basis"]))
    d4 = sum(1 for f in facts if len(str(f.get("object_or_value") or "")) > 40)   # ★説明文の疑い
    d5 = sum(1 for f in facts if f.get("context") and len(str(f["context"])) > 60)
    d6 = sum(1 for f in facts if re.fullmatch(r"F\d{3,}", str(f.get("id") or "")))
    d7 = sum(1 for f in facts if insrc(f.get("subject")))
    extra = [k for k in obj if k not in ("facts", "residual")] if whole else []
    return {"id": cid, "facts": n, "residual": len(resid), "whole_json": whole,
            "D1_引用が原文に在る": (d1, n), "D3_余分な鍵": extra,
            "D4_値が40字超": (d4, n), "D5_contextが60字超": (d5, n),
            "D6_id形式": (d6, n), "D7_subjectが原文に在る": (d7, n)}


if __name__ == "__main__":
    cases = {c["id"]: c for c in json.load(open(D + "/cases.json"))}
    rows = []
    print("%-4s %-18s %5s %5s %-9s %-9s %-9s %-9s %s" % (
        "id", "テーマ", "FACT", "残余", "D1引用", "D7主語", "D4値超", "D6 id", "D3余分"))
    for cid in ["T%d" % i for i in range(1, 11)]:
        src = open("%s/src/%s.txt" % (D, cid), encoding="utf-8", errors="replace").read()[:16464]
        r = check(cid, src)
        if not r:
            continue
        rows.append(r)
        f = lambda t: "%d/%d" % t
        print("%-4s %-18s %5d %5d %-9s %-9s %-9s %-9s %s" % (
            cid, cases[cid]["theme"][:18], r["facts"], r["residual"],
            f(r["D1_引用が原文に在る"]), f(r["D7_subjectが原文に在る"]),
            f(r["D4_値が40字超"]), f(r["D6_id形式"]), r["D3_余分な鍵"] or "無"))
    json.dump(rows, open(D + "/protocol.json", "w"), ensure_ascii=False)
    T = lambda k: (sum(r[k][0] for r in rows), sum(r[k][1] for r in rows))
    print()
    print("★★定義と実態(分母= FACT %d件 / %d テーマ)" % (sum(r["facts"] for r in rows), len(rows)))
    for k in ("D1_引用が原文に在る", "D7_subjectが原文に在る", "D6_id形式"):
        a, b = T(k)
        print("  %-24s %d/%d = %.0f%%" % (k, a, b, 100.0 * a / b))
    for k in ("D4_値が40字超", "D5_contextが60字超"):
        a, b = T(k)
        print("  %-24s %d/%d = %.0f%%  (★0%% が 定義どおり)" % (k, a, b, 100.0 * a / b))
    print("  %-24s %d/%d テーマ" % ("D2_residual が 0件",
                                    sum(1 for r in rows if r["residual"] == 0), len(rows)))
