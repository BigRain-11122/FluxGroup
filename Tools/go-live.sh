#!/bin/bash
# go-live.sh — 把机队从"暂停"切到"常驻最小集"，默认只演练。
#
# 为什么要有它：2026-11-11 CEO 令「全部暂停，等我梳理工作流」。梳理完要恢复时，
# 手工敲 40 多个 launchctl 既慢又容易漏；本脚本把"最小可用集"固化下来：
#   envprobe  每天采一次本机 AI 环境 → cph4/fleet/env/<station>.json（静默，无窗口）
#   pulse     主控脉：巡查/派单/验收的节拍器（恢复它才会真正开始跑）
#
# 用法：
#   bash Tools/go-live.sh                 # 演练：只打印计划与前置检查（不加载任何服务）
#   bash Tools/go-live.sh --apply         # 真正恢复 envprobe + pulse
#   bash Tools/go-live.sh --apply pulse   # 只恢复指定项
#   bash Tools/go-live.sh --status        # 看现在有哪些 fluxgroup 服务在跑
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LA="$HOME/Library/LaunchAgents"
U=$(id -u)
PY="$(command -v python3 || true)"
MODE="dry"; WANT=""; FORCE=0
case "${1:-}" in
  --apply) MODE="apply"; shift; WANT="$*" ;;
  --force) FORCE=1; shift ;;
  --status) MODE="status" ;;
  "") ;;
  *) echo "用法：$0 [--apply [envprobe drive] [--force] | --status]"; exit 2 ;;
esac

say() { printf '%s\n' "$*"; }

if [ "$MODE" = "status" ]; then
  n=$(launchctl list 2>/dev/null | grep -c fluxgroup || true)
  say "fluxgroup 常驻服务：${n} 项"
  launchctl list 2>/dev/null | grep fluxgroup | awk '{print "  "$3"  pid="$1"  rc="$2}'
  [ -f "$ROOT/cph4/fleet/state/quality-score.json" ] && \
    say "最近评分：$(python3 -c 'import json;print(json.load(open("'"$ROOT"'/cph4/fleet/state/quality-score.json"))["total"])' 2>/dev/null || echo '?')/100"
  exit 0
fi

say "== 前置检查 =="
ok=1
[ -n "$PY" ] && say "ok   python3: $PY" || { say "FAIL 找不到 python3"; ok=0; }
[ -d "$ROOT/cph4/fleet" ] && say "ok   仓库: $ROOT" || { say "FAIL 仓库路径不对"; ok=0; }
[ -f "$ROOT/Tools/fleet/station_drive.py" ] && say "ok   自驱入口在" || { say "FAIL 缺 station_drive.py"; ok=0; }
if curl -s -m 2 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  say "ok   本机模型服务在听（11434）"
else
  say "warn 本机模型服务没起：自驱会走纯规则，模型类工序排队"
fi
curl -s -m 2 http://127.0.0.1:8792/api/version >/dev/null 2>&1 \
  && say "ok   网关在听（8792）" || say "warn 网关没起（各机借模型会失败，属预期）"
# 2026-11-12（批次6）：工位状态必须过闸。原实现不看 STATIONS.json，在一台被判
# blocked/offline 的机器上 --apply 会把该机变成第二个主控、开始造卡派单。
if [ "$FORCE" = "1" ]; then
  PF_ARGS="--force"
else
  PF_ARGS=""
fi
if "$PY" "$ROOT/Tools/fleet/go_live_preflight.py" $PF_ARGS >/dev/null 2>&1; then
  say "ok   工位自检通过（$( "$PY" "$ROOT/Tools/fleet/go_live_preflight.py" --json 2>/dev/null | "$PY" -c "import json,sys;d=json.load(sys.stdin);print(d['station']+'/'+d['status'])" 2>/dev/null)）"
else
  say "FAIL 工位自检不过："
  "$PY" "$ROOT/Tools/fleet/go_live_preflight.py" $PF_ARGS 2>&1 | sed "s/^/     /" | tail -8
  ok=0
fi
[ "$ok" = "1" ] || { say "前置不过，别恢复"; exit 2; }

PLIST_ENV="$LA/com.fluxgroup.envprobe.plist"
say ""
say "== 计划 =="
say "1) envprobe：每日 08:20 静默采本机 AI 环境 → cph4/fleet/env/<station>.json"
say "2) drive   ：v3 自驱（station_drive，按 AUTOMATION-v1 排班）"
say "   pulse  ：v2 遗留主控（往已归档的 PRODUCTION-QUEUE 造卡），默认不恢复"
say "   其余 40+ 项仍留在 $LA/disabled/20261111-pause/，需要时 bash Tools/restore-startup.sh <名字>"

if [ "$MODE" = "dry" ]; then
  say ""
  say "（演练模式，没有加载任何服务。要真恢复：bash Tools/go-live.sh --apply）"
  exit 0
fi

want_env=1; want_drive=1; want_pulse=0
if [ -n "$WANT" ]; then
  want_env=0; want_drive=0
  case " $WANT " in *" envprobe "*) want_env=1 ;; esac
  case " $WANT " in *" drive "*) want_drive=1 ;; esac
  case " $WANT " in *" pulse "*) want_pulse=1; say "warn pulse 是 v2 遗留，确认后才会恢复" ;; esac
fi

if [ "$want_env" = "1" ]; then
  mkdir -p "$LA"
  cat > "$PLIST_ENV" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.envprobe</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$ROOT/Tools/fleet/env_probe.py</string><string>--write</string></array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>20</integer></dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>/tmp/fluxgroup-envprobe.log</string>
  <key>StandardErrorPath</key><string>/tmp/fluxgroup-envprobe.err</string>
  <key>ProcessType</key><string>Background</string>
</dict></plist>
PLIST
  launchctl bootout "gui/$U/com.fluxgroup.envprobe" 2>/dev/null || true
  if launchctl bootstrap "gui/$U" "$PLIST_ENV" 2>/dev/null; then
    say "ok   envprobe 已加载（每日 08:20，静默）"
    "$PY" "$ROOT/Tools/fleet/env_probe.py" --write >/dev/null 2>&1 \
      && say "     已先采一次：cph4/fleet/env/<station>.json"
  else
    say "FAIL envprobe 加载失败（看 $PLIST_ENV）"
  fi
fi

if [ "$want_drive" = "1" ]; then
  say "   >>> 注册 v3 自驱：station_drive --once（每 300 秒，按排班表跑）"
  "$PY" "$ROOT/Tools/fleet/install_drive_agent.py" --load 2>&1 | sed "s/^/     /"
fi

if [ "$want_pulse" = "1" ]; then
  if [ -x "$ROOT/Tools/restore-startup.sh" ] || [ -f "$ROOT/Tools/restore-startup.sh" ]; then
    bash "$ROOT/Tools/restore-startup.sh" pulse 2>&1 | tail -5
  else
    say "FAIL 找不到 Tools/restore-startup.sh"
  fi
fi

say ""
say "== 恢复后自检 =="
launchctl list 2>/dev/null | grep fluxgroup | awk '{print "  "$3" pid="$1}'
say "再看一眼：bash Tools/go-live.sh --status"
exit 0
