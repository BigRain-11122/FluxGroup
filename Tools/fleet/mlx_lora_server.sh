#!/bin/bash
# 养号 LoRA 独立服务：与 ollama 并存，占 8788。
# 由 launchd (com.fluxgroup.mlxlora) 守护——不要手动 nohup/setsid，
# macOS 没有 setsid，且 shell 退出会连带杀掉后台进程（本轮踩过）。
set -euo pipefail

ROOT="/Users/junsheng.sun/FluxGroup"
PY="/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"
BASE="${MLX_BASE_MODEL:-/Users/junsheng.sun/.fluxgroup/models/qwen3.5-4b-4bit}"
PORT="${MLX_LORA_PORT:-8788}"
RUNS="$ROOT/cph4/fleet/social/train/RUNS"

# mlx_lm.server 处理 GET /v1/models 时会调 scan_cache_dir()，缓存目录不存在就抛
# CacheNotFound 把请求打死；launchd 不继承登录 shell 的 HF_HOME，所以要显式钉住并建目录。
export HF_HOME="${HF_HOME:-/Users/junsheng.sun/models/hf}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_HOME/hub}"
mkdir -p "$HF_HUB_CACHE"

# 适配器：显式指定 > ACTIVE 指针 > 最新一轮的 best > 最新一轮的 adapter
# ACTIVE 指针（train/ACTIVE.json）是"人工选点"的落点：只按"最新一轮"抓，
# 会把刚跑完的对照实验当成上线件（A/B 两轮都会有 best 目录）。
resolve_adapter() {
  if [[ -n "${MLX_ADAPTER:-}" ]]; then echo "$MLX_ADAPTER"; return; fi
  local act="$ROOT/cph4/fleet/social/train/ACTIVE.json"
  if [[ -f "$act" ]]; then
    local a
    a="$(sed -n 's/.*"adapter"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$act" | head -1)"
    if [[ -n "$a" && -f "$ROOT/$a/adapters.safetensors" ]]; then echo "$ROOT/$a"; return; fi
  fi
  local d
  for d in $(ls -1dt "$RUNS"/*/ 2>/dev/null); do
    if [[ -f "${d}best/adapters.safetensors" ]]; then echo "${d}best"; return; fi
    if [[ -f "${d}adapter/adapters.safetensors" ]]; then echo "${d}adapter"; return; fi
  done
  return 1
}

ADAPTER="$(resolve_adapter)" || { echo "[mlxlora] 找不到可用适配器，退出" >&2; exit 78; }

echo "[mlxlora] base=$BASE"
echo "[mlxlora] adapter=$ADAPTER"
echo "[mlxlora] port=$PORT"

exec "$PY" -m mlx_lm server \
  --model "$BASE" \
  --adapter-path "$ADAPTER" \
  --host 127.0.0.1 \
  --port "$PORT" \
  --chat-template-args '{"enable_thinking": false}' \
  --log-level INFO
