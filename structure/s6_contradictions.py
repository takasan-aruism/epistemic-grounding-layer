#!/usr/bin/env python3
"""Stage 6: CONTRADICTIONS.jsonl + lineage classification. Deterministic.
spec v0.1 §6.1 listed 7 contradiction types, 5 mechanical + 2 for the LLM.
v0.2 moved a 6th to the mechanical side. This implementation mechanises all 7:
  - "same component described differently" -> measured as divergence across the 3
    consensus seeds' purpose_1line variants (no LLM judgement needed)
  - "same authority claimed by multiple stores" -> ledger files written from >1 component
"""
import json, re, collections, difflib
from pathlib import Path
S = Path("/home/takasan/egl/structure"); HOME = Path("/home/takasan")
man   = {f"{r['repo']}/{r['relative_path']}": r for r in map(json.loads, open(S/"FILE_MANIFEST.jsonl"))}
sym   = {r["key"]: r for r in map(json.loads, open(S/"SYMBOL_INDEX.jsonl"))}
reach = {r["key"]: r for r in map(json.loads, open(S/"REACHABILITY.jsonl"))}
cons  = {r["key"]: r for r in map(json.loads, open(S/"FILE_EXTRACTION_CONSENSUS.jsonl"))}
items = [json.loads(l) for l in open(S/"ITEM_LADDER.jsonl")]
comps = {r["component_id"]: r for r in map(json.loads, open(S/"COMPONENT_INVENTORY.jsonl"))}
edges = [json.loads(l) for l in open(S/"EDGE_INVENTORY.jsonl")]

C = []
def add(t, sev, subject, detail, ev):
    C.append({"type": t, "severity": sev, "subject": subject, "detail": detail,
              "evidence": ev, "trust_tier": "T3_DERIVED", "regenerable": True,
              "derived_from": "mechanical join over the derived layer"})

# tests index: which module each test_* targets
tests_for = collections.defaultdict(list)
for k, r in sym.items():
    if r.get("test_target"):
        tests_for[r["test_target"]].append(k)

srcs = [k for k, r in man.items() if r["extension"] == ".py" and r["classification"] == "source"
        and r["trust_tier"] == "T1_TRACKED"]

# --- 1. doc says implemented / code absent ---------------------------------
md_refs = collections.Counter()
for r in sym.values():
    if r["language"] == "markdown":
        for cr in r.get("code_refs", []): md_refs[cr] += 1
have = {k.split("/")[-1] for k in man}
for base, n in md_refs.items():
    if base not in have:
        add("DOC_CLAIMS_FILE_THAT_DOES_NOT_EXIST", "MED", base,
            f"{n} 件の md が {base} を参照しているが、5 リポのどこにも存在しない", [])

# --- 2. code exists / no caller (and not an entrypoint) --------------------
for k in srcs:
    r = sym[k]
    if not r["imported_by"] and not r.get("cli_entrypoints") and reach.get(k, {}).get("reach_category") == "ORPHAN":
        add("CODE_WITH_NO_CALLER", "LOW", k,
            f"{r.get('loc',0)} LOC / 定義 {len(r.get('defines',[]))} 個、呼出元 0・CLI なし", [k])

# --- 3. wired but no test ---------------------------------------------------
# CORRECTNESS: "no file named test_<module>.py" is a NAMING proxy, not evidence of being
# untested. The admissible check is: does ANY test file import this module?
def test_importers(k):
    return [i for i in sym.get(k, {}).get("imported_by", [])
            if man.get(i, {}).get("classification") == "test" or "/test" in "/" + i
            or i.split("/")[-1].startswith("test_")]
for k in srcs:
    if reach.get(k, {}).get("wired"):
        ti = test_importers(k)
        if not ti:
            add("LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST", "HIGH", k,
                "live path 到達だが、いかなるテストからも import されていない", [k])
        elif not tests_for.get(k.split("/")[-1][:-3]):
            add("LIVE_CODE_TESTED_ONLY_INDIRECTLY", "LOW", k,
                f"専用の test_<name>.py は無いが {len(ti)} 本のテストから間接的に import される",
                [k] + ti[:2])

# --- 4. tested but no runtime evidence -------------------------------------
DIR_RULE = [("ds/ds/","DS"),("rri/rri/","RRI"),("dev-workcell/dw/","DW"),("egl/egl/","EGL")]
def comp_of(k):
    for p,n in DIR_RULE:
        if k.startswith(p): return n
    return "TWODER" if k.startswith("twoder/") else "OTHER"
for k in srcs:
    base = k.split("/")[-1][:-3]
    if test_importers(k) and not reach.get(k, {}).get("wired"):
        add("TESTED_BUT_NOT_ON_LIVE_PATH", "MED", k,
            f"test {len(test_importers(k))} 本から import され、live path 未到達 "
            f"({reach.get(k,{}).get('reach_category')})", [k] + tests_for[base][:2])

# --- 5/6. ROADMAP DONE vs measured ladder ----------------------------------
for it in items:
    if it["roadmap_status"] != "DONE": continue
    if not it["bound_files"]:
        add("ROADMAP_DONE_UNVERIFIABLE", "MED", it["item_id"],
            "DONE だがファイル束縛が解決できない（命名規約外）→ 検証不能", [])
    elif it["ladder"]["wired"] == "NO":
        add("ROADMAP_DONE_BUT_NOT_WIRED", "HIGH", it["item_id"],
            f"DONE だが live path 未到達。importers={it['importers'][:3]}",
            it["bound_files"])

# --- 7a. same component described differently (seed divergence, mechanical) --
for k, r in cons.items():
    v = [x for x in r.get("purpose_1line_variants", []) if x]
    if len(v) >= 2:
        sims = [difflib.SequenceMatcher(None, v[0], x).ratio() for x in v[1:]]
        if sims and max(sims) < 0.35:
            add("DESCRIPTION_UNSTABLE_ACROSS_SEEDS", "LOW", k,
                f"3 シードの purpose_1line が相互に不一致 (max similarity {max(sims):.2f})", [k])

# --- 7b. same store written from more than one component --------------------
writers = collections.defaultdict(set)
for k in srcs:
    for w in sym[k].get("file_writes", []):
        t = w.get("target")
        if t and (".jsonl" in str(t) or ".json" in str(t)):
            writers[str(t)].add(comp_of(k))
for store, cs in writers.items():
    if len(cs) > 1:
        add("STORE_WRITTEN_BY_MULTIPLE_COMPONENTS", "HIGH", store,
            f"書き手コンポーネントが複数: {sorted(cs)}", [])

C.sort(key=lambda x: ({"HIGH":0,"MED":1,"LOW":2}[x["severity"]], x["type"], x["subject"]))
(S/"CONTRADICTIONS.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in C)+"\n")

# --- lineage classification (spec §5) --------------------------------------
LOOP = {"DS","RRI","DW","EGL"}
SAFETY = re.compile(r"(authority|gate|guard|admission|failure_memory|policy|validator|etb|preflight)")
OBS    = re.compile(r"(log|trace|inspect|report|dashboard|forecast|ledger|registry|event)")
HANDOFF= re.compile(r"(webui|control_surface|command_surface|offramp|autonomous_git|dep_flag)")
lin = []
for k in [x for x in man if man[x]["extension"]==".py"]:
    rc = reach.get(k, {}).get("reach_category")
    b = k.split("/")[-1]
    if rc == "LIVE_REACHABLE":
        if HANDOFF.search(b): c = "migration_handoff"
        elif SAFETY.search(b): c = "safety_support"
        elif OBS.search(b): c = "observability"
        else: c = "core_path"
    elif rc == "TEST_ONLY":  c = "test"
    elif rc == "ARCHIVE_OR_EXPERIMENT": c = "experimental_branch"
    elif rc in ("ORPHAN",):  c = "historical_residue"
    else: c = "unwired_support"
    lin.append({"key": k, "lineage": c, "reach_category": rc,
                "loc": sym.get(k,{}).get("loc",0), "trust_tier":"T3_DERIVED","regenerable":True})
(S/"LINEAGE.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in lin)+"\n")

print(f"contradictions: {len(C)}")
for t,n in collections.Counter(x["type"] for x in C).most_common():
    sev = next(x["severity"] for x in C if x["type"]==t)
    print(f"  {n:4d}  [{sev:4s}] {t}")
print("\n=== HIGH の内訳 ===")
for t,n in collections.Counter(x["type"] for x in C if x["severity"]=="HIGH").most_common():
    print(f"  {n:4d}  {t}")
print("\n=== STORE_WRITTEN_BY_MULTIPLE_COMPONENTS ===")
for x in C:
    if x["type"]=="STORE_WRITTEN_BY_MULTIPLE_COMPONENTS": print("   ",x["subject"],"|",x["detail"])
print("\n=== LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST ===")
for x in [y for y in C if y["type"]=="LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST"]: print("   ",x["subject"])
print("\n(注) file_writes のリテラル解決率が低いため STORE_WRITTEN_BY_MULTIPLE_COMPONENTS は"
      " 過小検出。0 件は「無い」ではなく「この手法では見えない」。")
print("\n=== 系譜分類 (LOC) ===")
agg=collections.Counter(); loc=collections.Counter()
for x in lin: agg[x["lineage"]]+=1; loc[x["lineage"]]+=x["loc"]
for k in sorted(agg,key=lambda z:-loc[z]): print(f"  {agg[k]:4d} files {loc[k]:7d} LOC  {k}")
