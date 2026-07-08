import json
CAND={x["id"]:x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
mine=json.load(open("/home/takasan/egl/experiments/hbb_sealed_scored.json"))["depths"]
blind=json.load(open("/home/takasan/egl/experiments/hbb_sealed_blindscore.json"))
ids=list(mine); AA=[k for k in ids if CAND[k]["intervention_scope"].startswith("ARUISM")]; FOS=[k for k in ids if k not in AA]
# blind reach set per arm
braw={a:set() for a in "ABFCD"}
for a in "ABFCD":
    braw[a]=set(blind[f"{a}_AA"]) if f"{a}_AA" in blind else set()
# reconstruct blind full reach from scored
bs={}
for s in blind["scored"]:
    if s["recover"]=="YES": bs.setdefault(s["arm"],set()).add(s["id"])
def mine_reach(a): return set(k for k in ids if mine[k][a]>0)
def blind_reach(a): return bs.get(a,set())
print("=== reach 比較(私 strict vs Qwen lenient vs consensus=両者一致)===")
print("arm | mine(total/AA) | qwen(total/AA) | consensus(total/AA)")
cons={}
for a in "ABFCD":
    m=mine_reach(a); q=blind_reach(a); c=m&q
    cons[a]=c
    print(f"  {a} | {len(m)}/{len(m&set(AA))} | {len(q)}/{len(q&set(AA))} | {len(c)}/{len(c&set(AA))}")
print("\n=== H_primary を3 scorer 全部で ===")
for name,reach in [("mine",mine_reach),("qwen",blind_reach),("consensus",lambda a:cons[a])]:
    BA=reach("B")&set(AA); CA=reach("C")&set(AA); DA=reach("D")&set(AA)
    cu=sorted(CA-BA); du=sorted(DA-BA)
    hp = (len(BA|CA)>max(len(BA),len(CA))) and (len(cu)>=1 or len(du)>=1)
    print(f"  [{name}] C-unique={cu} D-unique={du} | H_primary={'CONFIRMED' if hp else 'NOT_CONFIRMED'}")
print("\n=== 判定 ===")
print("- 絶対 reach は scorer 依存で信頼不能(私 engine 6/11 < B 10/11 / Qwen engine 11/11 > B 10/11)")
print("- C-unique=D-unique=0 は 3 scorer 全部で一致 → H_primary NOT_CONFIRMED は robust")
print("- しかし『B が engine を支配』は私の scoring 固有の artifact(Qwen では逆)→ §5 report のこの framing は撤回すべき")
json.dump({"mine":{a:sorted(mine_reach(a)) for a in "ABFCD"},"qwen":{a:sorted(blind_reach(a)) for a in "ABFCD"},"consensus":{a:sorted(cons[a]) for a in "ABFCD"},"robust_finding":"C-unique=D-unique=0 across all 3 scorers (H_primary NOT_CONFIRMED robust); absolute reach scorer-dependent (unreliable); 'B dominates engine' was my-scoring artifact"},open("/home/takasan/egl/experiments/hbb_recheck.json","w"),ensure_ascii=False,indent=2)
