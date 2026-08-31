#!/usr/bin/env python3
"""[Claude実装/Topology] 2026-08-30 — ★外部から 情報を 取る 口(★レベル1 だけ)。★ITEM-2DER-EVO-0044。

★★これは 本線では ありません= ★front door にも 巡回にも 繋いでいません(★Taka 指示 逐語=
  『成果物としてClaudeが叩けば情報が取得できる状態を作る（この時点で本線に接続する必要はない）』)。

★★使い方=
    python3 egl/experiments/fetch/fetch1.py <種類> <対象> [--out ファイル] [--max N]
    python3 egl/experiments/fetch/fetch1.py --table          ★網羅表(★取れる物・システム・形式・レベル)
    python3 egl/experiments/fetch/fetch1.py --selftest       ★レベル1 の 全種類を 実走して 数を 出す

★★種類(★レベル1= ★2026-08-30 に この機械で 実走して 取れた 物 だけ)=
    auto     … URL から 判定して 下の どれかへ 回す
    web      … HTML → 本文テキスト        (★実測 ja.wikipedia 徳川家康 115,553字)
    render   … 描画して テキスト           (★実測 e-Gov 憲法 800B→11,957字 / 2.1秒)
    pdf      … PDF → テキスト              (★実測 arXiv 1706.03762 40,074字)
    json     … JSON/Atom の API            (★実測 Wikipedia REST 2,410B / GitHub API 6,617B)
    rss      … RSS/Atom の 見出し          (★実測 Yahoo topics 3,118B)
    search   … 検索の 結果一覧             (★実測 DuckDuckGo html 10件・鍵 不要)
    youtube  … 題名・説明・字幕の一覧      (★実測 題名と説明は 取れる。★字幕の本体は レベル2)
    xprofile … X の プロフィール欄         (★実測 名前/投稿数/追随者/自己紹介。★投稿本文は レベル3)
    file     … 生のまま 保存(画像など)     (★実測 wikimedia jpeg 9,022B)

★★返り= ★JSON 1件。★必ず 入る 欄= ok / kind / target / sec。
  ★取れた ときだけ= status / content_type / bytes / chars / preview / out。
  ★取れない ときだけ= error(★型と 文の 先頭)。★★『取れた』と『使える』を 分ける=
    ★`chars` が 本文の 字数。★`bytes` が 大きくても `chars` が 0 の ことが ある
    (★実測= YouTube の HTML 1,376,037B → 本文 0字= ★中身は JS の 中)。

★★依存は ★この機械に 在る 物 だけ(★2026-08-30 実測)= urllib(標準) / bs4 / lxml /
  feedparser / playwright / pdftotext(CLI)。★入れないと 動かない 物は 使っていません。
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")
TIMEOUT = 30
MAX_BYTES = 8_000_000


# ── 網羅表(★Taka 指示の ①取れる物 ②システム ③形式 ④レベル) ────────────────
#   ★レベルの 決め方(★推測でなく 実走の 結果)=
#     1 … ★この機械の いまの 道具だけで ★認証なしで ★実際に 取れた
#     2 … ★道具の 追加 か 鍵の 取得 が 要る(★技術上の 問題)
#     3 … ★ログイン・契約・規約 が 要る(★セキュリティ面の 課題)
TABLE = [
    # (システム, 取れる物, 形式, レベル, 実測)
    ("一般WEB(HTML)",      "本文",          "テキスト", 1, "ja.wikipedia 徳川家康 1,643,086B→本文 115,553字"),
    ("SPA/法令(描画)",     "本文",          "テキスト", 1, "e-Gov 憲法 静的800B(10字)→描画後 11,957字 / 2.1秒"),
    ("PDF",                "本文",          "テキスト", 1, "arXiv 1706.03762 2,215,244B→40,074字(pdftotext)"),
    ("プレーンテキスト",   "本文",          "テキスト", 1, "gutenberg 11-0.txt 151,191B"),
    ("CSV",                "表",            "テキスト", 1, "datasets/gdp 562,767B"),
    ("JSON API",           "構造データ",    "テキスト", 1, "Wikipedia REST 2,410B / GitHub API 6,617B"),
    ("Atom/RSS",           "見出し",        "テキスト", 1, "arXiv API 4,557B / Yahoo topics 3,118B"),
    ("検索(DuckDuckGo)",   "題名+URL",      "テキスト", 1, "★訂正= html面は12件ほどでCAPTCHA(202)。ddgs 経由なら10/10・各20件"),
    ("YouTube",            "題名・説明",    "テキスト", 1, "HTML の JS から 題名と shortDescription を 取れた"),
    ("画像",               "画像そのもの",  "画像",     1, "wikimedia Example.jpg 9,022B"),
    ("X(プロフィール)",    "名前/数/紹介",  "テキスト", 1, "静的HTML 292,877B→2,178字(名前・投稿数・追随者)"),
    ("YouTube(字幕)",      "字幕本文",      "テキスト", 2, "字幕6本の 一覧は 取れる が 本体の 取得は 0バイト"),
    ("YouTube(音声/動画)", "音声・動画",    "音声/動画", 2, "yt-dlp が 無い(★ffmpeg は 在る)"),
    ("音声→文字",         "書き起こし",    "音声",     2, "whisper 系が 1つも 入っていない"),
    ("画像→文字(OCR)",    "文字",          "画像",     2, "tesseract も pytesseract も 無い"),
    ("Google検索",         "題名+URL",      "テキスト", 2, "鍵(API key)か 規約上の 手当てが 要る"),
    ("docx/xlsx",          "本文/表",       "テキスト", 2, "python-docx も openpyxl も 無い"),
    ("X(投稿本文)",        "投稿",          "テキスト", 3, "静的でも 描画でも 本文 0字= ログインが 要る"),
    ("Facebook",           "投稿",          "テキスト", 3, "HTTP 400 ／ 743字は ログイン誘導のみ"),
    ("課金の要る面",       "本文",          "テキスト", 3, "x.com の 一部が 402(課金)"),
]


def _enc(url):
    """★URL に 日本語が 入ると 落ちる(★実測 UnicodeEncodeError)∴ ★先に 逃がす。"""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc,
                                    urllib.parse.quote(p.path, safe="/:@"),
                                    urllib.parse.quote(p.query, safe="=&:/?+"),
                                    p.fragment))


def _get(url, headers=None):
    req = urllib.request.Request(_enc(url), headers={"User-Agent": UA, **(headers or {})})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as f:
            body = f.read(MAX_BYTES)
            return {"ok": True, "status": f.status, "content_type": f.headers.get("Content-Type"),
                    "body": body, "final": f.url, "sec": round(time.time() - t0, 2)}
    except Exception as ex:
        return {"ok": False, "error": "%s: %s" % (type(ex).__name__, str(ex)[:120]),
                "sec": round(time.time() - t0, 2)}


def _text_of(body):
    """★★2026-09-01 直した(★私の 欠陥)= ★前は `get_text(" ")` で ★行を 空白に 潰していた。

    ★★実害は 2つ= ①★材料の 質が 測れない= ★ja.wikipedia 徳川家康が ★4行に なり
      ★『本文率 100%』と 出る(★リンク一覧と 本文が 同じ 100% に 見える= ★逆の 答え)。
      ②★分解する 側(★LLM 担当・EVO-0045)が ★段落の 境目を 失う。
    ★★実測(同じ頁・同じ取得)= `get_text(" ")` → 4行・本文率 100.0% ／
      `get_text("\n")` → ★10,775行・文らしい行 867・★本文率 44.3%。★字数は どちらも 116,192(同じ)。
    ★★字数は 変わらない= ★内容は 落としていない。★変わるのは ★構造が 残るか だけ。
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "lxml")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text("\n", strip=True)


def material_quality(text):
    """★材料の 質を ★決定論で 測る(★LLM 0回 ／ 書き込み 0)。

    ★★なぜ 要るか(★Inference Control の 実測 2026-09-01)= ★検索結果一覧を FACT 抽出に 通すと
      ★プロトコルは 完璧に 守られる(完走 3/3 ／ 引用が原文に在る 31/31)のに
      ★出るのは 所在カードだけ(『量子力学 入門』は 21件中16件= 76% が has_url/title/publisher)。
      ★★材料に 中身が 無い ∴ 出しようが ない。★『取れた』と『使える』を 分ける 数が 要る。
    ★★既存に 無かった= `egl.acquisition.CONTENT_STATUSES` は
      OBSERVED / CHALLENGE_PAGE / AUTH_WALL / PLACEHOLDER / EMPTY / UNEXPECTED_CONTENT / UNSUPPORTED
      ∴ ★『有る』と『使える』の 間の 語が 無い(★全レポ 走査で 確認)。

    ★★鍵(★何を 分母に したか)= ★分母は ★空でない 行の 字数の 合計。
      ★『文らしい行』= ★12字以上 かつ ★句点(。．.！？!?)を 含む 行。
      ★`body_ratio` = 文らしい行の 字数 ÷ 分母。
      ★`url_density` = URL の 数 ÷ 空でない行の 数(★索引(リンク一覧)は ここが 高い)。
    ★★これは ★私が 決めた 定義です= ★他の面の 数(例 23%)と ★直接は 比べられません。
    """
    import re as _re
    # ★★URL を 先に 外してから 測る(★2026-09-01 実測で 分かった 落とし穴)=
    #   ★URL は ドメインの 点(.)を 含む ∴ ★『句点を 含む 行』に 当たってしまい
    #   ★リンク一覧が ★本文率 100% に 見えた(★索引と 本文が 同じ 100%= 逆の 答え)。
    #   ★外して 測ると ★残るのは 題名だけ= ★短く 句点も 無い ∴ 本文率が 下がる。
    _bare = _re.sub(r"https?://\S+", " ", text or "")
    lines = [l.strip() for l in _re.split(r"[\n\r]+", _bare) if l.strip()]
    if not lines:
        return {"chars": len(text or ""), "lines": 0, "body_lines": 0,
                "body_ratio": 0.0, "url_density": 0.0,
                "key": "★分母=空でない行の字数合計 ／ 文らしい行=12字以上かつ句点を含む"}
    body = [l for l in lines if len(l) >= 12 and _re.search(r"[。．\.！？!?]", l)]
    tot = sum(len(l) for l in lines)
    return {"chars": len(text), "lines": len(lines), "body_lines": len(body),
            "body_ratio": round(100.0 * sum(len(l) for l in body) / tot, 1),
            "url_density": round(1.0 * len(_re.findall(r"https?://", text)) / len(lines), 3),
            "key": "★分母=空でない行の字数合計 ／ 文らしい行=12字以上かつ句点を含む"}


def _ok(kind, target, r, text=None, extra=None):
    out = {"ok": True, "kind": kind, "target": target, "sec": r.get("sec"),
           "status": r.get("status"), "content_type": r.get("content_type"),
           "bytes": len(r.get("body") or b"")}
    if text is not None:
        out["chars"] = len(text)
        out["preview"] = " ".join(text.split())[:400]
        out["quality"] = material_quality(text)     # ★『取れた』と『使える』を 分ける
        out["_text"] = text
    if extra:
        out.update(extra)
    return out


def _ng(kind, target, r):
    return {"ok": False, "kind": kind, "target": target, "sec": r.get("sec"),
            "error": r.get("error")}


# ── レベル1 の 口 ────────────────────────────────────────────────────────
def k_web(url):
    r = _get(url)
    return _ng("web", url, r) if not r["ok"] else _ok("web", url, r, _text_of(r["body"]))


def k_render(url, wait="networkidle"):
    """★静的で 本文が 出ない 面(SPA)を 描画して 取る。★実測 e-Gov 2.1秒。"""
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(user_agent=UA)
            pg.goto(_enc(url), wait_until=wait, timeout=60000)
            txt = pg.inner_text("body")
            b.close()
    except Exception as ex:
        return {"ok": False, "kind": "render", "target": url,
                "sec": round(time.time() - t0, 2),
                "error": "%s: %s" % (type(ex).__name__, str(ex)[:120])}
    return {"ok": True, "kind": "render", "target": url, "sec": round(time.time() - t0, 2),
            "status": None, "content_type": "text/plain(rendered)", "bytes": len(txt.encode()),
            "chars": len(txt), "preview": " ".join(txt.split())[:400],
            "quality": material_quality(txt), "_text": txt}


def k_pdf(url, out=None):
    r = _get(url)
    if not r["ok"]:
        return _ng("pdf", url, r)
    tmp = out or "/tmp/fetch1_%d.pdf" % os.getpid()
    open(tmp, "wb").write(r["body"])
    try:
        txt = subprocess.run(["pdftotext", "-q", tmp, "-"], capture_output=True,
                             timeout=120).stdout.decode("utf-8", "replace")
    except Exception as ex:
        return {"ok": False, "kind": "pdf", "target": url, "sec": r["sec"],
                "error": "%s: %s" % (type(ex).__name__, str(ex)[:120])}
    finally:
        if not out and os.path.exists(tmp):
            os.remove(tmp)
    return _ok("pdf", url, r, txt)


def k_json(url):
    r = _get(url, {"Accept": "application/json"})
    if not r["ok"]:
        return _ng("json", url, r)
    raw = r["body"].decode("utf-8", "replace")
    try:
        obj = json.loads(raw)
        extra = {"json_keys": (list(obj)[:12] if isinstance(obj, dict) else "list:%d" % len(obj))}
    except Exception:
        obj, extra = None, {"json_keys": None, "note": "★JSON として 読めない(★Atom/XML の ことが ある)"}
    return _ok("json", url, r, raw, extra)


def k_rss(url):
    import feedparser
    r = _get(url)
    if not r["ok"]:
        return _ng("rss", url, r)
    f = feedparser.parse(r["body"])
    items = [{"title": e.get("title"), "link": e.get("link")} for e in f.entries[:30]]
    return _ok("rss", url, r, "\n".join(str(i["title"]) for i in items), {"items": items,
               "n_items": len(f.entries)})


def k_search(query, max_n=10):
    """★鍵の 要らない 検索。★第一手は `ddgs`・控えが html 面。

    ★★2026-08-31 訂正(★私の 早すぎた 断定)= ★html 面を 直に 叩くと ★12件ほどで
      ★202 を 返し 本文が CAPTCHA に なる(逐語『Select all squares containing a duck』)。
      ★60秒 待っても 戻らなかった。★『10件 取れた』を 1回 見て レベル1 と 書いたのが 誤り。
    ★★`ddgs`(9.14.4・この機械に 在る)なら ★挑戦画面の 下でも 引けた= ★連続10件 10/10・各20件。
    """
    try:
        from ddgs import DDGS
        with DDGS() as d:
            rows = list(d.text(query, max_results=max_n))
        hits = [{"title": x.get("title") or "", "url": x.get("href") or ""} for x in rows]
        if hits:
            body = "\n".join("%s\t%s" % (h["title"], h["url"]) for h in hits)
            return {"ok": True, "kind": "search", "target": query, "sec": None, "status": None,
                    "content_type": "application/json", "bytes": len(body.encode()),
                    "chars": len(body), "preview": " / ".join(h["title"] for h in hits)[:400],
                    "hits": hits, "n_hits": len(hits), "engine": "ddgs",
                    "quality": material_quality(body), "_text": body}
    except Exception:
        pass
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    r = _get(url)
    if not r["ok"]:
        return _ng("search", query, r)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r["body"], "lxml")
    hits = []
    for a in soup.select("a.result__a")[:max_n]:
        href = a.get("href", "")
        m = re.search(r"uddg=([^&]+)", href)
        hits.append({"title": a.get_text(" ", strip=True),
                     "url": urllib.parse.unquote(m.group(1)) if m else href})
    return _ok("search", query, r, "\n".join(h["title"] for h in hits),
               {"hits": hits, "n_hits": len(hits), "engine": "duckduckgo-html"})


def k_youtube(url):
    """★題名と 説明は HTML の JS から 取れる。★字幕の 本体は レベル2(★一覧までは 出す)。"""
    r = _get(url)
    if not r["ok"]:
        return _ng("youtube", url, r)
    s = r["body"].decode("utf-8", "replace")
    title = (re.search(r"<title>(.{0,200}?)</title>", s) or [None, None])[1]
    desc = (re.search(r'"shortDescription":"(.{0,4000}?)","', s) or [None, None])[1]
    tracks = []
    m = re.search(r'"captionTracks":(\[.*?\])', s)
    if m:
        try:
            for t in json.loads(m.group(1).replace("\\u0026", "&")):
                tracks.append({"lang": t.get("languageCode"),
                               "name": (t.get("name") or {}).get("simpleText")})
        except Exception:
            pass
    body = "\n".join(x for x in (title, (desc or "").replace("\\n", "\n")) if x)
    return _ok("youtube", url, r, body,
               {"title": title, "n_caption_tracks": len(tracks), "caption_tracks": tracks,
                "note": "★字幕の 本体は レベル2(★一覧は 取れる が 取得は 0バイト・2026-08-30 実測)"})


def k_xprofile(url):
    """★X は プロフィール欄 まで(★投稿本文は レベル3= ログインが 要る)。"""
    r = _get(url)
    if not r["ok"]:
        return _ng("xprofile", url, r)
    txt = _text_of(r["body"])
    return _ok("xprofile", url, r, txt,
               {"note": "★投稿本文は 入らない(★静的でも 描画でも 0字= レベル3)"})


def k_file(url, out=None):
    r = _get(url)
    if not r["ok"]:
        return _ng("file", url, r)
    path = out or os.path.join("/tmp", os.path.basename(urllib.parse.urlsplit(url).path) or "fetch1.bin")
    open(path, "wb").write(r["body"])
    return _ok("file", url, r, None, {"out": path})


KINDS = {"web": k_web, "render": k_render, "pdf": k_pdf, "json": k_json, "rss": k_rss,
         "search": k_search, "youtube": k_youtube, "xprofile": k_xprofile, "file": k_file}


def k_auto(target):
    """★URL の 形から 口を 選ぶ。★選べない ときは `web`。★選んだ 口を 返りに 書く。"""
    if not str(target).startswith(("http://", "https://")):
        return dict(k_search(target), routed_by="auto:文字列は検索へ")
    low = target.lower()
    if "youtube.com/watch" in low or "youtu.be/" in low:
        return dict(k_youtube(target), routed_by="auto:youtube")
    if "x.com/" in low or "twitter.com/" in low:
        return dict(k_xprofile(target), routed_by="auto:xprofile")
    if low.endswith(".pdf") or "/pdf/" in low:
        return dict(k_pdf(target), routed_by="auto:pdf")
    if low.endswith((".xml", ".rss", ".atom")) or "/rss" in low or "/feed" in low:
        return dict(k_rss(target), routed_by="auto:rss")
    if low.endswith(".json") or "/api/" in low or low.startswith("https://api."):
        return dict(k_json(target), routed_by="auto:json")
    if low.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp3", ".mp4", ".zip")):
        return dict(k_file(target), routed_by="auto:file")
    r = k_web(target)
    # ★静的で 本文が 薄ければ ★描画へ 落とす(★実測 e-Gov 10字 → 11,957字)。
    if r.get("ok") and r.get("chars", 0) < 200:
        r2 = k_render(target)
        if r2.get("ok") and r2.get("chars", 0) > r.get("chars", 0):
            return dict(r2, routed_by="auto:web→本文が薄いので render へ落とした",
                        static_chars=r.get("chars"))
    return dict(r, routed_by="auto:web")


def _print_table():
    print("★外部から 取れる物の 網羅表(★2026-08-30 実走・ITEM-2DER-EVO-0044)")
    print("★レベル 1=いまの道具で認証なしに取れた / 2=道具か鍵が要る / 3=ログイン・契約・規約が要る")
    print()
    print("  %-2s %-20s %-14s %-10s %s" % ("Lv", "システム", "取れる物", "形式", "実測"))
    print("  " + "-" * 108)
    for sysname, what, form, lv, ev in sorted(TABLE, key=lambda x: (x[3], x[0])):
        print("  %-2d %-20s %-14s %-10s %s" % (lv, sysname, what, form, ev))
    n1 = sum(1 for x in TABLE if x[3] == 1)
    print()
    print("  ★分母 %d 行 ／ レベル1 %d ／ レベル2 %d ／ レベル3 %d"
          % (len(TABLE), n1, sum(1 for x in TABLE if x[3] == 2), sum(1 for x in TABLE if x[3] == 3)))


SELFTEST = [
    ("web",      "https://ja.wikipedia.org/wiki/徳川家康"),
    ("render",   "https://elaws.e-gov.go.jp/document?lawid=321CONSTITUTION"),
    ("pdf",      "https://arxiv.org/pdf/1706.03762"),
    ("json",     "https://ja.wikipedia.org/api/rest_v1/page/summary/徳川家康"),
    ("rss",      "https://news.yahoo.co.jp/rss/topics/top-picks.xml"),
    ("search",   "徳川家康 生年"),
    ("youtube",  "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("xprofile", "https://x.com/elonmusk"),
    ("file",     "https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg"),
]


def _selftest():
    print("★レベル1 の 全種類を 実走する(★分母 %d)" % len(SELFTEST))
    ok = 0
    for kind, target in SELFTEST:
        r = KINDS[kind](target)
        got = r.get("chars", r.get("bytes", 0))
        if r.get("ok"):
            ok += 1
            print("  ok  %-9s %-46s %8s %6.1fs" % (kind, str(target)[:46], got, r.get("sec") or 0))
        else:
            print("  ★  %-9s %-46s %s" % (kind, str(target)[:46], r.get("error")))
    print()
    print("★通った = %d/%d" % (ok, len(SELFTEST)))
    return 0 if ok == len(SELFTEST) else 1


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--table":
        _print_table()
        return 0
    if argv[0] == "--selftest":
        return _selftest()
    kind = argv[0]
    if kind not in KINDS and kind != "auto":
        print("★知らない 種類: %s ／ 使えるのは: auto %s" % (kind, " ".join(sorted(KINDS))))
        return 2
    if len(argv) < 2:
        print("★対象が ありません")
        return 2
    target = argv[1]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    # ★★2026-08-31 直した= ★`pdf` の `--out` が ★生の PDF を 書いていた ∴
    #   ★本文を 使う 側(★LLM 担当= 分解の 材料)には 使えなかった。
    #   ★`--out` は ★どの種類でも ★本文を 書く。★生のまま 欲しい ときは `file` を 使う。
    r = k_auto(target) if kind == "auto" else (
        KINDS[kind](target, out) if kind == "file" else KINDS[kind](target))
    text = r.pop("_text", None)
    if out and text is not None and kind != "file":
        open(out, "w", encoding="utf-8").write(text)
        r["out"] = out
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
