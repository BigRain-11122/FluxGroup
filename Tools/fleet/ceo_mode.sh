#!/bin/bash
# ceo_mode.sh - 把主控脉让出来给游戏（可逆）
#
# 为什么需要（2026-11-03 CEO「我可能会用 macbook 去玩一些游戏」）：
#   这台 32GB 统一内存同时要养 4B 模型 + 脉冲 + 执行腿。开游戏时不先让路，
#   GPU/内存被机队占着，游戏会掉帧、机队也会掉卡，两头都不讨好。
#   让路=停常驻循环，不是改配置；回来一条命令恢复，配置一个字都不动。
#
# 用法：
#   sudo 不需要。./ceo_mode.sh start [--with-ai]   停脉+看门狗（--with-ai 连 ollama 一起停）
#   ./ceo_mode.sh stop                             先过 deploy_gate 再恢复
#   ./ceo_mode.sh status                           看现在谁在跑
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PULSE=com.fluxgroup.pulse
WATCHDOG=com.fluxgroup.watchdog
OLLAMA=com.fluxgroup.ollama
STATE="$ROOT/cph4/fleet/state/ceo-mode.json"

say() { printf '%s\n' "$*"; }

do_status() {
  say "--- 常驻进程 ---"
  for j in "$PULSE" "$WATCHDOG" "$OLLAMA"; do
    if launchctl print "gui/$(id -u)/$j" >/dev/null 2>&1; then say "  $j  RUNNING"; else say "  $j  stopped"; fi
  done
  say "--- 执行腿 ---"
  pgrep -fl "lane_agent|autowork|master_pulse" | sed 's/^/  /' || say "  (none)"
  if [ -f "$STATE" ]; then say "--- 状态 ---"; cat "$STATE"; fi
}

do_start() {
  local with_ai="no"
  [ "${1:-}" = "--with-ai" ] && with_ai="yes"
  say "让路给游戏：停 ${WATCHDOG}（先停，否则它会把脉冲拉回来）"
  launchctl bootout "gui/$(id -u)/$WATCHDOG" 2>/dev/null
  say "停 ${PULSE}"
  launchctl bootout "gui/$(id -u)/$PULSE" 2>/dev/null
  # 收掉在跑的执行腿（脉冲停了它们还会把当前这张卡跑完，跑完就没人接了）
  pkill -f "Tools/fleet/lane_agent.py" 2>/dev/null
  pkill -f "Tools/fleet/autowork.py" 2>/dev/null
  if [ "$with_ai" = "yes" ]; then
    say "停 ${OLLAMA}（释放约 3-4GB 统一内存）"
    launchctl bootout "gui/$(id -u)/$OLLAMA" 2>/dev/null
  fi
  mkdir -p "$(dirname "$STATE")"
  printf '{"mode":"gaming","since":"%s","ai_stopped":"%s"}\n' \
    "$(date +%Y-%m-%dT%H:%M:%S)" "$with_ai" > "$STATE"
  say ""
  say "机队已让路。恢复：$0 stop"
}

do_stop() {
  say "先过部署闸（闸不过不许重启，2026-11-02 定法）"
  if ! /usr/bin/python3 "$ROOT/Tools/fleet/deploy_gate.py" >/tmp/ceo-mode-gate.log 2>&1; then
    say "deploy_gate 未通过，未恢复。看 /tmp/ceo-mode-gate.log"
    tail -5 /tmp/ceo-mode-gate.log
    return 1
  fi
  say "闸通过。起 ${OLLAMA}"
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$OLLAMA.plist" 2>/dev/null
  say "起 ${PULSE}"
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$PULSE.plist" 2>/dev/null
  say "起 ${WATCHDOG}"
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$WATCHDOG.plist" 2>/dev/null
  rm -f "$STATE"
  sleep 3
  do_status
}

case "${1:-status}" in
  start) do_start "${2:-}" ;;
  stop)  do_stop ;;
  status) do_status ;;
  *) say "用法: $0 {start [--with-ai]|stop|status}"; exit 2 ;;
esac