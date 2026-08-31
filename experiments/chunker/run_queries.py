#!/usr/bin/env python3
"""★受入②を ★問い10本＋対照3本で 測る(★ITEM-2DER-EVO-0045)。"""
import os, sys
sys.path.insert(0, "/home/takasan"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chunk_v0 as C, queries_v0 as Q
from run_minpo import terms, score, SRC

text = open(SRC).read()
hs = C.headings(text)
us = C.units(text)

# ★★門= ★錨が 本文に 無ければ ★先に 止める。
#   ★理由(★実測 2026-09-01)= ★私が 第793条の 錨を ★作文で 書き ★本文に 無かった
#     ∴ ★『順位 None』が 出て ★方法の 失敗に 見えた。★これは ★私の 錯誤。
#   ∴ ★以後は ★錨が 在ることを 先に 確かめてからでないと 数を 出さない。
_missing = [lbl for _q, a, lbl in Q.Q if a not in text]
if _missing:
    raise SystemExit("★止めた= 錨が 本文に 無い: %s(★方法でなく ★問いの表の 誤り)" % ",".join(_missing))
print("★門= 錨が 本文に 在る %d/%d 件(★無ければ 数を 出さない)" % (len(Q.Q), len(Q.Q)))
print("★受入② 問いの語で 絞れるか(★問い %d本 ／ ★対照 %d本 ／ 材料 %d字)" % (
    len(Q.Q), len(Q.CONTROL), len(text)))
print("★答えは 条文本体の 一意な 文字列で 指す(★条番号は 目次にも 在るので 使わない)")
print()
print("%-10s %6s %8s %8s %10s %12s" % ("詰める上限", "片数", "でたらめ", "★1位が当たり", "★上位3位以内", "★対照の誤当たり"))
for lim in (C.LIMIT, 16000, 4000, 1000):
    pk = C.pack(us, lim)
    n = len(pk)
    top1 = top3 = 0
    for q, anchor, _lbl in Q.Q:
        ts = terms(q)
        rows = sorted(((score(text, hs, s, e, ts)[0], (s, e)) for s, e, *_ in pk), key=lambda r: -r[0])
        rank = next((i for i, (sc, sp) in enumerate(rows, 1) if anchor in text[sp[0]:sp[1]]), None)
        if rank == 1: top1 += 1
        if rank and rank <= 3: top3 += 1
    # ★対照= 答えが 無い 問い。★1位の 点が 0 なら ★当てて いない(★正しく 白紙)
    bad = 0
    for q in Q.CONTROL:
        ts = terms(q)
        best = max(score(text, hs, s, e, ts)[0] for s, e, *_ in pk)
        if best > 0: bad += 1
    print("%-10s %6d %8s %8s %10s %12s" % (
        "%d字" % lim, n, "%.0f%%" % (100.0 / n),
        "%d/%d" % (top1, len(Q.Q)), "%d/%d" % (top3, len(Q.Q)), "%d/%d" % (bad, len(Q.CONTROL))))
print()
print("★でたらめ= 1/片数(★この線を 超えて 初めて 効いたと 言える)")
print("★対照の誤当たり= ★この文に 答えが 無い 問いで ★点が 付いた 数(★0 が 正しい)")
