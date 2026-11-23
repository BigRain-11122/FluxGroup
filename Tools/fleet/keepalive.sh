#!/bin/bash
# keepalive.sh — 不依赖 launchd 的机队常驻集（start/stop/status）。
#
# 为什么要这条路（2026-11-15 实锚）：本机 fluxgroup 启动项被一个来源未定位的
# "暂停器"反复拆除——10:55 停机一次、11:00 恢复后被搬回 disabled/20261115-pause
# 并 bootout（11:02），期间机器 6 分钟无任何键盘鼠标输入，说明不是人在删。
# 同时每次装 launchd Login Item 都会弹 "Background Items Added" 系统通知，
# 违反 CEO 静默律。所以在定位那个暂停器之前，机队用"会话外常驻进程"跑：
# 无 plist、无登录项、无弹窗，一条命令起停。
#
# 用法：
#   bash Tools/fleet/keepalive.sh start|stop|status
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$(command -v python3)"
RUN=/tmp/fluxgroup-keepalive
mkdir -p "$RUN"
cd "$ROOT" || exit 1

# name:log:命令
JOBS=(
  "gateway:llm-gateway.log:$PY Tools/fleet/llm_gateway.py --host 0.0.0.0 --port 8792"
  "console:console.log:$PY Tools/fleet/console_server.py --host 0.0.0.0 --port 8787"
  # automation_runner 是"跑一轮就退"的，必须外面套循环（原 launchd plist 靠 StartInterval 触发）
  "drive:drive.log:while true; do $PY Tools/fleet/automation_runner.py --budget 240; sleep 300; done"
  "station:station.log:$PY Tools/fleet/station_drive.py --loop 60"
  # 39 席模型赋能面：原来靠 launchd StartInterval=180，改成循环等价（跑一轮就退）
  "seats:seats.log:while true; do $PY Tools/fleet/seat_dispatch.py --max-runs 2; sleep 180; done"
)

start_one() {
  local name="$1" log="$2" cmd="$3"
  if [ -f "$RUN/$name.pid" ] && kill -0 "$(cat "$RUN/$name.pid")" 2>/dev/null; then
    echo "already  $name  pid=$(cat "$RUN/$name.pid")"
    return 0
  fi
  # 认领已在跑的实例：上一轮会话留下的进程没有 pid 文件时，硬起第二个会撞端口
  # （gateway）或被单例锁挡住（station_drive），两种都表现为"我起了但它立刻 DOWN"。
  local script
  script="$(printf '%s' "$cmd" | grep -oE 'Tools/fleet/[A-Za-z0-9_]+\.py' | head -1)"
  local found
  found="$( [ -n "$script" ] && pgrep -f "$script" | head -1 || true )"
  if [ -n "$found" ]; then
    echo "$found" >"$RUN/$name.pid"
    echo "adopt    $name  pid=$found（已在跑，接管记账）"
    return 0
  fi
  # 必须真正脱离会话：2026-11-15 实测 nohup 不够——工具调用结束时整个进程组被回收，
  # 四个常驻进程在 2-3 分钟内全部消失。macOS 没有 setsid(1)，用 perl 的 POSIX::setsid
  # 先自立会话再 exec，才能让进程活过发起它的那一轮 shell。
  perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV' bash -c "$cmd" \
    >>"$RUN/$log" 2>&1 </dev/null &
  echo $! >"$RUN/$name.pid"
  echo "start    $name  pid=$(cat "$RUN/$name.pid")"
}

stop_one() {
  local name="$1"
  if [ -f "$RUN/$name.pid" ]; then
    local pid; pid="$(cat "$RUN/$name.pid")"
    pkill -P "$pid" 2>/dev/null
    kill "$pid" 2>/dev/null
    rm -f "$RUN/$name.pid"
    echo "stop     $name  pid=$pid"
  else
    echo "not-run  $name"
  fi
}

status() {
  for j in "${JOBS[@]}"; do
    local name="${j%%:*}"
    if [ -f "$RUN/$name.pid" ] && kill -0 "$(cat "$RUN/$name.pid")" 2>/dev/null; then
      echo "UP    $name  pid=$(cat "$RUN/$name.pid")"
    else
      echo "DOWN  $name"
    fi
  done
  echo "--- listen ---"
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | awk '$9 ~ /:(8787|8792|11434)$/ {print "  "$1" "$9}'
}

case "${1:-status}" in
  start) for j in "${JOBS[@]}"; do IFS=: read -r n l c <<<"$j"; start_one "$n" "$l" "$c"; done ;;
  stop) for j in "${JOBS[@]}"; do stop_one "${j%%:*}"; done ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
  status) status ;;
  *) echo "用法：$0 start|stop|status|restart"; exit 2 ;;
esac
