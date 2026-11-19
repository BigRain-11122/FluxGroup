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
  # 8788 现在训练期间不再停：还活着就别重启（重启会打断正在出稿的养号请求）
  if launchctl print "gui/$UID_N/com.fluxgroup.mlxlora" >/dev/null 2>&1; then
    echo "[train] 8788 全程在跑，不重启 $(date '+%H:%M:%S')"
  else
    echo "[train] 恢复 8788 LoRA 服务 $(date '+%H:%M:%S')"
    launchctl bootstrap "gui/$UID_N" "$HOME/Library/LaunchAgents/com.fluxgroup.mlxlora.plist" 2>/dev/null
    sleep 25
  fi
  "$PY" "$ROOT/Tools/fleet/vram_ceiling.py" --apply default 2>&1 | tail -3
  # 白名单回到训练前的样子（默认 2B+4B），否则日常两条车道会被清扫器误伤
  if [[ -f "$LANE_OK.trainbak" ]]; then
    mv "$LANE_OK.trainbak" "$LANE_OK"
  fi
  echo "[train] 结束 $(date '+%H:%M:%S')"
}
trap 'rm -f "$SENT"; restore' EXIT

SENT="/Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-EXCLUSIVE"
LANE_OK="/Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-LANE-OK"
# 共用档的白名单必须只剩 4B：清扫器按这个文件"护住"模型，若 2B 还在名单里，
# 采集/日间智能体把它抢回来 3.1GB，浏览器就没地方站（2026-11-19 实锚）。
cp "$LANE_OK" "$LANE_OK.trainbak" 2>/dev/null || true
echo "qwen3.5:4b-mlx" > "$LANE_OK"
echo "$(date '+%Y-%m-%dT%H:%M:%S') $$" > "$SENT"
# 哨兵：训练期间别的组件不许再往 ollama 装模型。2026-11-18 实锚——训练跑到一半，
# 机队别处把 9B(9GB)+4B(5GB) 装了回来，训练进程 rss 从 3.9GB 被换出到 0.43GB，
# 9 分钟没落一个 checkpoint。事后清理不够，必须在调用方就先挡住。
# 别的常驻会随时往 ollama 装 9B/4B，把训练挤到换页（实锚：26 分钟没落一个 checkpoint）。
# 训练窗口内让路：停掉会拉模型的常驻，训完由 restore 拉回。
# 2026-11-19 CEO「采集和训练的同时，养号实战」→ 不再一刀切让路。
# 实测（Tools/fleet/tri_lane_probe.py，40 iter）：训练 + 8788 出稿 + 采集浏览器同时跑，
# swap 零增长、pageouts 6-88/分（阈值 120）、训练 3.0-3.5s/步、出稿 10/10 成功。
# 所以：留 8788、留采集（sociallearn/socialagentday）；只停会拉 9B 的 modelqueue，
# 档位改用 train-shared（只留 4B@8k，9B/8B 禁入——9B 一进来就 9GB，训练会被换出）。
PAUSED_JOBS=()
for j in com.fluxgroup.modelqueue; do
  if launchctl print "gui/$UID_N/$j" >/dev/null 2>&1; then
    launchctl bootout "gui/$UID_N/$j" >/dev/null 2>&1 && PAUSED_JOBS+=("$j")
  fi
done
echo "[train] 让路（仅拉大模型的队列）：${PAUSED_JOBS[*]:-无}"
echo "[train] 切 train-shared 档（保留 4B 与 8788，禁 9B/8B） $(date '+%H:%M:%S')"
"$PY" "$ROOT/Tools/fleet/vram_ceiling.py" --apply train-shared 2>&1 | tail -2
sleep 3

SW0=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
echo "[train] 起训 swap=${SW0}MB iters=$*"
"$PY" -u "$ROOT/Tools/fleet/train_lora.py" "$@"
rc=$?
SW1=$(sysctl -n vm.swapusage | sed -n 's/.*used = \([0-9.]*\)M.*/\1/p')
echo "[train] 训练结束 rc=$rc swap ${SW0}MB→${SW1}MB"
exit $rc
