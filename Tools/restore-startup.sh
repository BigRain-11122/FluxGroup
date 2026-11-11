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

# 2026-11-11 CEO 令：Mac 不用移动硬盘 + 只做主控/轻活/本地模型。
# 下列服务不再恢复（留档仍在 disabled 目录，需要时可手工 bootstrap）：
#   intake       —— 收件口会往外置盘落字节，已退役（产物留产出机）
#   assetshare   —— 读 /Volumes 的素材盘入口，无外置盘即空转
RETIRED="com.fluxgroup.intake com.fluxgroup.assetshare"

match_all=1
[ "$#" -gt 0 ] && match_all=0

restored=0
for f in "$PAUSED"/*.plist; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  label="${base%.plist}"
  case " $RETIRED " in *" $label "*) echo "跳过（已退役） $base"; continue;; esac
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

echo "共恢复 $restored 项。"

# 登录项：从留档 JSON 读回 name/path 逐个重新加入
INV="$HOME/FluxGroup/cph4/fleet/STARTUP-INVENTORY-20261111.json"
if [ -f "$INV" ] && [ "$match_all" -eq 1 ]; then
  echo "--- 恢复登录项 ---"
  python3 - "$INV" <<'PY' > /tmp/_li_restore.sh
import json,sys,shlex
d=json.load(open(sys.argv[1],encoding="utf-8"))
for it in d.get("login_items_detail") or []:
    p=it.get("path","")
    if not p: continue
    print("osascript -e 'tell application \"System Events\" to make login item at end "
          "with properties {path:\"%s\", hidden:false}' >/dev/null 2>&1 && echo \"登录项 %s\"" % (p, it.get("name","?")))
PY
  bash /tmp/_li_restore.sh
fi
