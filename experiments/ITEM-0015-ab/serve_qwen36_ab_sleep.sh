#!/usr/bin/env bash
# ITEM-2DER-EVO-0015 A/B sleep-wake experiment: Qwen3.6-35B-A3B, no-fp8-KV + sleep-mode + dev-mode, gpu-util 0.45
# (co-existence budget: 0.45 + 0.45 = 0.90 so both instances can init on 2x RTX 5090). Rollback = serve_qwen36_vllm.sh
set -euo pipefail
MODEL_DIR=/storage/models/Qwen3.6-35B-A3B-NVFP4-RedHatAI
IMAGE=vllm/vllm-openai:nightly
NAME=qwen36_vllm
PORT=8005
docker rm -f "${NAME}" 2>/dev/null || true
docker run -d --name "${NAME}" \
  --gpus all --ipc=host \
  -e VLLM_SERVER_DEV_MODE=1 \
  -v "${MODEL_DIR}:/model:ro" \
  -p ${PORT}:8000 \
  "${IMAGE}" \
  --model /model \
  --served-model-name Qwen3.6-35B-A3B \
  --tensor-parallel-size 2 \
  --enable-expert-parallel \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 4 \
  --max-model-len 32768 \
  --enable-prefix-caching \
  --reasoning-parser qwen3 \
  --enable-sleep-mode \
  --gpu-memory-utilization 0.85
echo "started ${NAME} (AB sleep-mode, no-fp8-KV, util 0.45) on port ${PORT}"
