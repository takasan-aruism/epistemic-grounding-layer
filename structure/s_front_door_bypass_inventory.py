#!/usr/bin/env python3
"""s_front_door_bypass_inventory — 依頼 D4-I: front door を経由しない「直叩き」経路の機械的な列挙。

★棚卸しのみ。**閉塞の提案はしない**（依頼 D4-I の明示指示）。完全決定論・LLM 不使用。

問い:
  (1) `egl.de_admission` を `twoder.submit` を経由せず直接呼んでいる箇所
  (2) `dw.workcell` を `submit`/`dispatch` を経由せず直接呼んでいる箇所
  (3) それぞれ LIVE か TEST_ONLY_ISLAND か（`EDGE_INVENTORY.jsonl` と突合）

判定規則（事前固定・記録）:
  - 「直叩き」= 当該 symbol を import して呼んでいるファイルのうち、**front door 経由の入口を通っていない**もの。
  - front door 経由と見なすのは `twoder/submit.py` 自身と、submit を呼ぶラッパ（`de_submit_route.py`）。
  - **判定できないものは UNKNOWN と書く。推測で分類しない。**

usage: s_front_door_bypass_inventory.py [--check]
"""
import json
import os
import re
import sys

ROOT = "/home/takasan"
STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "FRONT_DOOR_BYPASS_INVENTORY.json")
EDGE_INVENTORY = os.path.join(STRUCT, "EDGE_INVENTORY.jsonl")
REPOS = ("egl", "ds", "rri", "twoder", "dev-workcell")

# 調べる対象（★事前固定）
TARGETS = [
    {"key": "de_admission", "symbols": ["admit_design_evidence"],
     "module_hints": ["egl.de_admission", "from egl import de_admission", "de_admission."],
     "front_door_files": ["twoder/submit.py", "egl/structure/de_submit_route.py"]},
    {"key": "dw_workcell", "symbols": ["create_task", "record_plan", "derive_state", "_read_events"],
     "module_hints": ["dw.workcell", "from dw import workcell", "workcell."],
     "front_door_files": ["twoder/submit.py", "twoder/dispatch.py", "dw/dispatch.py"]},
]


def _edge_status():
    """★(caller_file, callee_symbol) → status。**呼出箇所ごとの status** を返す（symbol 全体の集合ではない）。
    symbol 全体の集合を返すと全行が同じ値になり、問い(3)『それぞれ LIVE か TEST_ONLY_ISLAND か』に答えられない。"""
    by_pair, by_sym = {}, {}
    with open(EDGE_INVENTORY, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r.get("caller_file"), r.get("callee_symbol"))
            by_pair.setdefault(key, set()).add(r.get("status"))
            by_sym.setdefault(r.get("callee_symbol"), set()).add(r.get("status"))
    return ({k: sorted(v) for k, v in by_pair.items()}, {k: sorted(v) for k, v in by_sym.items()})


def _py_files():
    out = []
    for repo in REPOS:
        base = os.path.join(ROOT, repo)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
            for fn in filenames:
                if fn.endswith(".py"):
                    p = os.path.join(dirpath, fn)
                    out.append((os.path.relpath(p, ROOT), p))
    return sorted(out)


def scan():
    edge_pair, edge_sym = _edge_status()
    files = _py_files()
    results = {}
    for tgt in TARGETS:
        hits = []
        for rel, path in files:
            if rel in tgt["front_door_files"]:
                continue                       # front door 自身は直叩きではない
            if rel.endswith("/%s.py" % tgt["key"]) or rel.endswith("/workcell.py"):
                continue                       # 定義元モジュール内部の呼出は「直叩き」ではない
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if not any(h in text for h in tgt["module_hints"]):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for sym in tgt["symbols"]:
                    if re.search(r"\b%s\s*\(" % re.escape(sym), line):
                        st = edge_pair.get((rel, sym))
                        hits.append({"file": rel, "line": i, "callee": sym,
                                     "edge_status": st or ["UNKNOWN(この呼出箇所は EDGE_INVENTORY に無い)"],
                                     "status_resolution": "PER_CALL_SITE" if st else "UNRESOLVED",
                                     "is_test": ("/test" in rel or rel.split("/")[-1].startswith("test_")
                                                 or "/regression/" in rel),
                                     "source": line.strip()[:120]})
        results[tgt["key"]] = hits
    return results, edge_sym


def assess():
    results, edge = scan()
    summary = {}
    for key, hits in results.items():
        by_status = {}
        for h in hits:
            for s in h["edge_status"]:
                by_status[s] = by_status.get(s, 0) + 1
        summary[key] = {"total_call_sites": len(hits),
                        "files": sorted({h["file"] for h in hits}),
                        "n_files": len({h["file"] for h in hits}),
                        "test_sites": sum(1 for h in hits if h["is_test"]),
                        "non_test_sites": sum(1 for h in hits if not h["is_test"]),
                        "by_edge_status": by_status,
                        "unresolved_sites": sum(1 for h in hits if h.get("status_resolution") == "UNRESOLVED")}
    return {"summary": summary, "sites": results,
            "rules": {"front_door_files": {t["key"]: t["front_door_files"] for t in TARGETS},
                      "symbols": {t["key"]: t["symbols"] for t in TARGETS},
                      "note": "front door 自身は除外。判定できないものは UNKNOWN と書き、推測で分類しない。"},
            "scope_note": "★棚卸しのみ。閉塞の提案はしない（依頼 D4-I）。"}


def check():
    r = assess()
    ok = True
    print("[%s] 走査対象が空でない (%d repo)" % ("PASS" if REPOS else "FAIL", len(REPOS)))
    a = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    print("[%s] 決定論再現" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    found = sum(v["total_call_sites"] for v in r["summary"].values())
    print("[INFO] 検出した直叩き呼出箇所: %d" % found)
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    r = assess()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    print("front door を経由しない直叩き経路の棚卸し（★閉塞の提案はしない）")
    for key, s in r["summary"].items():
        print("\n■ %s : 呼出箇所 %d / ファイル %d（test %d / 非test %d）"
              % (key, s["total_call_sites"], s["n_files"], s["test_sites"], s["non_test_sites"]))
        print("   EDGE_INVENTORY status 内訳: %s" % s["by_edge_status"])
        for h in r["sites"][key]:
            if h["is_test"]:
                continue
            print("   [非test] %s:%d  %s  %s" % (h["file"], h["line"], h["callee"], h["edge_status"]))
        tests = sorted({h["file"] for h in r["sites"][key] if h["is_test"]})
        if tests:
            print("   [test] %d ファイル: %s" % (len(tests), ", ".join(tests[:6])
                                                 + (" …" if len(tests) > 6 else "")))
    print("\n  → %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
