#!/usr/bin/env python3
"""Stage 5: HISTORY_EVENTS.jsonl — deterministic. Spec v0.1 §5 (unchanged in v0.2).
No narrative generation. Events are extracted, phases are cut at measured boundaries:
a phase boundary is a commit that introduces a NEW cross-component dependency
(the birth of an edge), not a subjective chapter break.
"""
import ast, json, re, subprocess, collections
from pathlib import Path

HOME = Path("/home/takasan"); S = HOME/"egl/structure"
REPOS = ["egl", "twoder", "dev-workcell", "rri", "ds"]
DE = re.compile(r"DE-\d{4}"); ITEM = re.compile(r"ITEM-[A-Z0-9\-]+")
CHG = re.compile(r"CHG-\d{4}"); JREV = re.compile(r"JREV-\d{4}")

DIR_RULE = [("ds/ds/","DS"),("rri/rri/","RRI"),("dw/","DW"),("egl/","EGL"),
            ("autonomy/","EGL_AUTONOMY"),("experiments/","EXPERIMENT"),("docs/","DOCS"),
            ("regression/","TEST"),("audit/","AUDIT"),("tools/","TOOLS")]
def comp_of(repo, rel):
    if rel.startswith("test") or "/test" in "/"+rel or "regression/" in rel: return "TEST"
    for pre,n in DIR_RULE:
        if rel.startswith(pre): return n
    if repo=="twoder": return "TWODER"
    if repo=="dev-workcell": return "DW"
    return {"egl":"EGL","rri":"RRI","ds":"DS"}.get(repo,"OTHER")

def modcomp(mod):
    m = mod.lstrip(".").split(".")[0]
    return {"egl":"EGL","rri":"RRI","ds":"DS","dw":"DW","twoder":"TWODER"}.get(m)

def sh(cwd,*a): return subprocess.run(a,cwd=cwd,capture_output=True,text=True).stdout

def imports_of(cwd, sha, path):
    src = sh(cwd,"git","show",f"{sha}:{path}")
    if not src: return set()
    try: t = ast.parse(src)
    except Exception: return set()
    out=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names:
                c=modcomp(a.name)
                if c: out.add(c)
        elif isinstance(n,ast.ImportFrom):
            c=modcomp(n.module or "")
            if c: out.add(c)
    return out

events=[]
for repo in REPOS:
    cwd=HOME/repo
    log=sh(cwd,"git","log","--reverse","--date=short","--name-status",
           "--pretty=format:%x01%H%x02%ad%x02%P%x02%s")
    cur=None; changed=[]
    def flush():
        global cur,changed
        if not cur: return
        sha,date,parents,subj = cur
        comps=sorted({comp_of(repo,f) for _,f in changed})
        pys=[f for st,f in changed if f.endswith(".py") and st!="D"]
        new_dep=[]
        if len(changed)<=40 and parents.strip():
            par=parents.split()[0]
            for f in pys[:12]:
                after=imports_of(cwd,sha,f)
                before=imports_of(cwd,par,f)
                born=after-before
                own=comp_of(repo,f)
                for b in sorted(born):
                    if b!=own: new_dep.append(f"{own}({repo}/{f}) -> {b}")
        events.append({
            "date":date,"repo":repo,"commit":sha[:7],"subject":subj,
            "changed_files":len(changed),
            "changed_py":[f for f in pys][:20],
            "components_touched":comps,
            "de_refs":sorted(set(DE.findall(subj))),
            "item_refs":sorted(set(ITEM.findall(subj))),
            "chg_refs":sorted(set(CHG.findall(subj))),
            "jrev_refs":sorted(set(JREV.findall(subj))),
            "new_cross_component_deps":new_dep,
            "is_edge_birth":bool(new_dep),
            "trust_tier":"T3_DERIVED","regenerable":True,
            "derived_from":"git log --name-status + AST import diff vs parent",
        })
        cur=None; changed=[]
    for line in log.splitlines():
        if line.startswith("\x01"):
            flush()
            h,d,p,s2=line[1:].split("\x02",3); cur=(h,d,p,s2)
        elif line.strip() and cur:
            parts=line.split("\t")
            if len(parts)>=2: changed.append((parts[0],parts[-1]))
    flush()

events.sort(key=lambda e:(e["date"],e["repo"],e["commit"]))
(S/"HISTORY_EVENTS.jsonl").write_text("\n".join(json.dumps(e,ensure_ascii=False) for e in events)+"\n")
print(f"history events: {len(events)}")
births=[e for e in events if e["is_edge_birth"]]
print(f"edge-birth commits: {len(births)}")
print("\n=== 系統間の辺が生まれた commit（フェーズ境界の候補）===")
seen=set()
for e in births:
    for d in e["new_cross_component_deps"]:
        pair=(d.split("(")[0], d.split("-> ")[-1])
        if pair[0]==pair[1] or pair in seen: continue
        seen.add(pair)
        print(f"  {e['date']}  {e['repo']:12s} {pair[0]:12s} -> {pair[1]:12s}  {e['subject'][:64]}")
print()
byday=collections.Counter(e["date"] for e in events)
print("commits/day:", " ".join(f"{d[-5:]}:{n}" for d,n in sorted(byday.items())))
