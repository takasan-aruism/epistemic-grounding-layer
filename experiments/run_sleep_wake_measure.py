#!/usr/bin/env python3
"""local wake latency 実測(§5 MEASUREMENT need, AEC AC-4)。
vLLM Sleep Mode(level 1: weights を CPU offload)を実 enable し、sleep/wake 往復の latency を計測。
現在の docker full-reload swap(~174.5s, DE-0074)と比較。DECLARED でなく MEASURED を作る。"""
import json, time, subprocess, urllib.request, urllib.error
from pathlib import Path

BASE = "http://localhost:8005"
def post(path, timeout=200):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + path, data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(); return round(time.time() - t0, 1), r.status
    except urllib.error.HTTPError as e:
        return round(time.time() - t0, 1), e.code
    except Exception as e:
        return round(time.time() - t0, 1), f"ERR:{type(e).__name__}"

def is_sleeping():
    try:
        with urllib.request.urlopen(BASE + "/is_sleeping", timeout=10) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)[:60]}

def gpu():
    o = subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True,
                       capture_output=True, text=True).stdout.split()
    return [int(x) for x in o if x.strip().isdigit()]

def gen(seed=0):
    body = json.dumps({"model": "Qwen3.6-35B-A3B", "temperature": 0, "seed": seed, "max_tokens": 20,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "user", "content": "Reply with exactly: hello world"}]}).encode()
    try:
        req = urllib.request.Request(BASE + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            c = json.load(r)["choices"][0]["message"].get("content") or ""
            return c[:40], not (c.count("!") > 8 or c.strip() == "")
    except Exception as e:
        return f"ERR:{type(e).__name__}", False

def main():
    out = {"model": "Qwen3.6-35B-A3B-NVFP4 (tp2)", "sleep_level": 1, "baseline_swap_s": 174.5, "cycles": []}
    print("### vLLM Sleep Mode wake-latency measurement ###\n")
    # ensure awake
    st = is_sleeping()
    print(f"[initial] is_sleeping={st}")
    if st.get("is_sleeping"):
        lat, code = post("/wake_up"); print(f"  woke initial sleep in {lat}s (http {code})")
    g0 = gpu(); print(f"[awake] GPU used={g0} MiB")
    txt, ok = gen(); print(f"[awake] generate: {txt!r} coherent={ok}")

    for i in range(1, 4):
        c = {"cycle": i}
        g_before = gpu()
        s_lat, s_code = post("/sleep?level=1")
        g_sleep = gpu()
        w_lat, w_code = post("/wake_up")
        g_wake = gpu()
        txt, ok = gen(seed=i)
        c.update({"gpu_before": g_before, "sleep_s": s_lat, "sleep_http": s_code, "gpu_asleep": g_sleep,
                  "wake_s": w_lat, "wake_http": w_code, "gpu_awake": g_wake, "gen": txt, "gen_coherent": ok,
                  "gpu_freed_mib": [b - a for b, a in zip(g_before, g_sleep)]})
        out["cycles"].append(c)
        print(f"[cycle {i}] sleep={s_lat}s(http {s_code}) gpu {g_before}->{g_sleep} (freed {c['gpu_freed_mib']}) | "
              f"wake={w_lat}s(http {w_code}) gpu->{g_wake} | gen={txt!r} coherent={ok}")

    wakes = [c["wake_s"] for c in out["cycles"] if isinstance(c["wake_http"], int) and c["wake_http"] == 200]
    sleeps = [c["sleep_s"] for c in out["cycles"] if isinstance(c["sleep_http"], int) and c["sleep_http"] == 200]
    out["avg_wake_s"] = round(sum(wakes) / len(wakes), 1) if wakes else None
    out["avg_sleep_s"] = round(sum(sleeps) / len(sleeps), 1) if sleeps else None
    out["all_coherent"] = all(c["gen_coherent"] for c in out["cycles"])
    out["speedup_vs_docker_swap"] = round(174.5 / out["avg_wake_s"], 1) if out["avg_wake_s"] else None
    print(f"\n=== MEASURED ===")
    print(f"  avg wake latency = {out['avg_wake_s']}s  (avg sleep = {out['avg_sleep_s']}s)")
    print(f"  vs docker full-reload swap 174.5s -> speedup {out['speedup_vs_docker_swap']}x")
    print(f"  coherent after every wake: {out['all_coherent']}")
    Path("/home/takasan/egl/experiments/sleep_wake_measured.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> sleep_wake_measured.json 保存")

if __name__ == "__main__":
    main()
