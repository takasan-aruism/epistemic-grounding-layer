#!/usr/bin/env python3
"""★T2 の 実測(★ITEM-2DER-EVO-0020)。"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule_v0 as R

P = "/home/takasan/egl/structure/"
SEEDS = ["FILE_EXTRACTION.jsonl", "FILE_EXTRACTION_S23.jsonl", "FILE_EXTRACTION_S47.jsonl"]


def load(f):
    d = {}
    for l in open(P + f):
        r = json.loads(l)
        if r.get("extract_status") == "OK":
            d[r["key"]] = r.get("lifecycle_signal")
    return d


def main():
    seeds = [load(f) for f in SEEDS]
    keys = sorted(set(seeds[0]) & set(seeds[1]) & set(seeds[2]))
    print("★対象= egl/structure/s2_extract.py:call(★T2 5件のうち Qwen が推論する 1件)")
    print("★測る欄= lifecycle_signal(★schema で 閉じた 5値。★他10欄は 自由記述 ∴ 対象外)")
    print("★分母= 3 seed に 共通で OK だった %d ファイル(seed7=%d S23=%d S47=%d)" % (
        len(keys), *[len(s) for s in seeds]))
    print()

    uni = [k for k in keys if seeds[0][k] == seeds[1][k] == seeds[2][k]]
    print("★① LLM の 自己一致(★temperature 0・seed だけ 変えた)")
    print("   3 seed 一致= %d/%d = %.1f%%  ／ 割れた= %d" % (
        len(uni), len(keys), 100.0 * len(uni) / len(keys), len(keys) - len(uni)))
    print("   ★∴ ★同じ器に 同じ物を 入れて ★半分は 違う答えが 返る")
    print()

    # ★道すじ= key は "repo/relative" 形式
    paths = {}
    for k in keys:
        repo, rel = k.split("/", 1)
        paths[k] = "/home/takasan/%s/%s" % (repo, rel)
    have = {k: p for k, p in paths.items() if os.path.exists(p)}
    print("★実物が 在る= %d/%d(★消えた ファイルは 測らない)" % (len(have), len(keys)))
    imp = R.importers(list(have.values()))

    det = {}
    for k, p in have.items():
        src = open(p, encoding="utf-8", errors="replace").read()
        det[k] = R.classify(p, src, imp.get(p, 0))[0]

    print()
    print("★② 決定論の 規則(5行)と ★LLM の 突き合わせ")
    u2 = [k for k in uni if k in det]
    agree_u = sum(1 for k in u2 if det[k] == seeds[0][k])
    print("   ・★LLM が 自分と 一致した %d件 での 一致= %d/%d = %.1f%%" % (
        len(u2), agree_u, len(u2), 100.0 * agree_u / len(u2)))
    sp = [k for k in keys if k in det and k not in uni]
    agree_any = sum(1 for k in sp if det[k] in {seeds[0][k], seeds[1][k], seeds[2][k]})
    print("   ・★LLM が 割れた %d件 で ★規則が どれか1つと 一致= %d/%d = %.1f%%" % (
        len(sp), agree_any, len(sp), 100.0 * agree_any / len(sp)))
    print("   ・★規則の 自己一致= 100%%(★作りで 保証・★同じ入力なら 同じ値)")
    print()
    print("★③ 値の 分布")
    print("   LLM(seed7)= %s" % dict(Counter(seeds[0][k] for k in have)))
    print("   ★規則    = %s" % dict(Counter(det.values())))
    print()
    print("★④ 一致しない 型(★上位5)")
    mis = Counter((seeds[0][k], det[k]) for k in u2 if det[k] != seeds[0][k])
    for (a, b), n in mis.most_common(5):
        print("   LLM=%-11s 規則=%-11s %d件" % (a, b, n))


if __name__ == "__main__":
    main()
