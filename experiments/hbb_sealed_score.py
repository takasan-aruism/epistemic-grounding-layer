import json
CAND={x["id"]:x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
# Independent Hint Sufficiency depth (external-weight, anonymized-merit scoring)
D={
"HBB-01":{"A":0,"B":3,"F":4,"C":0,"D":0},"HBB-03":{"A":0,"B":0,"F":0,"C":0,"D":0},
"HBB-05":{"A":0,"B":4,"F":3,"C":2,"D":3},"HBB-06":{"A":0,"B":3,"F":3,"C":2,"D":4},
"HBB-08":{"A":0,"B":2,"F":0,"C":2,"D":0},"HBB-10":{"A":4,"B":4,"F":2,"C":2,"D":2},
"HBB-11":{"A":0,"B":3,"F":0,"C":0,"D":4},"HBB-12":{"A":0,"B":2,"F":0,"C":0,"D":4},
"HBB-13":{"A":0,"B":3,"F":0,"C":2,"D":2},"HBB-17":{"A":0,"B":4,"F":0,"C":3,"D":0},
"HBB-24":{"A":0,"B":2,"F":0,"C":0,"D":0},
}
ids=list(D); AA=[k for k in ids if CAND[k]["intervention_scope"].startswith("ARUISM")]; FOS=[k for k in ids if k not in AA]
def rc(arm,S): return [k for k in S if D[k][arm]>0]
print("### SEALED result (external-weight, N=11 local; HBB-04/30=GPT handoff) ###")
print("incident sc | A B F C D | breakthrough")
for k in ids:
    sc=CAND[k]["intervention_scope"][:2]
    print("  %s %s | %d %d %d %d %d | %s"%(k,sc,D[k]["A"],D[k]["B"],D[k]["F"],D[k]["C"],D[k]["D"],CAND[k]["breakthrough_structure"][:44]))
print("\nBreakthrough Reach:")
for arm in "ABFCD": print("  %s: total %d/11 | AA %d/6 | FOS %d/5"%(arm,len(rc(arm,ids)),len(rc(arm,AA)),len(rc(arm,FOS))))
# H_primary: B∪C on AA
BA=set(rc("B",AA)); CA=set(rc("C",AA)); BC=BA|CA
print("\n=== H_primary (B∪C complementarity on AA) ===")
print("  B on AA: %s (%d)"%(sorted(BA),len(BA)))
print("  C on AA: %s (%d)"%(sorted(CA),len(CA)))
print("  B∪C on AA: %d | max(B,C): %d | C-unique(C∖B): %s"%(len(BC),max(len(BA),len(CA)),sorted(CA-BA)))
print("  H_primary [B∪C>max(B,C) AND C-unique>=1]: %s"%("CONFIRMED" if len(BC)>max(len(BA),len(CA)) and len(CA-BA)>=1 else "NOT_CONFIRMED"))
# D-SECONDARY
DA=set(rc("D",AA))
print("\n=== D-SECONDARY (null: D does not beat B on AA) ===")
print("  D on AA: %s (%d) | B on AA: %d | null[D<=B]: %s"%(sorted(DA),len(DA),len(BA),"HOLDS" if len(DA)<=len(BA) else "REJECTED"))
print("  D-unique on AA (D∖B): %s | D H0-reaches: %s"%(sorted(DA-BA),[k for k in ids if D[k]["D"]==4]))
json.dump({"depths":D,"AA":AA,"FOS":FOS,"H_primary":"NOT_CONFIRMED" if not(len(BC)>max(len(BA),len(CA)) and len(CA-BA)>=1) else "CONFIRMED","B_AA":sorted(BA),"C_AA":sorted(CA),"C_unique_AA":sorted(CA-BA),"D_AA":sorted(DA),"reach":{a:{"total":len(rc(a,ids)),"AA":len(rc(a,AA)),"FOS":len(rc(a,FOS))} for a in "ABFCD"},"scorer":"Claude external-weight; external cross-review required"},open("/home/takasan/egl/experiments/hbb_sealed_scored.json","w"),ensure_ascii=False,indent=2)
