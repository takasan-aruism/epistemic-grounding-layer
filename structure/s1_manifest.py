#!/usr/bin/env python3
"""Stage 1a: FILE_MANIFEST.jsonl — deterministic, no LLM.
Spec: egl/docs/STRUCTURAL_RECONSTRUCTION_SPEC_v0.1.md §2.2
DERIVED artifact (regenerable). Not a system of record.
"""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

HOME = Path("/home/takasan")
REPOS = ["egl", "twoder", "dev-workcell", "rri", "ds"]
OUT = HOME / "egl/structure/FILE_MANIFEST.jsonl"

LANG = {".py": "python", ".md": "markdown", ".json": "json", ".jsonl": "jsonl",
        ".sh": "shell", ".html": "html", ".txt": "text", ".log": "log",
        ".zip": "archive", ".diff": "diff", ".csv": "csv", ".yaml": "yaml", ".yml": "yaml"}

def sh(cwd, *args):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout

def classify(rel, ext, tracked):
    p = rel.lower()
    base = os.path.basename(p)
    if "/__pycache__/" in "/" + p or ext == ".pyc":
        return "generated"
    if ext == ".py":
        if base.startswith("test_") or "/regression/" in "/" + p or "/tests/" in "/" + p:
            return "test"
        return "source"
    if ext == ".jsonl":
        return "event_store" if not tracked else "ledger"
    if ext == ".json":
        if "/runs/" in "/" + p:
            return "runtime_trace"
        if "/out/" in "/" + p or "/results/" in "/" + p:
            return "generated"
        return "config" if base in ("package.json",) else "ledger"
    if ext == ".md":
        return "doc"
    if ext in (".zip",):
        return "archive"
    if ext in (".log", ".txt", ".diff", ".html", ".csv"):
        return "generated" if "/out/" in "/" + p else "artifact"
    if ext in (".sh",):
        return "source"
    return "artifact"

GEN_HINT = re.compile(r"(/__pycache__/|/\.pytest_cache/|/out/|/runs/|\.pyc$|-latest\.json$)")
DE_RE = re.compile(r"DE-\d{4}")

def main():
    rows = []
    for repo in REPOS:
        root = HOME / repo
        if not root.exists():
            continue
        tracked = set(x for x in sh(root, "git", "ls-files").splitlines() if x)
        # first/last commit + count per tracked file (one git log pass per repo)
        first, last, count = {}, {}, {}
        log = sh(root, "git", "log", "--name-only", "--date=short",
                 "--pretty=format:%x01%H%x02%ad%x02%s")
        cur = None
        for line in log.splitlines():
            if line.startswith("\x01"):
                h, d, s = line[1:].split("\x02", 2)
                cur = (h[:7], d, s)
            elif line.strip() and cur:
                f = line.strip()
                # git log walks newest -> oldest
                if f not in last:
                    last[f] = cur
                first[f] = cur
                count[f] = count.get(f, 0) + 1
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for fn in filenames:
                ap = Path(dirpath) / fn
                rel = str(ap.relative_to(root))
                # T3_DERIVED self-exclusion: this pipeline's own outputs are not
                # subjects of the survey. Including them makes the manifest
                # self-referential and non-deterministic (cf. DE-0132).
                if repo == "egl" and rel.startswith("structure/") and ap.suffix == ".jsonl":
                    continue
                ext = ap.suffix.lower()
                is_tracked = rel in tracked
                try:
                    st = ap.stat()
                    h = hashlib.sha256(ap.read_bytes()).hexdigest()
                except (OSError, PermissionError):
                    continue
                f0, f1 = first.get(rel), last.get(rel)
                de = None
                if f0 and DE_RE.search(f0[2]):
                    de = DE_RE.search(f0[2]).group(0)
                rows.append({
                    "repo": repo, "relative_path": rel, "absolute_path": str(ap),
                    "trust_tier": "T1_TRACKED" if is_tracked else "T2_RUNTIME",
                    "tracked": is_tracked,
                    "git_first_commit": f0[0] if f0 else None,
                    "git_first_date": f0[1] if f0 else None,
                    "git_first_subject": f0[2] if f0 else None,
                    "git_last_commit": f1[0] if f1 else None,
                    "git_last_date": f1[1] if f1 else None,
                    "commit_count": count.get(rel, 0),
                    "mtime": int(st.st_mtime), "size": st.st_size, "sha256": h,
                    "extension": ext, "language": LANG.get(ext, "other"),
                    "classification": classify(rel, ext, is_tracked),
                    "generated": bool(GEN_HINT.search("/" + rel)),
                    "introduced_by_de": de,
                    "derived_from": "git+filesystem", "regenerable": True,
                })
    rows.sort(key=lambda r: (r["repo"], r["relative_path"]))
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"{len(rows)} rows -> {OUT}")
    return rows

if __name__ == "__main__":
    main()
