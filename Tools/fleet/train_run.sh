#!/bin/bash
# 训练批：先腾内存（卸 ollama 模型 + 停 8788 LoRA 服务），训完无条件恢复。
# 为什么要这样：训练要 ~10GB，8788 的 LoRA 服务常驻 2.9GB 却不参与训练，
# 留着就是把 swap 往死里推（2026-11-17 实锚：跑到 590 步 swap +1.3GB、空闲只剩 393MB）。
set -uo pipefail

ROOT="/Users/junsheng.sun/FluxGroup"
UID_N="$(id -u)"
LOG="$ROOT/.codely-cli/state/train-run.log"
PY="/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"

restore() {
  for j in ${PAUSED_JOBS[*]:-}; do
    launchctl bootstrap "gui/$UID_N" "$HOME/Library/LaunchAgents/$j.plist" >/dev/null 2>&1
  done
  echo "[train] 恢复 8788 LoRA 服务 $(date '+%H:%M:%S')"
  launchctl bootstrap "gui/$UID_N" "$HOME/Library/LaunchAgents/com.fluxgroup.mlxlora.plist" 2>/dev/null
  sleep 25
  "$PY" "$ROOT/Tools/fleet/vram_ceiling.py" --apply default 2>&1 | tail -3
  echo "[train] 结束 $(date '+%H:%M:%S')"
}
trap 'rm -f "$SENT"; restore' EXIT

SENT="/Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-EXCLUSIVE"
echo "$(date '+%Y-%m-%dT%H:%M:%S') $$" > "$SENT"
# 哨兵：训练期间别的组件不许再往 ollama 装模型。2026-11-18 实锚——训练跑到一半，
# 机队别处把 9B(9GB)+4B(5GB) 装了回来，训练进程 rss 从 3.9GB 被换出到 0.43GB，
# 9 分钟没落一个 checkpoint。事后清理不够，必须在调用方就先挡住。
# 别的常驻会随时往 ollama 装 9B/4B，把训练挤到换页（实锚：26 分钟没落一个 checkpoint）。
# 训练窗口内让路：停掉会拉模型的常驻，训完由 restore 拉回。
PAUSED_JOBS=()
for j in com.fluxgroup.sociallearn com.fluxgroup.socialagentday com.fluxgroup.modelqueue; do
  if launchctl print "gui/$UID_N/$j" >/dev/null 2>&1; then
    launchctl bootout "gui/$UID_N/$j" >/dev/null 2>&1 && PAUSED_JOBS+=("$j")
  fi
done
echo "[train] 让路：${PAUSED_JOBS[*]:-无}"
echo "[train] 腾内存：停 8788 + 切 train 档 $(date '+%H:%M:%S')"
launchctl bootout "gui/$UID_N/com.fluxgroup.mlxlora" 2>/dev/null
"$PY" "$ROOT/Tools/fleet/vram_ceiling.py" --apply train 2>&1 | tail -2
sleep 5

SW0=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
echo "[train] 起训 swap=${SW0}MB iters=$*"
"$PY" -u "$ROOT/Tools/fleet/train_lora.py" "$@"
rc=$?
SW1=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
echo "[train] 训练结束 rc=$rc swap ${SW0}MB→${SW1}MB"
exit $rc
