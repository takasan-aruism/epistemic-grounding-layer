#!/usr/bin/env python3
"""★受入①②③を 民法で 実走して 数で 示す(★ITEM-2DER-EVO-0045)。"""
import os, re, sys, time
sys.path.insert(0, "/home/takasan")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chunk_v0 as C

SRC = os.environ.get("MINPO", "/tmp/claude-1000/-home-takasan/b2930a6c-e4f7-42f6-82da-6d48a6998fb7/scratchpad/minpo.txt")

# ★問い= Taka/RRI が 受入②に 書いた 例。★答え= 第七百九条を 含む 片が 返ること。
QUERY = "不法行為の損害賠償は"
ANSWER = "故意又は過失によって他人の権利"   # ★第七百九条の 条文本体(★一意)
DECOY = "第七百九条"                        # ★同じ語は ★目次にも 在る= ★囮
STOP = set("のはがをにでとへやもからまでよりについてに関するですますかどうなにいつどこ誰")


def terms(q):
    """★問いから 語を 取る(★決定論・★助詞を 落とすだけ)。"""
    out, buf = [], ""
    for ch in q:
        if ch in STOP or ch in "、。 　":
            if len(buf) >= 2:
                out.append(buf)
            buf = ""
        else:
            buf += ch
    if len(buf) >= 2:
        out.append(buf)
    return out


def score(text, hs, s, e, ts):
    """★片の 点= ★本文の 語数 ＋ ★見出しの道すじの 語数×3。

    ★見出しを 重く する 理由= ★実測で 第七百九条の 条文に ★『不法行為』の 語が 1つも 無い。
      ★その語は ★章の 見出し(第五章 不法行為)に しか 無い ∴ ★道すじを 見ないと 当たらない。
    """
    body = text[s:e]
    path = "／".join(C.path_of(hs, s))
    return sum(body.count(t) for t in ts) + 3 * sum(path.count(t) for t in ts), path


def main():
    text = open(SRC).read()
    hs = C.headings(text)
    print("★材料= %s" % SRC)
    print("  文字数= %d ／ 行数= %d ／ 見出し= %d" % (len(text), text.count("\n") + 1, len(hs)))
    print("  ★出所= e-Gov 法令API(129AC0000000089・XML)を 平文へ 展開")
    print("  ★RRI 実測の 222,670字は ★描画後の inner_text= ★別の鍵(★同じ法令・★取り方が違う)")
    print()

    # ---- 受入① 上限に 収まるか ----
    t0 = time.perf_counter()
    us = C.units(text)                      # ★梯子を 最後まで 降りた 自然な 単位
    pk = C.pack(us, C.LIMIT)                # ★上限まで 詰め直す
    sec = time.perf_counter() - t0
    sizes = [e - s for s, e, *_ in pk]
    print("★受入① 上限に 収まるか(★上限= %d字= BUDGET65536−骨組512−最小出力256−余白64)" % C.LIMIT)
    print("  ★自然な単位= %d件(最大 %d字) → ★詰め直した片= %d件" % (
        len(us), max(e - s for s, e, *_ in us), len(pk)))
    print("  ★片の字数= 最大 %d ／ 最小 %d ／ 平均 %d" % (max(sizes), min(sizes), sum(sizes) // len(sizes)))
    print("  ★★上限を超えた片= %d/%d 件" % (sum(1 for z in sizes if z > C.LIMIT), len(pk)))
    print("  (%.2f秒)" % sec)
    print()

    # ---- 受入② 問いの語で 絞れるか ----
    ts = terms(QUERY)
    print("★受入② 問いの語で 該当箇所に 絞れるか")
    print("  問い= 『%s』 → 取った語= %s" % (QUERY, ts))
    dp = [m.start() for m in re.finditer(DECOY, text)]
    print("  ★当てる先= 第七百九条の ★条文本体(『%s…』)" % ANSWER[:12])
    print("  ★★『%s』の 語だけで 当てると 外れる= ★%d箇所に 在り ★1つ目は 目次(pos %d)= ★囮" % (
        DECOY, len(dp), dp[0]))
    print("     (★私の 最初の 試験は これを 当てて ★間違った 道すじを 出した= ★計器の 欠陥・直した)")
    for name, spans in (("詰めた片", pk), ("自然な単位(条)", us)):
        rows = sorted(((score(text, hs, s, e, ts), (s, e)) for s, e, *_ in spans),
                      key=lambda r: -r[0][0])
        (pt, path), (s, e) = rows[0]
        hit = ANSWER in text[s:e]
        holder = [i for i, (a, b, *_) in enumerate(spans) if ANSWER in text[a:b]]
        rank = next((i for i, (sc, sp) in enumerate(rows, 1)
                     if ANSWER in text[sp[0]:sp[1]]), None)
        print("  ・%-14s 分母 %5d件 ／ 1位の点 %3d ／ ★1位が正解を含む= %s ／ ★正解の順位= %s/%d" % (
            name, len(spans), pt, hit, rank, len(spans)))
        print("      1位の道すじ= %s ／ %d字" % (path or "(無し)", e - s))
        if not hit and holder:
            a, b, *_ = spans[holder[0]]
            print("      ★正解が入っている片= %d字 ／ 道すじ= %s" % (
                b - a, "／".join(C.path_of(hs, a)) or "(無し)"))
    print()

    # ---- 受入③ 元の文に 戻せるか ----
    print("★受入③ 保存則(取得文 = 使った片 + 使わなかった残余)")
    for name, spans in (("詰めた片", pk), ("自然な単位", us)):
        r = C.check_conservation(text, spans)
        print("  ・%-10s 戻る=%s ／ 隙間=%d字 ／ 重なり=%d字 ／ ★落ちた=%d字 ／ %d字→%d字" % (
            name, r["★元の文に戻る"], r["★隙間の文字数"], r["★重なりの文字数"],
            r["★落ちた文字数"], r["元の文字数"], r["片をつないだ文字数"]))


if __name__ == "__main__":
    main()
