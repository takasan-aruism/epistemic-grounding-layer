#!/usr/bin/env python3
"""★取得した外部文を Qwen が読める単位に 分解する(★ITEM-2DER-EVO-0045 ／ 担当 Inference Control)。

★★方針= ★決定論で 解く。★LLM は 使わない。
  ★理由= 切る位置は ★見出しと 改行で 決まる ∴ ★揺れる器を 挟む 必要が 無い
  (★私の 常設方針= ★まず 決定論で 解けるかを 問い、解けないなら 揺れを抑えた LLM)。

★★形は 2段=
  ①`units()`  ★いちばん細かい 自然な 単位まで 落とす(★編→章→節→款→条→段落→行→文)。
  ②`pack()`   ★隣どうしを ★上限まで 詰め直す。
  ∴ ★片は 上限に 収まり(①の受入)、★指し先は 条のまま 残る(②の受入)。

★★保存則(③の受入)は ★作りで 保証する=
  ★片は 全部 ★(start, end) の 区間。★start は 前の片の end と ★必ず 一致し、
  ★最初は 0・★最後は len(text) ∴ ★つなぐと 元の文に 戻る。
  ★『落ちた分』が 出ない= ★捨てる処理を 1つも 持たない。
"""
import re

# ★上限= twoder/detail_llm.py の 定数から 導いた 値(★手書きの数を 置かない ための 既定)。
#   BUDGET 65536 − 骨組 512 − 最小出力 256 − 余白 64 = 64704
try:
    from twoder import detail_llm as _D
    LIMIT = _D.BUDGET_TOKENS - _D.PROMPT_SKELETON_TOKENS - _D.MIN_OUTPUT_TOKENS - _D.SAFETY_MARGIN
except Exception:                                    # ★引けない時も 動く(★出所は 下の note に 残る)
    LIMIT = 64704

_K = "一二三四五六七八九十百千"

# ★梯子= ★強い順。★各段は『行頭に 現れる 見出し』の 形で 書く。
#   ★段の 名前を 付ける= ★どの段で 切れたかを ★片に 残す ため。
LADDER = [
    ("編",   re.compile(r"^第[%s]+編(?:　|\s|$)" % _K, re.M)),
    ("章",   re.compile(r"^第[%s]+章(?:　|\s|$)" % _K, re.M)),
    ("節",   re.compile(r"^第[%s]+節(?:　|\s|$)" % _K, re.M)),
    ("款",   re.compile(r"^第[%s]+款(?:　|\s|$)" % _K, re.M)),
    ("条",   re.compile(r"^第[%s]+条(?:の[%s]+)?(?:　|\s|$|　)" % (_K, _K), re.M)),
    ("見出し", re.compile(r"^#{1,6}\s", re.M)),        # ★法令以外(markdown)でも 効く 段
    ("段落",  re.compile(r"\n\s*\n")),
    ("行",   re.compile(r"\n")),
    ("文",   re.compile(r"(?<=。)")),
]


def _cuts(text, a, b, rx):
    """★区間 [a,b) の 中で ★境界に なる 位置を 返す(★a と b は 含めない)。"""
    out = []
    for m in rx.finditer(text, a, b):
        p = m.start()
        if a < p < b:
            out.append(p)
    return out


def units(text, limit=None, ladder=None):
    """★いちばん細かい 自然な 単位まで 落とす。-> [(start, end, 段の名前)]

    ★上限を 渡すと ★上限に 収まるまでだけ 落とす(★それ以上は 割らない)。
    ★上限を 渡さないと ★梯子を 最後まで 降りる= ★条まで 割れる。
    """
    lad = ladder or LADDER
    out = []

    def rec(a, b, lv, why):
        if a >= b:
            return
        if limit is not None and (b - a) <= limit:
            out.append((a, b, why)); return
        if lv >= len(lad):
            if limit is None:
                out.append((a, b, why)); return
            # ★梯子を 使い切った= ★字数で 割る(★それでも 区間は 隙間なく 並ぶ)
            p = a
            while p < b:
                q = min(p + limit, b)
                out.append((p, q, "字数")); p = q
            return
        name, rx = lad[lv]
        cs = _cuts(text, a, b, rx)
        if not cs:
            rec(a, b, lv + 1, why); return
        pts = [a] + cs + [b]
        for i in range(len(pts) - 1):
            rec(pts[i], pts[i + 1], lv + 1, name)

    rec(0, len(text), 0, "全体")
    return out


def pack(spans, limit=None):
    """★隣どうしを ★上限まで 詰め直す。-> [(start, end, [元の単位数])]

    ★隣接だけを 併せる ∴ ★区間は 隙間なく 並んだまま= ★保存則は 崩れない。
    """
    lim = LIMIT if limit is None else limit
    out = []
    for s, e, _w in spans:
        if out and (e - out[-1][0]) <= lim:
            out[-1] = (out[-1][0], e, out[-1][2] + 1)
        else:
            out.append((s, e, 1))
    return out


def headings(text, ladder=None):
    """★見出しの 出た 位置を 段ごとに 拾う(★片に 見出しの 道すじを 添える ため)。

    ★★これは ★本文には 混ぜない= ★保存則を 壊さない ため。★添えるのは ★脇の情報だけ。
    """
    lad = ladder or LADDER
    got = []
    for name, rx in lad[:6]:                          # ★見出しの段だけ(段落/行/文は 見出しでない)
        for m in rx.finditer(text):
            ln_end = text.find("\n", m.start())
            ln_end = len(text) if ln_end < 0 else ln_end
            got.append((m.start(), name, text[m.start():ln_end].strip()))
    got.sort()
    return got


def path_of(hs, pos, ladder=None):
    """★位置 pos より 前に 出た 見出しを 段ごとに 1つずつ 採る= ★その片の 道すじ。"""
    lad = ladder or LADDER
    order = [n for n, _ in lad[:6]]
    cur = {}
    for p, name, txt in hs:
        if p > pos:
            break
        cur[name] = txt
        for deeper in order[order.index(name) + 1:]:  # ★上の段が 変わったら 下の段は 捨てる
            cur.pop(deeper, None)
    return [cur[n] for n in order if n in cur]


def check_conservation(text, spans):
    """★保存則を 実際に 検算する。-> dict(★数で 返す・★『落ちた分』も 数で 返す)"""
    joined = "".join(text[s:e] for s, e, *_ in spans)
    gaps = sum(spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1))
    overlaps = sum(max(0, spans[i][1] - spans[i + 1][0]) for i in range(len(spans) - 1))
    return {
        "元の文字数": len(text),
        "片をつないだ文字数": len(joined),
        "★元の文に戻る": joined == text,
        "先頭が0": bool(spans) and spans[0][0] == 0,
        "末尾が末端": bool(spans) and spans[-1][1] == len(text),
        "★隙間の文字数": gaps,
        "★重なりの文字数": overlaps,
        "★落ちた文字数": len(text) - len(joined),
    }
