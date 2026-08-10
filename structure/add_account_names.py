#!/usr/bin/env python3
"""採択された科目の名前を 命名台帳へ足す(★新台帳0=既存 jsonl に行を足すだけ・★LLM 0回)。
★名前は MGR/DESIGN が定めた物を そのまま書く(★捏造しない=★由来を name_status に残す)。
★既存の行は 1バイトも変えない。"""
import json
import sys

sys.path.insert(0, "/home/takasan/egl/structure")
import s_account_axis_names as N   # noqa: E402

ADD = [("AX-cee7bf57", "進捗の記録", "v3"), ("ACC-53c96ac2", "実装の依頼", "adopted")]


def main():
    lines = [json.loads(l) for l in open(N.OUT, encoding="utf-8") if l.strip()]
    header, rows = lines[0], lines[1:]
    have = {r["axis_id"] for r in rows}
    added = []
    for aid, name, ver in ADD:
        if aid in have:
            continue
        rows.append({"axis_id": aid, "axes_version": ver, "name": name,
                     "name_status": "ADOPTED_BY_ADJUDICATION",   # ★LLM 合議ではない=★由来を分ける
                     "adjudicated_by": "MGR/DESIGN 2026-08-10", "proposals": {}, "agreement_count": 0,
                     "consolidated_tokens": None, "sample_element_ids": [], "sampled_k": 0,
                     "model": None, "endpoint": None, "seeds": [], "prompt_id": None})
        added.append(aid)
    rows.sort(key=lambda r: r["axis_id"])
    open(N.OUT, "w", encoding="utf-8").write(N._ser(rows, header))
    print("★足した行 =", added, "／ 台帳の行数 =", len(rows))


if __name__ == "__main__":
    main()
