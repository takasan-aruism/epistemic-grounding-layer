#!/usr/bin/env bash
# Qwen3.6-35B-A3B-NVFP4 を vLLM で serve(RTX5090/sm_120 対応版)。
#
# ⚠️ 重要: checkpoint は必ず RedHatAI 版を使うこと。
#   nvidia/Qwen3.6-35B-A3B-NVFP4(modelopt)は GDN 線形注意まで量子化しており、
#   sm_120 で silent garbage(!!!! 等)を吐く(vLLM issue #40252)。
#   RedHatAI 版(compressed-tensors)は linear_attn を bf16 で ignore しており正常動作。
#
# 動作レシピ出典: patrickgawron.com RTX5090 Qwen3.6-35B NVFP4 ガイド
# OpenAI 互換: http://127.0.0.1:8005/v1
set -euo pipefail

MODEL_DIR=/storage/models/Qwen3.6-35B-A3B-NVFP4-RedHatAI
IMAGE=vllm/vllm-openai:nightly
NAME=qwen36_vllm
PORT=8005

docker rm -f "${NAME}" 2>/dev/null || true

docker run -d --name "${NAME}" \
  --gpus all \
  --ipc=host \
  -v "${MODEL_DIR}:/model:ro" \
  -p ${PORT}:8000 \
  "${IMAGE}" \
  --model /model \
  --served-model-name Qwen3.6-35B-A3B \
  --tensor-parallel-size 2 \
  --enable-expert-parallel \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 32 \
  --max-model-len 32768 \
  --enable-prefix-caching \
  --reasoning-parser qwen3 \
  --gpu-memory-utilization 0.92

echo "started ISOLATION(no-fp8-kv,no-sleep) ${NAME} on port ${PORT}. logs: docker logs -f ${NAME}"
