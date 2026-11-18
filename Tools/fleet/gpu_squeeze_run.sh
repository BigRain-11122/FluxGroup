#!/bin/bash
# 压测跑批：先让开两个会抢内存/CPU 的常驻活（采集与日计划），跑完无条件恢复。
# 为什么要写成一整个脚本：2026-11-18 实锚——`nohup ... &` 起的压测进程会随 shell
# 退出被杀（"后台进程守护"这条坑又踩了一次），所以整段逻辑必须由一个身体承担，
# 且恢复动作放在 trap 里，压测中途炸掉也能把常驻拉回来。
set -uo pipefail

ROOT="/Users/junsheng.sun/FluxGroup"
UID_N="$(id -u)"
LOG="$ROOT/.codely-cli/state/gpu-squeeze.log"
PAUSED=()

pause_job() {
  if launchctl print "gui/$UID_N/$1" >/dev/null 2>&1; then
    launchctl bootout "gui/$UID_N/$1" >/dev/null 2>&1 && PAUSED+=("$1")
  fi
}

restore_jobs() {
  for j in "${PAUSED[@]:-}"; do
    [[ -n "$j" ]] || continue
    launchctl bootstrap "gui/$UID_N" "$HOME/Library/LaunchAgents/$j.plist" >/dev/null 2>&1
  done
  echo "[squeeze] 已恢复：${PAUSED[*]:-无}"
}

trap restore_jobs EXIT

pause_job com.fluxgroup.sociallearn
pause_job com.fluxgroup.socialagentday
echo "[squeeze] 让开：${PAUSED[*]:-无}｜开始 $(date '+%H:%M:%S')"

PY="/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"
[[ -x "$PY" ]] || PY="$(command -v python3)"
echo "[squeeze] 解释器 $PY"
"$PY" -u "$ROOT/Tools/fleet/gpu_squeeze.py" "$@"
rc=$?
echo "[squeeze] 结束 rc=$rc $(date '+%H:%M:%S')"
exit $rc
