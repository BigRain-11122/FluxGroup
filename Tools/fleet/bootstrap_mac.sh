#!/usr/bin/env bash
# bootstrap_mac.sh - join the Mac (bm-m) to the fleet as master-control + iOS build node.
# Run ON THE MAC, once:
#   bash Tools/fleet/bootstrap_mac.sh
# Prereqs: Tailscale installed and signed in; git; python3 (Xcode CLT); SSH key for the repo.
set -euo pipefail

ROOT="${ROOT:-$HOME/FluxGroup}"
NODE="${NODE:-bm-m}"
HUB="${HUB:-100.110.185.62}"
REPO="${REPO:-git@github.com:BigRain-11122/FluxGroup.git}"

echo "== fluxgroup mac bootstrap: node=$NODE root=$ROOT =="

command -v git >/dev/null || { echo "FAIL: git missing"; exit 1; }
command -v python3 >/dev/null || { echo "FAIL: python3 missing (xcode-select --install)"; exit 1; }
TS="$(command -v tailscale || true)"
if [ -z "$TS" ] && [ -x "/Applications/Tailscale.app/Contents/MacOS/Tailscale" ]; then
  TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
fi
if [ -z "$TS" ]; then
  echo "FAIL: Tailscale missing. Install: brew install --cask tailscale (or App Store), sign in, rerun."
  exit 1
fi
"$TS" status >/dev/null 2>&1 || { echo "FAIL: tailscale not connected"; exit 1; }
IP="$("$TS" ip -4 | head -1)"
[ -n "$IP" ] || { echo "FAIL: no tailnet IPv4"; exit 1; }
HOST="$(scutil --get ComputerName 2>/dev/null || hostname)"
echo "tailnet=$IP host=$HOST"

if [ ! -d "$ROOT/.git" ]; then
  echo "cloning $REPO -> $ROOT"
  git clone "$REPO" "$ROOT"
fi
cd "$ROOT"
git fetch origin main
git checkout main
git pull --ff-only origin main || { echo "FAIL: pull not fast-forward; resolve git status first"; exit 1; }

python3 - "$ROOT" "$HOST" "$IP" <<'PY'
import json, sys
root, host, ip = sys.argv[1:4]
p = root + "/Tools/fleet-nodes.json"
d = json.load(open(p, encoding="utf-8-sig"))
for n in d["nodes"]:
    if n["id"] == "bm-m":
        n["host"] = host
        n["tailnet_ip"] = ip
        n["root"] = root
        n["enabled"] = True
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("roster updated:", host, ip)
PY

python3 Tools/fleet/fleet_hb.py --node "$NODE" --hub "$HUB" --root "$ROOT" || true

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.fluxgroup/logs"
cat > "$HOME/Library/LaunchAgents/com.fluxgroup.fleet-hb.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.fleet-hb</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>$ROOT/Tools/fleet/fleet_hb.py</string>
    <string>--node</string><string>$NODE</string><string>--hub</string><string>$HUB</string>
  </array>
  <key>StartInterval</key><integer>60</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/.fluxgroup/logs/hb.log</string>
  <key>StandardErrorPath</key><string>$HOME/.fluxgroup/logs/hb.err</string>
</dict></plist>
EOF

cat > "$HOME/Library/LaunchAgents/com.fluxgroup.fleet-agent.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.fleet-agent</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>$ROOT/Tools/fleet/fleet_agent.py</string>
    <string>--node</string><string>$NODE</string><string>--serve</string>
  </array>
  <key>KeepAlive</key><true/>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/.fluxgroup/logs/agent.log</string>
  <key>StandardErrorPath</key><string>$HOME/.fluxgroup/logs/agent.err</string>
</dict></plist>
EOF

cat > "$HOME/Library/LaunchAgents/com.fluxgroup.keepawake.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.keepawake</string>
  <key>ProgramArguments</key><array><string>/usr/bin/caffeinate</string><string>-s</string></array>
  <key>KeepAlive</key><true/>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF

for p in com.fluxgroup.fleet-hb com.fluxgroup.fleet-agent com.fluxgroup.keepawake; do
  launchctl unload "$HOME/Library/LaunchAgents/$p.plist" 2>/dev/null || true
  launchctl load -w "$HOME/Library/LaunchAgents/$p.plist"
done

echo "== verify =="
python3 Tools/fleet/fleet_hb.py --node "$NODE" --hub "$HUB" --root "$ROOT" || true
echo "OK: bm-m joined. Check on bm-a: Tools/nats/fleet-clock-report.ps1 (bm-m should appear)."
echo "Master-control cutover stays manual until bm-m runs stable for 24h; bm-a remains hot standby."