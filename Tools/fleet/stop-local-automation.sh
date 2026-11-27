#!/bin/bash
# stop-local-automation.sh — 停掉本机全部 FluxGroup 自启与算力服务（可回滚）
# 令源：CEO 2026-11-27「先把本机自动化任务和算力分配都停了」
# 手法：bootout + disable + plist 移入 disabled/20261127-ceo-stop/（不删除）
# 留档：cph4/fleet/STOP-INVENTORY-20261127.json
# 恢复：把 plist 移回 ~/Library/LaunchAgents/，launchctl enable 后 bootstrap
set -u

LA="$HOME/Library/LaunchAgents"
PAUSED="$LA/disabled/20261127-ceo-stop"
U=$(id -u)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INV="$ROOT/cph4/fleet/STOP-INVENTORY-20261127.json"

mkdir -p "$PAUSED"

# 1) 停机前留档（标签/命令/触发方式/当时 pid）
python3 - "$LA" "$INV" "$PAUSED" <<'PY'
import datetime, glob, json, os, plistlib, subprocess, sys
la, inv, paused = sys.argv[1], sys.argv[2], sys.argv[3]
out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
loaded = {}
for line in out.splitlines()[1:]:
    p = line.split("\t")
    if len(p) >= 3:
        loaded[p[2]] = {"pid": p[0], "last_exit": p[1]}
items = []
for f in sorted(glob.glob(os.path.join(la, "com.fluxgroup.*.plist"))):
    with open(f, "rb") as fh:
        d = plistlib.load(fh)
    label = d.get("Label", os.path.basename(f)[:-6])
    items.append({
        "label": label,
        "plist": f,
        "program": d.get("ProgramArguments") or [d.get("Program", "")],
        "start_interval": d.get("StartInterval"),
        "keep_alive": d.get("KeepAlive"),
        "run_at_load": d.get("RunAtLoad"),
        "stdout": d.get("StandardOutPath"),
        "stderr": d.get("StandardErrorPath"),
        "loaded_before_stop": label in loaded,
        "pid_at_stop": loaded.get(label, {}).get("pid"),
        "last_exit_at_stop": loaded.get(label, {}).get("last_exit"),
    })
doc = {
    "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "why": "CEO 2026-11-27 令：先把本机自动化任务和算力分配都停了",
    "paused_dir": paused,
    "count": len(items),
    "items": items,
}
with open(inv, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1)
print("inventory: %s (%d items)" % (inv, len(items)))
PY

# 2) 卸载 + 持久禁用 + 归档 plist
stopped=0
for f in "$LA"/com.fluxgroup.*.plist; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  label="${base%.plist}"
  launchctl bootout "gui/$U/$label" 2>/dev/null || true
  launchctl disable "gui/$U/$label" 2>/dev/null || true
  mv "$f" "$PAUSED/$base"
  echo "stopped  $label"
  stopped=$((stopped+1))
done

# 3) 清掉已脱管的残留进程（只匹配本仓工具路径与服务名，不碰编辑器/CLI 本体）
pkill -f "$ROOT/Tools/fleet/" 2>/dev/null || true
pkill -f "train_build.py" 2>/dev/null || true
pkill -f "mlx_lm server" 2>/dev/null || true
sleep 1

# 4) 本地模型服务（算力占用）
launchctl bootout "gui/$U/com.ollama.ollama" 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true

echo "---- verify ----"
launchctl list | awk '$3 ~ /^com\.fluxgroup\./ {print "STILL LOADED: "$3}'
for p in 8788 11434 11436 8792; do
  if lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1; then
    echo "STILL LISTENING: $p"
  else
    echo "free: $p"
  fi
done
echo "plists archived: $(ls -1 "$PAUSED" | wc -l | tr -d ' ')  -> $PAUSED"
echo "done ($stopped stopped)"
