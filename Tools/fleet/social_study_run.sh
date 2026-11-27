#!/bin/bash
# 学习批：浏览器 profile 只有一份，采集循环占着它，所以要么让路要么等。
# 这里让路：停 sociallearn → 清残留锁 → 学 → 恢复（与压测/实战同一套让路模式）。
set -uo pipefail
ROOT="/Users/junsheng.sun/FluxGroup"; U="$(id -u)"
restore() {
  launchctl bootstrap "gui/$U" "$HOME/Library/LaunchAgents/com.fluxgroup.sociallearn.plist" 2>/dev/null
  echo "[study] 已恢复采集循环 $(date '+%H:%M:%S')"
}
trap restore EXIT
launchctl bootout "gui/$U/com.fluxgroup.sociallearn" 2>/dev/null
pkill -f "browser-bilibili" 2>/dev/null
sleep 5
rm -f "$HOME/.fluxgroup/browser-bilibili/SingletonLock" 2>/dev/null
cd "$ROOT" && .venv-housing/bin/python -u Tools/fleet/social_study.py "$@"
