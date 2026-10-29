#!/bin/bash
# setup-mac.sh - put the MacBook on the bus as the control plane, with almost no disk.
#
# CEO 2026-10-29: the Mac is a scheduler, not a worker. So it clones ONLY the control
# plane (scheduler, queues, registries, order ledger) and never media, game art, or
# model files. Expected footprint: tens of MB, not tens of GB.
#
# Usage:  bash setup-mac.sh            (installs into ~/FluxGroup)
#         ROOT=~/work/FluxGroup bash setup-mac.sh
set -euo pipefail

ROOT="${ROOT:-$HOME/FluxGroup}"
REPO="${REPO:-git@github.com:BigRain-11122/FluxGroup.git}"
NODE="${NODE:-bm-m}"

command -v git >/dev/null || { echo "need git (xcode-select --install)"; exit 1; }
command -v python3 >/dev/null || { echo "need python3 (xcode-select --install)"; exit 1; }

echo "== clone (blob-filter + sparse: no media, no art) =="
if [ ! -d "$ROOT/.git" ]; then
  git clone --filter=blob:none --sparse "$REPO" "$ROOT"
  cd "$ROOT"
  git sparse-checkout set --no-cone \
    '/AI.md' '/CODELY.md' \
    '/Tools/fleet/' '/Tools/queue_claim.py' '/Tools/backlog_fill.py' \
    '/cph4/fleet/*.json' '/cph4/fleet/*.jsonl' '/cph4/fleet/*.md' \
    '/cph4/fleet/dispatcher/' '/cph4/fleet/lanes/' \
    '/cph4/fleet/queue-receipts/' '/cph4/fleet/cmd/' '/cph4/fleet/acks/' \
    '/cph4/fleet/WORK-RULES.disabled-20261029.jsonl' \
    '/docs/orders.md'
else
  cd "$ROOT"; git pull --ff-only || true
fi
echo "   footprint: $(du -sh "$ROOT" | cut -f1)"

echo "== launchd: scheduler every 2 minutes =="
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$HOME/Library/LaunchAgents/com.fluxgroup.master.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.master</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>$ROOT/Tools/fleet/master_agent.py</string>
    <string>--node</string><string>$NODE</string>
    <string>--root</string><string>$ROOT</string>
    <string>--no-push</string>
  </array>
  <key>StartInterval</key><integer>120</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>/tmp/fluxgroup-master.log</string>
  <key>StandardErrorPath</key><string>/tmp/fluxgroup-master.err</string>
</dict></plist>
PLIST

launchctl unload "$HOME/Library/LaunchAgents/com.fluxgroup.master.plist" 2>/dev/null || true
launchctl load "$HOME/Library/LaunchAgents/com.fluxgroup.master.plist"

echo "== heartbeat every 5 minutes =="
cat > "$HOME/Library/LaunchAgents/com.fluxgroup.hb.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.hb</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>$ROOT/Tools/fleet/fleet_hb.py</string>
    <string>--node</string><string>$NODE</string>
    <string>--root</string><string>$ROOT</string>
  </array>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>/tmp/fluxgroup-hb.err</string>
</dict></plist>
PLIST
launchctl unload "$HOME/Library/LaunchAgents/com.fluxgroup.hb.plist" 2>/dev/null || true
launchctl load "$HOME/Library/LaunchAgents/com.fluxgroup.hb.plist"

cat <<EOF

== done ==
scheduler : com.fluxgroup.master (every 120s, node=$NODE)
heartbeat : com.fluxgroup.hb     (every 300s)
logs      : /tmp/fluxgroup-master.log  /tmp/fluxgroup-hb.err

still to do by hand:
  1) Tailscale: install, join the same tailnet, then tell bm-a the machine name
     (bm-a writes it into Tools/fleet-nodes.json; the master starts counting it)
  2) keep it awake while plugged in:   caffeinate -dimsu &
  3) check it is alive:                tail -n 20 /tmp/fluxgroup-master.log
     expected line: STANDBY node=$NODE declared_master=bm-a
     (standby is correct until MASTER-NODE.json is switched to $NODE)
  4) switch the master later: edit cph4/fleet/MASTER-NODE.json -> "node": "$NODE", commit.
EOF