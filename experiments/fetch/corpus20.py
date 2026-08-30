#!/usr/bin/env python3
"""[Claude実装/Topology] 2026-08-31 — ★外部取得の 試験用 20件(★LLM 担当の 依頼)。

★★これは ★RRI が 測った 20本(10領域×2・到達17/20)では ありません= ★別物です。
  ★私が 2026-08-30〜31 に ★1件ずつ 実走して レベルを 決めた ★20行 の 方です。
  ★同じ『20』が 2つ 在る ので ★鍵(何を 分母に したか)を 必ず 添える こと。

★★使い方= python3 egl/experiments/fetch/corpus20.py [--json 出力先]
  ★毎回 実走して ★その場の 数を 出す(★古い数を 貼らない)。

★★1件の 形=
  id / 領域 / 期待レベル / 口(adapter か fetch1 の種類) / 対象 / 期待する結果 / 根拠(前回の実測)
  ★『期待する結果』は ★通る(ok)だけでは ない= ★通らない ことが 正しい 件も 入れている
    (★レベル2・3 は ★落ちるのが 正解 ∴ ★試験としては ★そこが 効く)。
"""
import json
import subprocess
import sys
import time

FETCH1 = "/home/takasan/egl/experiments/fetch/fetch1.py"

CASES = [
 # id, 領域, Lv, 種類, 対象, 期待, 前回の実測
 ("C01", "一般WEB",     1, "web",      "https://ja.wikipedia.org/wiki/徳川家康", "ok",   "本文 115,553字"),
 ("C02", "法令(SPA)",   1, "render",   "https://elaws.e-gov.go.jp/document?lawid=321CONSTITUTION", "ok", "静的800B→描画 11,957字 2.0秒"),
 ("C03", "法令(静的)",  1, "web",      "https://elaws.e-gov.go.jp/document?lawid=321CONSTITUTION", "ok_but_thin", "800B・本文10字= ★取れたが 使えない"),
 ("C04", "論文PDF",     1, "pdf",      "https://arxiv.org/pdf/1706.03762", "ok",   "39,919字(pdftotext)"),
 ("C05", "プレーン",     1, "web",      "https://www.gutenberg.org/files/11/11-0.txt", "ok", "151,191B"),
 ("C06", "表(CSV)",     1, "web",      "https://raw.githubusercontent.com/datasets/gdp/main/data/gdp.csv", "ok", "562,767B"),
 ("C07", "API(百科)",   1, "json",     "https://ja.wikipedia.org/api/rest_v1/page/summary/徳川家康", "ok", "2,410B"),
 ("C08", "API(論文)",   1, "json",     "http://export.arxiv.org/api/query?search_query=all:transformer&max_results=2", "ok", "4,557B Atom"),
 ("C09", "API(コード)", 1, "json",     "https://api.github.com/repos/python/cpython", "ok", "6,617B"),
 ("C10", "RSS",        1, "rss",      "https://news.yahoo.co.jp/rss/topics/top-picks.xml", "ok", "3,118B"),
 ("C11", "検索",        1, "search",   "徳川家康 生年", "ok", "ddgs 経由 20件(★html面は12件ほどでCAPTCHA)"),
 ("C12", "検索(法令)",  1, "search",   "日本国憲法 第九条", "ok", "ddgs 経由 20件"),
 ("C13", "動画メタ",    1, "youtube",  "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "ok", "題名と説明。★HTML 1,376,037B だが 本文0字"),
 ("C14", "画像",        1, "file",     "https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg", "ok", "9,022B jpeg"),
 ("C15", "SNSプロフ",   1, "xprofile", "https://x.com/elonmusk", "ok_meta_only", "2,178字= 名前/投稿数/追随者。★投稿本文は 入らない"),
 ("C16", "SNS投稿",     3, "web",      "https://x.com/elonmusk/status/1", "expect_no_body", "★ログインが 要る= 本文0字が 正解"),
 ("C17", "SNS(FB)",     3, "web",      "https://www.facebook.com/Meta/", "expect_fail", "★HTTP 400 が 正解"),
 ("C18", "課金",        3, "web",      "https://httpbingo.org/status/402", "expect_fail", "★402= PAYMENT_REQUIRED が 正解"),
 ("C19", "相手側障害",  2, "web",      "https://httpbingo.org/status/503", "expect_fail", "★503= SERVER_ERROR が 正解"),
 ("C20", "存在しない",  2, "web",      "https://ja.wikipedia.org/wiki/存在しない頁_ZZZQQ_20260831", "expect_fail", "★404= NOT_FOUND_REMOTE が 正解"),
]


def transport_of(target):
    """★本線の 語(`transport_status`)を 添える= ★『通らない』の 理由を 消さない。

    ★`fetch1` は 実験の 口 ∴ ★返りは urllib の 例外文。★試験に 使うのは ★本線の 語 の 方
      (PAYMENT_REQUIRED / SERVER_ERROR / NOT_FOUND_REMOTE / BAD_REQUEST …)。
    """
    if not str(target).startswith(("http://", "https://")):
        return None
    try:
        sys.path.insert(0, "/home/takasan/egl")
        from egl import adapters as A
        r = A.fetch({"adapter_class": "ACQ_HTTP_STATIC", "target_locator": target})
        return {"transport": r["transport_status"], "content": r["content_status"],
                "http": r["http_status"]}
    except Exception as ex:
        return {"transport": "★引けない", "error": type(ex).__name__}


def run(kind, target):
    t0 = time.time()
    p = subprocess.run([sys.executable, FETCH1, kind, target],
                       capture_output=True, timeout=180)
    sec = round(time.time() - t0, 2)
    try:
        return json.loads(p.stdout.decode("utf-8", "replace")), sec
    except Exception:
        return {"ok": False, "error": (p.stderr.decode("utf-8", "replace")[:120] or "no json")}, sec


def main(argv):
    out = argv[argv.index("--json") + 1] if "--json" in argv else None
    rows = []
    print("★外部取得 試験用 20件(★私の20行。★RRI の20本とは 別物)")
    print("  %-4s %-12s %-2s %-9s %-14s %8s %7s %-18s" % ("id", "領域", "Lv", "口", "期待", "実測chars", "秒", "本線の語"))
    print("  " + "-" * 104)
    for cid, area, lv, kind, target, expect, basis in CASES:
        r, sec = run(kind, target)
        got = r.get("chars", r.get("bytes", 0)) or 0
        tr = transport_of(target)
        rows.append({"id": cid, "領域": area, "level": lv, "kind": kind, "target": target,
                     "expect": expect, "basis": basis, "ok": bool(r.get("ok")),
                     "chars": r.get("chars"), "bytes": r.get("bytes"),
                     "error": r.get("error"), "sec": sec, "本線の語": tr})
        print("  %-4s %-12s %-2d %-9s %-14s %8s %6.1fs %-18s %s"
              % (cid, area, lv, kind, expect, got, sec,
                 (tr or {}).get("transport") or "-", "" if r.get("ok") else "★通らない"))
    n_ok = sum(1 for x in rows if x["ok"])
    print()
    print("  ★分母 %d ／ 通った %d ／ 通らない %d" % (len(rows), n_ok, len(rows) - n_ok))
    print("  ★★『通らない』が 正しい 件が 在る= expect が expect_fail / expect_no_body の 5件。")
    print("  ★★この20件は ★私が 実走して レベルを 決めた 20行。★RRI の 20本(到達17/20)とは ★別の 分母。")
    if out:
        json.dump({"generated_by": "TOPOLOGY_CLAUDE", "item": "ITEM-2DER-EVO-0047",
                   "note": "★RRI の20本とは別物。★私が実走して決めた20行。",
                   "n": len(rows), "n_ok": n_ok, "rows": rows},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  ★書いた:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
