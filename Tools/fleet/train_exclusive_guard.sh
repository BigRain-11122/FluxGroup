#!/bin/bash
# 训练独占清扫器：哨兵在 → 每 30 秒把 ollama 里任何已装载模型卸掉。
# 为什么不能只靠 llm_client 的哨兵判定：机队里还有直接打 /api/generate 的调用方
# （console/modelqueue/learning 各有一份），只挡一条路，路还在。
set -uo pipefail
# launchd 的 PATH 只有 /usr/bin:/bin:/usr/sbin:/sbin，`ollama` 在 .homebrew/bin 下，
# 不写绝对路径就会出现"脚本在跑但一个模型都没卸"的假动作（2026-11-18 实锚：
# 三模型驻留 17GB、日志空白、job 状态 running）。同族坑：pyenv 解释器。
OLLAMA="/Users/junsheng.sun/.homebrew/bin/ollama"
[[ -x "$OLLAMA" ]] || OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
SENT="/Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-EXCLUSIVE"
# 训练期间允许常驻的一条小车道（默认 2B）：实测占 3.2GB、出稿 34 tok/s，
# 只让训练慢 8%；9B(9GB)/4B(5GB) 一律卸，它们一装训练就掉页。
LANE_OK="/Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-LANE-OK"
# 允许多条车道（一行一个模型）：实测 2B 只让训练慢 8%，两三条小车道仍有余量；
# 但 9B 这种大户必禁（9GB，一装训练就掉页）。
ALLOW="$(cat "$LANE_OK" 2>/dev/null || echo qwen3.5:2b)"
LOG="/Users/junsheng.sun/FluxGroup/.codely-cli/state/train-exclusive.log"
while [[ -f "$SENT" ]]; do
  while read -r name; do
    [[ -z "$name" || "$name" == "NAME" ]] && continue
    if grep -qx "$name" <<< "$ALLOW"; then continue; fi
    "$OLLAMA" stop "$name" >/dev/null 2>&1 && echo "$(date '+%H:%M:%S') 卸下 $name" >> "$LOG"
  done < <("$OLLAMA" ps 2>/dev/null | awk 'NR>1{print $1}')
  sleep 30
done
echo "$(date '+%H:%M:%S') 哨兵消失，清扫器退出" >> "$LOG"
