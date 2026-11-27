#!/bin/bash
# 训练结束后把让路的常驻拉回来。为什么要单独一支：训练批是旧脚本起的（trap 里没有这段），
# 靠人记一定漏；这些常驻停了就是机器在空转（学习/日计划/模型队列全停）。
set -uo pipefail
U="$(id -u)"
JOBS="com.fluxgroup.sociallearn com.fluxgroup.socialagentday com.fluxgroup.modelqueue"
for i in $(seq 1 240); do
  if ! pgrep -f "mlx_lm lora" >/dev/null 2>&1; then
    sleep 5
    rm -f /Users/junsheng.sun/FluxGroup/.codely-cli/state/TRAIN-EXCLUSIVE
    for j in $JOBS; do
      launchctl bootstrap "gui/$U" "$HOME/Library/LaunchAgents/$j.plist" 2>/dev/null \
        && echo "$(date '+%H:%M:%S') 恢复 $j"
    done
    echo "$(date '+%H:%M:%S') 训练已结束，让路的常驻全部恢复"
    exit 0
  fi
  sleep 30
done
echo "$(date '+%H:%M:%S') 等了 2 小时训练还在跑，放弃恢复（人工检查）"
