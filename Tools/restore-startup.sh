#!/bin/bash
# 恢复 2026-11-11 暂停的全部用户级自启项。
# 令源：CEO 2026-11-11「都记录在案然后全部暂停，等我梳理工作流」
# 留档：cph4/fleet/STARTUP-INVENTORY-20261111.{json,md}
# 用法：bash Tools/restore-startup.sh            # 恢复全部
#       bash Tools/restore-startup.sh pulse console   # 只恢复名字含这些词的
set -u
LA="$HOME/Library/LaunchAgents"
PAUSED="$LA/disabled/20261111-pause"
U=$(id -u)

if [ ! -d "$PAUSED" ]; then
  echo "找不到暂停目录：$PAUSED" >&2
  exit 1
fi

match_all=1
[ "$#" -gt 0 ] && match_all=0

restored=0
for f in "$PAUSED"/*.plist; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  if [ "$match_all" -eq 0 ]; then
    keep=0
    for pat in "$@"; do case "$base" in *"$pat"*) keep=1;; esac; done
    [ "$keep" -eq 1 ] || continue
  fi
  cp -p "$f" "$LA/$base" || { echo "复制失败 $base" >&2; continue; }
  launchctl bootstrap "gui/$U" "$LA/$base" 2>/dev/null || launchctl load "$LA/$base" 2>/dev/null
  echo "恢复 $base"
  restored=$((restored+1))
done

echo "共恢复 $restored 项。登录项需手动或用下方命令重新加入："
echo '  osascript -e '"'"'tell application "System Events" to make login item at end with properties {path:"/Applications/<App>.app", hidden:false}'"'"''
