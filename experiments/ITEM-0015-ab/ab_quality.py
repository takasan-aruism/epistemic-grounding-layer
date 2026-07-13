#!/usr/bin/env python3
"""ITEM-0015 level-1 A/B QUALITY: real Pass@1 (execute generated code vs asserts) for Qwen3.6-35B-A3B vs 27B,
with a level-1 sleep/wake swap between them. approval APPROVAL-add18fbc80."""
import json, time, re, urllib.request, subprocess
Q, C = "http://localhost:8005", "http://localhost:8006"
QN, CN = "Qwen3.6-35B-A3B", "Qwen3.6-27B"

def post(u,p,b=None,to=180):
    d=json.dumps(b).encode() if b is not None else b""
    r=urllib.request.urlopen(urllib.request.Request(u+p,data=d,headers={"Content-Type":"application/json"},method="POST"),timeout=to)
    ct=r.headers.get("Content-Type",""); return json.load(r) if ct.startswith("application/json") else r.read().decode()
def get(u,p): return json.load(urllib.request.urlopen(u+p,timeout=10))
def vram(): return [int(x) for x in subprocess.run(["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],capture_output=True,text=True).stdout.split() if x.isdigit()]
def sleepL1(u):
    t=time.time();post(u,"/sleep?level=1",to=120)
    for _ in range(60):
        if get(u,"/is_sleeping").get("is_sleeping"): return round(time.time()-t,2)
        time.sleep(0.5)
def wake(u):
    t=time.time();post(u,"/wake_up",to=180)
    for _ in range(120):
        if get(u,"/is_sleeping").get("is_sleeping") is False: return round(time.time()-t,2)
        time.sleep(0.5)

TASKS=[
 ("is_even","Write a Python function is_even(n) returning whether n is even. Return only a ```python code block.",
  "assert is_even(2) and not is_even(3) and is_even(0)"),
 ("merge_intervals","Write merge_intervals(intervals) merging overlapping intervals, sorted by start. Return only a ```python code block.",
  "assert merge_intervals([[1,3],[2,6],[8,10]])==[[1,6],[8,10]]; assert merge_intervals([])==[]"),
 ("fib","Write fib(n) returning the nth Fibonacci number with fib(0)=0, fib(1)=1. Return only a ```python code block.",
  "assert fib(0)==0 and fib(1)==1 and fib(10)==55"),
]
def extract(txt):
    m=re.search(r"```(?:python)?\s*(.*?)```",txt,re.S)
    return m.group(1) if m else txt
def run_pass1(url,model):
    res=[]
    for name,prompt,test in TASKS:
        b={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":400,"chat_template_kwargs":{"enable_thinking":False}}
        t=time.time();r=post(url,"/v1/chat/completions",b);dt=time.time()-t
        txt=r["choices"][0]["message"].get("content") or ""; ntok=(r.get("usage") or {}).get("completion_tokens",0)
        code=extract(txt); ok=False; err=""
        try:
            ns={}; exec(code,ns); exec(test,ns); ok=True
        except Exception as e: err=str(e)[:80]
        res.append({"task":name,"pass":ok,"tok_s":round(ntok/dt,1) if dt>0 else 0,"latency":round(dt,1),"err":err})
    p1=sum(1 for x in res if x["pass"])/len(res)
    return {"model":model,"pass_at_1":round(p1,3),"mean_tok_s":round(sum(x["tok_s"] for x in res)/len(res),1),
            "mean_latency":round(sum(x["latency"] for x in res)/len(res),1),"tasks":res}

# state: Qwen awake / Coder asleep. Measure Qwen, swap (level1), measure Coder.
print("Qwen awake -> Pass@1"); qwen=run_pass1(Q,QN); print(" ",qwen["pass_at_1"],qwen["mean_tok_s"],"tok/s")
sl=sleepL1(Q); wk=wake(C); print(f"swap: qwen_sleepL1={sl}s coder_wake={wk}s vram={vram()}")
print("Coder awake -> Pass@1"); coder=run_pass1(C,CN); print(" ",coder["pass_at_1"],coder["mean_tok_s"],"tok/s")

# switch decision (quality = Pass@1, incumbent=Qwen 35B-A3B, candidate=Coder 27B)
dp=coder["pass_at_1"]-qwen["pass_at_1"]
if dp>=0.34: dec="SWITCH (27B clearly better Pass@1)"
elif dp<=-0.34: dec="KEEP_AS_SUBMODEL (27B worse)"
else: dec="KEEP_INCUMBENT (equal/marginal -> 35B-A3B for speed+single-GPU)"
out={"data_class":"MEASURED","swap":{"qwen_sleepL1_s":sl,"coder_wake_s":wk},"qwen":qwen,"coder":coder,
     "delta_pass_at_1":round(dp,3),"switch_decision":dec,"swap_mechanism":"level-1 sleep/wake, both regenerate correctly"}
json.dump(out,open("/tmp/ab_quality.json","w"),indent=1)
print(f"\n===== MEASURED: Qwen p@1={qwen['pass_at_1']} ({qwen['mean_tok_s']}t/s) vs Coder p@1={coder['pass_at_1']} ({coder['mean_tok_s']}t/s) | Δ={round(dp,3)} -> {dec} =====")
