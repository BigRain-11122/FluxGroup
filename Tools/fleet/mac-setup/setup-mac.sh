#!/bin/bash
# setup-mac.sh - put the MacBook on the bus as an ON-DEMAND node, with almost no disk.
#
# CEO 2026-10-29: the laptop is NOT a resident 24/7 box - it runs tasks when awake and
# stops when closed. So by default this installs NO background service: it prepares the
# clone and leaves one script you run when you want the Mac to work.
# Opt in to a daemon only if that changes:   INSTALL_DAEMON=1 bash setup-mac.sh
#
# Usage:  bash setup-mac.sh
#         ROOT=~/work/FluxGroup bash setup-mac.sh
#         INSTALL_DAEMON=1 bash setup-mac.sh
set -euo pipefail

ROOT="${ROOT:-$HOME/FluxGroup}"
REPO="${REPO:-git@github.com:BigRain-11122/FluxGroup.git}"
NODE="${NODE:-bm-m}"

command -v git >/dev/null || { echo "need git (xcode-select --install)"; exit 1; }
command -v python3 >/dev/null || { echo "need python3 (xcode-select --install)"; exit 1; }

SPARSE_PATHS=(
  '/AI.md' '/CODELY.md'
  '/Tools/fleet/' '/Tools/queue_claim.py' '/Tools/backlog_fill.py'
  '/cph4/fleet/*.json' '/cph4/fleet/*.jsonl' '/cph4/fleet/*.md'
  '/cph4/fleet/dispatcher/' '/cph4/fleet/lanes/'
  '/cph4/fleet/queue-receipts/' '/cph4/fleet/cmd/' '/cph4/fleet/acks/'
  '/docs/orders.md'
)

echo "== clone (blob-filter + sparse: media/art/model files never land) =="
if [ ! -d "$ROOT/.git" ]; then
  # --no-checkout matters: without it the first checkout materialises every tracked file,
  # which on this repo means media. Fetch refs first, restrict, then checkout.
  git clone --filter=blob:none --no-checkout "$REPO" "$ROOT"
fi
cd "$ROOT"
git sparse-checkout set --no-cone "${SPARSE_PATHS[@]}"
git checkout main 2>/dev/null || git switch main
git pull --ff-only || true
echo "   footprint: $(du -sh "$ROOT" | cut -f1)"

echo "== on-demand runner =="
cat > "$ROOT/tools-run-once.sh" <<'RUN'
#!/bin/bash
# One working session on the Mac: heartbeat, then one scheduler tick, then (if this box is
# allowed to work) one lane job. Run it when you want the laptop to participate; nothing
# stays resident afterwards.
set -uo pipefail
cd "$(dirname "$0")"
python3 Tools/fleet/fleet_hb.py --node "${NODE:-bm-m}" --root "$PWD" || true
python3 Tools/fleet/master_agent.py --node "${NODE:-bm-m}" --root "$PWD" --no-push || true
python3 Tools/fleet/lane_agent.py --node "${NODE:-bm-m}" --root "$PWD" || true
RUN
chmod +x "$ROOT/tools-run-once.sh"

if [ "${INSTALL_DAEMON:-0}" = "1" ]; then
  echo "== daemon (opted in) =="
  mkdir -p "$HOME/Library/LaunchAgents"
  cat > "$HOME/Library/LaunchAgents/com.fluxgroup.member.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxgroup.member</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>$ROOT/tools-run-once.sh</string>
  </array>
  <key>StartInterval</key><integer>600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>/tmp/fluxgroup-member.log</string>
  <key>StandardErrorPath</key><string>/tmp/fluxgroup-member.err</string>
</dict></plist>
PLIST
  launchctl unload "$HOME/Library/LaunchAgents/com.fluxgroup.member.plist" 2>/dev/null || true
  launchctl load "$HOME/Library/LaunchAgents/com.fluxgroup.member.plist"
  echo "   installed: com.fluxgroup.member (every 600s while the Mac is awake)"
fi

cat <<EOF

== done ==
clone     : $ROOT  ($(du -sh "$ROOT" | cut -f1))
runner    : bash $ROOT/tools-run-once.sh      <- run this when you want the Mac to work
daemon    : ${INSTALL_DAEMON:-0} (0 = not installed; the laptop stays non-resident)

still to do by hand:
  1) Tailscale: join the same tailnet, then tell bm-a the machine name
  2) first run:  bash $ROOT/tools-run-once.sh   -> expect "STANDBY node=$NODE ..."
     (standby is correct; the scheduler still lives on bm-a)
EOF