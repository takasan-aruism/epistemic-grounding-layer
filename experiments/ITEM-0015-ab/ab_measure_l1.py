#!/usr/bin/env python3
"""ITEM-2DER-EVO-0015 live A/B sleep/wake measurement. Qwen3.6-35B-A3B (:8005) vs Coder 27B (:8006), no-fp8-KV,
util 0.85, TP=2, --enable-sleep-mode. Measures sleep/wake latency, VRAM, gen latency, tokens/sec, coding-workload
success, over 3 round-trips. NO success unless both regenerate each cycle. approval APPROVAL-level1-rerun."""
import json, time, urllib.request, subprocess

Q, C = "http://localhost:8005", "http://localhost:8006"
QNAME, CNAME = "Qwen3.6-35B-A3B", "Qwen3.6-27B"

def _post(url, path, body=None, timeout=180):
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r) if r.headers.get("Content-Type","").startswith("application/json") else r.read().decode()

def _get(url, path, timeout=10):
    with urllib.request.urlopen(url + path, timeout=timeout) as r:
        return json.load(r)

def is_sleeping(url):
    try: return bool(_get(url, "/is_sleeping").get("is_sleeping"))
    except Exception: return None

def vram():
    out = subprocess.run(["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.split()
    return [int(x) for x in out if x.isdigit()]

def sleep_model(url):
    t=time.time(); _post(url, "/sleep?level=1", timeout=120)
    for _ in range(120):
        if is_sleeping(url) is True: return round(time.time()-t,2)
        time.sleep(0.5)
    return None  # failed to confirm sleep

def wake_model(url):
    t=time.time(); _post(url, "/wake_up", timeout=180)
    for _ in range(240):
        if is_sleeping(url) is False: return round(time.time()-t,2)
        time.sleep(0.5)
    return None

CODING_PROMPT = ("Write a Python function merge_intervals(intervals) that merges overlapping intervals and "
                 "returns the merged list sorted by start. Include a couple of assert-based tests. Return only code.")

def generate(url, model, prompt=CODING_PROMPT, max_tokens=384):
    body={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":max_tokens,
          "chat_template_kwargs":{"enable_thinking":False}}
    t=time.time(); r=_post(url,"/v1/chat/completions",body,timeout=180); dt=time.time()-t
    txt=r["choices"][0]["message"].get("content") or ""
    ntok=(r.get("usage") or {}).get("completion_tokens") or 0
    ok = len(txt.strip())>20 and ("def " in txt or "```" in txt)   # non-empty + looks like code (not garbage)
    return {"latency_s":round(dt,2),"tokens":ntok,"tok_per_s":round(ntok/dt,1) if dt>0 else 0,
            "output_ok":ok,"preview":txt.strip()[:70].replace(chr(10)," ")}

log={"approval_id":"APPROVAL-level1-rerun","round_trips":[],"errors":[]}

# setup: reach Qwen awake / Coder asleep (currently Coder awake / Qwen asleep)
print("SETUP: Coder sleep -> Qwen wake (target: Qwen awake / Coder asleep)")
log["setup_coder_sleep_s"]=sleep_model(C)
log["setup_qwen_wake_s"]=wake_model(Q)
print(f"  coder_sleep={log['setup_coder_sleep_s']}s qwen_wake={log['setup_qwen_wake_s']}s vram={vram()}")

for rt in range(1,4):
    print(f"\n=== ROUND-TRIP {rt}/3 ===")
    cyc={"rt":rt}; t0=time.time()
    # 1. Qwen generate (awake)
    cyc["qwen_gen"]=generate(Q,QNAME); print(f"  qwen_gen: {cyc['qwen_gen']}")
    cyc["vram_qwen_awake"]=vram()
    # 2. sleep Qwen -> wake Coder
    cyc["qwen_sleep_s"]=sleep_model(Q); cyc["vram_after_qwen_sleep"]=vram()
    cyc["coder_wake_s"]=wake_model(C)
    # 3. Coder generate (coding workload)
    cyc["coder_gen"]=generate(C,CNAME); print(f"  coder_gen: {cyc['coder_gen']}")
    cyc["vram_coder_awake"]=vram()
    # 4. sleep Coder -> wake Qwen
    cyc["coder_sleep_s"]=sleep_model(C); cyc["vram_after_coder_sleep"]=vram()
    cyc["qwen_wake_s"]=wake_model(Q)
    # 5. Qwen regenerate (resume check)
    cyc["qwen_resume"]=generate(Q,QNAME,prompt="Reply with exactly: OK",max_tokens=8); print(f"  qwen_resume: {cyc['qwen_resume']}")
    cyc["round_trip_total_s"]=round(time.time()-t0,2)
    # cycle success = both models regenerated + all transitions confirmed
    fails=[k for k in ("qwen_sleep_s","coder_wake_s","coder_sleep_s","qwen_wake_s") if cyc.get(k) is None]
    cyc["success"]=bool(cyc["qwen_gen"]["output_ok"] and cyc["coder_gen"]["output_ok"] and cyc["qwen_resume"]["output_ok"] and not fails)
    if fails: log["errors"].append(f"rt{rt}: transition timeout {fails}")
    print(f"  -> success={cyc['success']} total={cyc['round_trip_total_s']}s")
    log["round_trips"].append(cyc)

log["all_success"]=all(c["success"] for c in log["round_trips"])
log["n_success"]=sum(1 for c in log["round_trips"] if c["success"])
json.dump(log, open("/tmp/ab_result.json","w"), indent=1)
print(f"\n===== A/B RESULT: {log['n_success']}/3 round-trips succeeded | all_success={log['all_success']} | errors={log['errors']} =====")
