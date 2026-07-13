#!/usr/bin/env bash
# ITEM-2DER-EVO-0015 A/B sleep-wake experiment: Qwen3.6-27B-FP8 (dense coder), no-fp8-KV + sleep-mode + dev-mode,
# gpu-util 0.45, max-model-len 32768. Derived from serve_qwen36_27b_vllm.sh: removed --kv-cache-dtype fp8 (breaks
# sleep/wake, DE-0168), added --enable-sleep-mode + VLLM_SERVER_DEV_MODE=1, lowered util for co-existence. TP=2 kept.
set -euo pipefail
MODEL_DIR=/storage/models/Qwen3.6-27B-FP8
IMAGE=vllm/vllm-openai:nightly
NAME=qwen36_27b_vllm
PORT=8006
docker rm -f "${NAME}" 2>/dev/null || true
docker run -d --name "${NAME}" \
  --gpus all --ipc=host \
  -e VLLM_SERVER_DEV_MODE=1 \
  -v "${MODEL_DIR}:/model:ro" \
  -p ${PORT}:8000 \
  "${IMAGE}" \
  --model /model \
  --served-model-name Qwen3.6-27B \
  --tensor-parallel-size 2 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 4 \
  --max-model-len 32768 \
  --enable-prefix-caching \
  --reasoning-parser qwen3 \
  --enable-sleep-mode \
  --gpu-memory-utilization 0.85
echo "started ${NAME} (AB sleep-mode, no-fp8-KV, util 0.45) on port ${PORT}"
