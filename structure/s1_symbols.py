#!/usr/bin/env python3
"""Stage 1b: SYMBOL_INDEX.jsonl — deterministic AST/structural extraction, no LLM.
Spec §2.3. DERIVED artifact. Python / Markdown / JSON-JSONL extractors.
NOTE: never imports target modules (twoder/operator.py shadows stdlib `operator`,
DE-0486 §5(b)). Pure ast.parse on source text.
"""
import ast, json, os, re, sys
from collections import Counter
from pathlib import Path

HOME = Path("/home/takasan")
STRUCT = HOME / "egl/structure"
MANIFEST = STRUCT / "FILE_MANIFEST.jsonl"
OUT = STRUCT / "SYMBOL_INDEX.jsonl"

NET_HINT = re.compile(r"\b(requests|urllib|httpx|http\.client|socket|aiohttp|openai)\b")
URL_LIT = re.compile(r"https?://[^\s\"']+|:\d{4}\b")
EVENT_LIKE = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
STATUS_WORDS = re.compile(r"\b(PENDING|DONE|LIVE|PROPOSED|PLANNED|IN_PROGRESS|BLOCKED|CLOSED|"
                          r"SUPERSEDED|DEPRECATED|FROZEN|MISSING|UNWIRED|ORPHAN|NOT_IMPLEMENTED)\b")
DE_RE = re.compile(r"DE-\d{4}")
ITEM_RE = re.compile(r"ITEM-[A-Z0-9\-]+")
CHG_RE = re.compile(r"CHG-\d{4}")
JREV_RE = re.compile(r"JREV-\d{4}")
ART_RE = re.compile(r"ART-[0-9a-f]{6,}")


def module_candidates(repo, rel):
    """Dotted module names this file could be imported as (repo-root and HOME on sys.path)."""
    if not rel.endswith(".py"):
        return []
    p = rel[:-3].replace("/", ".")
    if p.endswith(".__init__"):
        p = p[:-9]
    out = {p}                      # repo root on sys.path
    out.add(f"{repo}.{p}" if repo != "dev-workcell" else p)  # HOME on sys.path
    return sorted(x for x in out if x)


def py_extract(src, path):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"parse_error": f"{e.__class__.__name__}: {e}"}
    imports, defines, calls = [], [], []
    reads, writes, subproc, net, evkinds = [], [], [], [], set()
    cli = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.append({"module": a.name, "symbol": None, "lineno": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * (node.level or 0)) + (node.module or "")
            for a in node.names:
                imports.append({"module": mod, "symbol": a.name, "lineno": node.lineno})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defines.append({
                "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                "name": node.name, "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "is_public": not node.name.startswith("_"),
                "doc": (ast.get_docstring(node) or "")[:200],
            })
        elif isinstance(node, ast.Call):
            fn = node.func
            name = (fn.attr if isinstance(fn, ast.Attribute)
                    else fn.id if isinstance(fn, ast.Name) else None)
            if name:
                full = ast.unparse(fn) if isinstance(fn, ast.Attribute) else name
                calls.append({"callee": full, "lineno": node.lineno})
                lits = [a.value for a in node.args
                        if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                if name in ("open",) or full.endswith((".open", ".read_text", ".read_bytes",
                                                        ".load", ".loads")):
                    mode = next((a.value for a in node.args[1:]
                                 if isinstance(a, ast.Constant) and isinstance(a.value, str)), "r")
                    tgt = writes if any(m in mode for m in "wax") else reads
                    tgt.append({"target": lits[0] if lits else None, "lineno": node.lineno,
                                "via": full})
                elif full.endswith((".write_text", ".write_bytes", ".dump", ".dumps",
                                    ".append_event", ".write")):
                    writes.append({"target": lits[0] if lits else None,
                                   "lineno": node.lineno, "via": full})
                if "subprocess" in full or name in ("run", "Popen", "check_output", "call"):
                    if "subprocess" in full or full in ("run", "Popen", "check_output"):
                        subproc.append({"call": full, "lineno": node.lineno,
                                        "args": lits[:3]})
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if EVENT_LIKE.match(v):
                evkinds.add(v)
    if NET_HINT.search(src):
        for m in NET_HINT.finditer(src):
            net.append({"lib": m.group(1)})
    urls = sorted(set(URL_LIT.findall(src)))[:12]
    if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', src):
        cli.append("__main__")
    if "argparse" in src:
        cli.append("argparse")
    base = os.path.basename(path)
    test_target = None
    if base.startswith("test_"):
        test_target = base[5:-3]
    return {
        "imports": imports, "defines": defines,
        "calls_count": len(calls),
        "calls": calls[:400],
        "file_reads": reads, "file_writes": writes,
        "subprocess_calls": subproc,
        "network_libs": sorted({n["lib"] for n in net}),
        "network_literals": urls,
        "event_kinds": sorted(evkinds)[:80],
        "cli_entrypoints": cli,
        "test_target": test_target,
        "loc": src.count("\n") + 1,
    }


def md_extract(src):
    m = re.search(r"^#\s+(.+)$", src, re.M)
    return {
        "title": m.group(1).strip() if m else None,
        "status_words": sorted(set(STATUS_WORDS.findall(src))),
        "supersedes": sorted(set(re.findall(r"SUPERSEDE[SD]?\s+([^\n。,]{3,60})", src)))[:10],
        "de_refs": sorted(set(DE_RE.findall(src))),
        "item_refs": sorted(set(ITEM_RE.findall(src))),
        "chg_refs": sorted(set(CHG_RE.findall(src))),
        "jrev_refs": sorted(set(JREV_RE.findall(src))),
        "repo_refs": sorted({r for r in ("egl", "twoder", "dev-workcell", "rri", "ds")
                             if re.search(r"\b" + re.escape(r) + r"\b", src)}),
        "code_refs": sorted(set(re.findall(r"`?([a-z_][a-z0-9_]*\.py)[:`]", src)))[:60],
        "headings": re.findall(r"^#{2,3}\s+(.+)$", src, re.M)[:40],
        "loc": src.count("\n") + 1,
    }


def jsonl_extract(path, ext):
    keys, kinds, ids, ts = Counter(), Counter(), [], []
    n = 0
    hashfields = set()
    try:
        if ext == ".jsonl":
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    n += 1
                    if n > 20000:
                        break
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if not isinstance(d, dict):
                        continue
                    keys.update(d.keys())
                    for k, v in d.items():
                        if k in ("kind", "event_kind", "type", "record_type", "event") and isinstance(v, str):
                            kinds[v] += 1
                        if isinstance(v, str) and re.match(r"^[A-Z]{2,6}-[0-9a-f]{4,}$", v):
                            ids.append(v)
                        if k.lower() in ("ts", "timestamp", "at", "created_at",
                                         "registered_at", "admitted_at") and isinstance(v, str):
                            ts.append(v)
                        if "hash" in k.lower() or "sha" in k.lower() or k.lower() in ("prev", "chain"):
                            hashfields.add(k)
        else:
            with open(path, encoding="utf-8", errors="replace") as f:
                d = json.load(f)
            if isinstance(d, dict):
                keys.update(d.keys()); n = 1
            elif isinstance(d, list):
                n = len(d)
                for x in d[:5000]:
                    if isinstance(x, dict):
                        keys.update(x.keys())
    except Exception as e:
        return {"parse_error": str(e)[:200]}
    return {
        "record_count": n,
        "schema_shape": [k for k, _ in keys.most_common(40)],
        "key_coverage": {k: round(v / n, 3) for k, v in keys.most_common(15)} if n else {},
        "event_kinds": [k for k, _ in kinds.most_common(30)],
        "id_samples": sorted(set(ids))[:8],
        "first_ts": min(ts) if ts else None,
        "last_ts": max(ts) if ts else None,
        "hash_chain_fields": sorted(hashfields)[:10],
    }


def main():
    rows = [json.loads(l) for l in open(MANIFEST)]
    out = []
    modmap = {}
    for r in rows:
        if r["extension"] == ".py":
            for m in module_candidates(r["repo"], r["relative_path"]):
                modmap.setdefault(m, []).append(f"{r['repo']}/{r['relative_path']}")
    for r in rows:
        ext, ap = r["extension"], r["absolute_path"]
        rec = {"repo": r["repo"], "relative_path": r["relative_path"],
               "key": f"{r['repo']}/{r['relative_path']}",
               "trust_tier": r["trust_tier"], "classification": r["classification"],
               "language": r["language"], "sha256": r["sha256"],
               "derived_from": "ast/regex", "regenerable": True}
        try:
            if ext == ".py":
                rec.update(py_extract(Path(ap).read_text(encoding="utf-8", errors="replace"), ap))
                rec["module_names"] = module_candidates(r["repo"], r["relative_path"])
            elif ext == ".md":
                rec.update(md_extract(Path(ap).read_text(encoding="utf-8", errors="replace")))
            elif ext in (".json", ".jsonl"):
                rec.update(jsonl_extract(ap, ext))
            else:
                continue
        except Exception as e:
            rec["extract_error"] = f"{e.__class__.__name__}: {e}"[:200]
        out.append(rec)

    # reverse index: who imports whom (cross-file, deterministic)
    imported_by = {}
    for rec in out:
        for imp in rec.get("imports", []):
            mod = imp["module"] or ""
            sym = imp.get("symbol")
            for cand in (mod, f"{mod}.{sym}" if sym else None):
                if cand and cand in modmap:
                    for tgt in modmap[cand]:
                        imported_by.setdefault(tgt, set()).add(rec["key"])
    for rec in out:
        rec["imported_by"] = sorted(imported_by.get(rec["key"], []))
        rec["imported_by_count"] = len(rec["imported_by"])
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
    print(f"{len(out)} rows -> {OUT}")
    perr = [r["key"] for r in out if r.get("parse_error")]
    print(f"parse_errors: {len(perr)}", perr[:5])

if __name__ == "__main__":
    main()
