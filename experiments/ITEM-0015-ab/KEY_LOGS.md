# ITEM-0015-ab — 主要 stdout/stderr (verbatim 抜粋)

失敗コンテナの docker logs は container 削除で消失。以下は実行中に採取した critical 行の逐語抜粋。

## 1. level-2 + both-awake → OOM (Coder init, DE-0237)
```
(Worker_TP1 pid=499) torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 144.00 MiB.
GPU 1 has a total capacity of 31.35 GiB of which 132.25 MiB is free. Including non-PyTorch memory,
this process has 16.37 GiB memory in use.
(EngineCore) RuntimeError: Engine core initialization failed.
```
→ 原因: Qwen awake(~15GB) のまま Coder(~14.4GB weights) init。起動順の問題。

## 2. level-2 + util 0.45 → KV 確保不能 (Coder init, DE-0237)
```
(EngineCore) ValueError: No available memory for the cache blocks.
Try increasing `gpu_memory_utilization` when initializing the engine.
```
→ util 0.45 は 27B weights でほぼ消費、KV 残らず。→ 0.85 必要。

## 3. level-2 + /wake_up (reload_weights 無し) → GARBAGE (DE-0237)
```
qwen_gen : output '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!' output_ok=False
coder_gen: output '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!' output_ok=False
A/B RESULT: 0/3 round-trips succeeded
```
→ level2 は weights を破棄。/wake_up はメモリ再確保のみ、weights 未復元 → garbage。**手順不備**。

## 4. no-fp8-kv + no-sleep (isolation, DE-0238) → HEALTHY
```
prompt='Reply with exactly: HELLO' -> garbage=False out='HELLO'
prompt='is_even(n)'               -> garbage=False out='```python\ndef is_even(n):\n    return n % 2 == 0\n```' (182 tok/s)
```
→ garbage は no-fp8-kv 構成ではない。sleep/wake 側。

## 5. level-1 sleep/wake (DE-0239) → 正常、weights CPU 退避+復元
```
(Worker) CuMemAllocator: sleep freed 25.44 GiB memory in total, of which 11.18 GiB is backed up in CPU
         and the rest 14.26 GiB is discarded directly.
(EngineCore) It took 0.498799 seconds to wake up tags {'weights', 'kv_cache'}.
baseline awake : '```python\ndef is_even(n):\n    return n % 2 == 0\n```'
after L1 wake  : '```python\ndef is_even(n):\n    return n % 2 == 0\n```'  (output_match=True)
```
→ level1 は weights(11.18GB) を CPU 退避 → wake で {weights,kv_cache} 復元。出力完全一致。**VERDICT=procedure error**。

## 6. level-1 A/B 実 Pass@1 (DE-0240)
```
Qwen awake -> Pass@1 0.667 (2/3) 167.6 tok/s
swap: qwen_sleepL1=0.48s coder_wake=0.63s vram=[28947,29277]
Coder awake -> Pass@1 1.0 (3/3) 74.2 tok/s
MEASURED: delta=0.333 -> KEEP_INCUMBENT (small 3-task sample, not firm)
```

## 7. production 復元検証 (各試験後)
```
out: '```python\ndef is_even(n):\n    return n % 2 == 0\n```' | tok/s: 35.8 | PRODUCTION HEALTHY: True
config: kv-cache-dtype fp8 / gpu-memory-utilization 0.92
```
