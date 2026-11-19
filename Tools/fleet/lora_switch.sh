#!/bin/bash
# 切换 8788 的适配器并等它就绪：写 ACTIVE 指针 → 重启 launchd → 探 /v1/models。
# 为什么要单独一支：闭环验收必须能"先换上去实测，不过再换回来"，
# 换的机制如果不确定，"回滚"就是一句空话。
set -uo pipefail
ROOT="/Users/junsheng.sun/FluxGroup"
UID_N="$(id -u)"
ADAPTER="${1:-}"
REASON="${2:-}"
if [[ -z "$ADAPTER" ]]; then echo "用法: lora_switch.sh <adapter 相对路径|base> [切换依据]"; exit 2; fi
if [[ "$ADAPTER" != "base" && ! -f "$ROOT/$ADAPTER/adapters.safetensors" ]]; then
  echo "适配器不存在：$ROOT/$ADAPTER"; exit 2
fi
python3 - "$ROOT" "$ADAPTER" "$REASON" <<'PY'
import json, sys, os
root, adapter, reason = sys.argv[1], sys.argv[2], sys.argv[3]
p = os.path.join(root, "cph4/fleet/social/train/ACTIVE.json")
cur = {}
try: cur = json.load(open(p, encoding="utf-8"))
except Exception: pass
if adapter == "base":
    # 回滚到基座：不挂任何适配器。此前"回滚"写死一个已被清理的权重目录，
    # 切不动却没人知道，被否的候选继续在线（2026-11-19 实锚）。
    cur.pop("adapter", None)
    cur["mode"] = "base"
    cur["run"] = ""
    cur["dataset"] = ""
else:
    cur["adapter"] = adapter
    # 必须清掉 mode=base：服务器见到 mode=base 就只跑基座，不清的话每次切换都是
    # 静默空操作（写进 ACTIVE 却不生效，正是 2026-11-19 那类"配置写了不等于生效"）。
    cur.pop("mode", None)
# 上一件的验收数字与归档路径不能跟着新指针走，否则账面是旧结论给新权重背书
cur.pop("eval", None)
cur.pop("archive", None)
# 依据必须与指针同批写入：只改 adapter 会留下上一次验收的 why，
# 账面像"已验收"，实际这件没人验过（2026-11-19 实锚）。
cur["why"] = reason or "(未提供验收依据) 由 lora_switch.sh 直接切换，质量按未验收处理"
cur["switched_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
json.dump(cur, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ACTIVE →", adapter or "base")
PY
launchctl bootout "gui/$UID_N/com.fluxgroup.mlxlora" 2>/dev/null
sleep 2
launchctl bootstrap "gui/$UID_N" "$HOME/Library/LaunchAgents/com.fluxgroup.mlxlora.plist" || exit 1
for i in $(seq 1 40); do
  if curl -s -m 3 http://127.0.0.1:8788/v1/models | grep -q '"id"'; then
    echo "[switch] 8788 就绪（${i}0%）"; exit 0
  fi
  sleep 3
done
echo "[switch] 8788 60 秒未就绪"; exit 1
