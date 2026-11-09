#!/bin/bash
# agent_lane.sh - 起/停本机「长上下文单请求」Ollama 专用车道（默认 127.0.0.1:11436）。
# 为什么单独一条：32k 上下文在机队档（NUM_PARALLEL=3）下要 13.1GB 且会被调度器驱逐；
# 单槽只需 7.7GB，能和机队的 4B 共存。实测见 docs/local-llm-agent-lane.md。
# 用法：Tools/fleet/agent_lane.sh [start|stop|status]
set -euo pipefail
PORT="${AGENT_LANE_PORT:-11436}"
OLLAMA_BIN="$(command -v ollama || echo /Users/junsheng.sun/bin/ollama)"
case "${1:-start}" in
  start)
    exec env OLLAMA_HOST="127.0.0.1:$PORT" \
      OLLAMA_NUM_PARALLEL=1 \
      OLLAMA_CONTEXT_LENGTH=32768 \
      OLLAMA_MAX_LOADED_MODELS=1 \
      OLLAMA_KEEP_ALIVE=15m \
      OLLAMA_FLASH_ATTENTION=1 \
      OLLAMA_KV_CACHE_TYPE=q8_0 \
      "$OLLAMA_BIN" serve
    ;;
  stop)
    pkill -f "OLLAMA_HOST=127.0.0.1:$PORT" 2>/dev/null || true
    echo "agent lane stop requested (port $PORT)"
    ;;
  status)
    curl -s -m 3 "http://127.0.0.1:$PORT/api/version" || echo "not running on $PORT"
    ;;
  *) echo "usage: $0 [start|stop|status]"; exit 2 ;;
esac
