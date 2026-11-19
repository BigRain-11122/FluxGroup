#!/bin/bash
# install-fanctl.sh —— 让本机按"更积极"的温度曲线自动调风扇
#
# 令源：CEO 2026-11-19「你把自动风扇策略调整的好点，让他散热积极点」
#
# 为什么装成 LaunchDaemon 而不是挂 App：
#   · SMC 读写需要 root，LaunchAgent（用户级）没这个权限；
#   · Macs Fan Control 启动会把配置覆盖成 Predefined:0（实测），
#     而且没有任何脚本接口，所以由我们自己的小守护进程接管更可靠。
#
# 用法：
#   sudo bash Tools/fleet/install-fanctl.sh            # 安装并启动
#   sudo bash Tools/fleet/install-fanctl.sh --status   # 看状态
#   sudo bash Tools/fleet/install-fanctl.sh --uninstall # 卸载（交回系统曲线）
set -u

PLIST=/Library/LaunchDaemons/com.fluxgroup.fanctl.plist
LABEL=com.fluxgroup.fanctl
LOG=/var/log/fluxgroup-fanctl.log
PY=/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3
TOOL=/Users/junsheng.sun/FluxGroup/Tools/fleet/fan_boost.py
# 曲线：45℃ 开始提速，78℃ 满转（系统默认介入更晚，这是"更积极"的核心）
LO=45
HI=78

if [ "$(id -u)" -ne 0 ]; then
  echo "需要 root：sudo bash $0 $*" >&2
  exit 2
fi

case "${1:-}" in
  --status)
    launchctl print "system/$LABEL" 2>/dev/null | grep -E "state = |pid = |runs = |last exit" || echo "未安装"
    echo "--- 最近日志 ---"; tail -8 "$LOG" 2>/dev/null || echo "(无日志)"
    echo "--- 当前转速 ---"; "$PY" "$TOOL" --show 2>&1 | tail -3
    exit 0;;
  --uninstall)
    launchctl bootout "system/$LABEL" 2>/dev/null
    rm -f "$PLIST" && echo "已卸载 $PLIST"
    "$PY" "$TOOL" --auto 2>&1 | tail -2
    echo "已交回系统自动曲线。"
    exit 0;;
esac

[ -x "$PY" ] || { echo "找不到解释器 $PY" >&2; exit 2; }
[ -f "$TOOL" ] || { echo "找不到 $TOOL" >&2; exit 2; }

# 先自检：能不能读到风扇（读不到就别装，免得装上一个永远失败的守护）
if ! "$PY" "$TOOL" --show 2>&1 | grep -q "fan0"; then
  echo "FAIL 读不到风扇，放弃安装。先手动跑：sudo $PY $TOOL --show" >&2
  exit 3
fi

launchctl bootout "system/$LABEL" 2>/dev/null

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$TOOL</string>
        <string>--curve</string>
        <string>--interval</string><string>20</string>
        <string>--lo</string><string>$LO</string>
        <string>--hi</string><string>$HI</string>
        <string>--verbose</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>$LOG</string>
    <key>StandardErrorPath</key><string>$LOG</string>
    <key>ProcessType</key><string>Background</string>
</dict>
</plist>
EOF

chown root:wheel "$PLIST"; chmod 644 "$PLIST"
launchctl bootstrap system "$PLIST" 2>&1 || launchctl load -w "$PLIST" 2>&1
sleep 3
echo "--- 安装结果 ---"
launchctl print "system/$LABEL" 2>/dev/null | grep -E "state = |pid = |runs =" || echo "未运行"
echo "--- 当前转速 ---"
"$PY" "$TOOL" --show 2>&1 | tail -3
echo
echo "曲线：${LO}℃ 起提速 → ${HI}℃ 满转，每 20 秒采样。日志：$LOG"
echo "建议退出 Macs Fan Control，避免它抢写：osascript -e 'quit app \"Macs Fan Control\"'"
echo "卸载：sudo bash $0 --uninstall    状态：sudo bash $0 --status"
