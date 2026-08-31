#!/usr/bin/env python3
"""★材料を 取り直す(★ITEM-2DER-EVO-0045)。★本文は repo に 置かない= ★外部の文だから。

★★なぜ 自分で 取ったか= ★取得の 記録は ★`raw_content_hash` しか 残らない
  (`egl/egl/acquisition.py: run_acquisition`)∴ ★RRI が 測った 本文は ★台帳から 引けない。
★★出所の 違いを 隠さない= ★RRI 実測 222,670字は ★描画後の inner_text ／ ★本script は ★法令API の XML。
  ★同じ法令・★取り方が 違う ∴ ★字数は 一致しない(★実測 233,074字)。
"""
import sys, re, urllib.request, xml.etree.ElementTree as ET

URL = "https://laws.e-gov.go.jp/api/1/lawdata/129AC0000000089"   # ★民法(明治二十九年法律第八十九号)
BLOCK = {"Part", "Chapter", "Section", "Subsection", "Division", "Article", "Paragraph",
         "Item", "Subitem1", "Subitem2", "PartTitle", "ChapterTitle", "SectionTitle",
         "SubsectionTitle", "DivisionTitle", "ArticleTitle", "ArticleCaption",
         "ParagraphSentence", "ItemSentence", "Sentence", "SupplProvision",
         "SupplProvisionLabel", "LawTitle", "TOC"}


def to_text(xml_bytes):
    root = ET.fromstring(xml_bytes.decode("utf-8"))
    out = []

    def walk(e):
        t = (e.text or "").strip()
        if t:
            out.append(t)
        for c in e:
            walk(c)
            s = (c.tail or "").strip()
            if s:
                out.append(s)
        if e.tag in BLOCK and out and out[-1] != "\n":
            out.append("\n")

    walk(root)
    return re.sub(r"\n{3,}", "\n\n", "".join(out))


if __name__ == "__main__":
    dst = sys.argv[1] if len(sys.argv) > 1 else "/tmp/minpo.txt"
    b = urllib.request.urlopen(URL, timeout=90).read()
    txt = to_text(b)
    open(dst, "w").write(txt)
    print("XML %d bytes → 平文 %d字 → %s" % (len(b), len(txt), dst))
