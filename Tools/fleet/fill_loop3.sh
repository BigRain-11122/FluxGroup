#!/bin/bash
# fill_loop.sh - 让本地 4B 持续有活，GPU 不做空转；州长仍在盯 swap。
cd "$(dirname "$0")/../.." || exit 1
PY="/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"
while true; do
  "$PY" Tools/fleet/local_worker.py --mode labels --limit 40 >/dev/null 2>&1
  sleep 1
done
