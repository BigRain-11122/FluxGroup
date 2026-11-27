#!/bin/bash
# agent_install.sh <alias> [--print]  —— 为某个账号生成并装载 24h 常驻智能体。
# 加号只该改配置：账号在 bili-accounts.json 里登记后，跑这一条就能上线。
set -uo pipefail
A="${1:?用法: agent_install.sh <alias> [--print]}"
PRINT="${2:-}"
U="$(id -u)"
ROOT="/Users/junsheng.sun/FluxGroup"
PLIST="$HOME/Library/LaunchAgents/com.fluxgroup.agent-$A.plist"
LABEL="com.fluxgroup.agent-$A"

# 先确认账号已登记（未登记就别装，避免装了个空壳）
python3 - "$A" <<'PY' || exit 2
import json, os, sys
alias = sys.argv[1]
p = os.path.expanduser("~/.fluxgroup/bili-accounts.json")
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception:
    print("读不到账号表"); sys.exit(2)
a = (d.get("accounts") or {}).get(alias)
if not isinstance(a, dict) or not a.get("profile"):
    print("账号未登记：%s（先跑 bili_login.py --new %s）" % (alias, alias)); sys.exit(2)
print("账号 %s → %s（%s）" % (alias, a.get("uname") or "-", a.get("platform") or "bilibili"))
PY

cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$ROOT/.venv-housing/bin/python</string>
    <string>$ROOT/Tools/fleet/agent_daemon.py</string>
    <string>--account</string><string>$A</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>StandardOutPath</key><string>$ROOT/.codely-cli/state/agent-$A.log</string>
  <key>StandardErrorPath</key><string>$ROOT/.codely-cli/state/agent-$A.log</string>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHONUNBUFFERED</key><string>1</string>
        <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>Nice</key><integer>5</integer>
</dict>
</plist>
PL
echo "已生成 $PLIST"
if [ "$PRINT" = "--print" ]; then echo "（--print：只生成不装载）"; exit 0; fi
launchctl bootout "gui/$U/$LABEL" 2>/dev/null
launchctl bootstrap "gui/$U" "$PLIST" && echo "已装载并启动 $LABEL"
launchctl list | grep -F "$LABEL" || echo "注意：launchctl 里看不到该任务"
