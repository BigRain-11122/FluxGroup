#!/bin/bash
# 冷备增量同步：把 FluxGroup 的最新提交同步到外置移动硬盘上的完整克隆。
#
# 分层原则（2026-11-02 定，实测依据）：
#   热区（本机 SSD，永不外移）—— cph4/fleet 全部（pulse 每分钟写）、.git、
#     Tools、CODELY.md。其中 cph4/fleet/mv0001-handover 有 202MB 且 24h 改动
#     469 个文件，是 MV 生产线，外置盘 89MB/s 的顺序写会把它拖慢一个数量级。
#   冷区（外置盘）—— 完整 git 克隆：全部历史、全部分支，可随时查阅或整仓恢复。
#     同步只传增量对象，不重拷工作树里没变的东西。
#
# 安全约定：
#   * 盘没挂载就干净退出（exit 0），绝不让备份失败去影响主控脉；
#   * 外置盘是镜像不是工作区，本地改动一律丢弃（reset --hard 到 origin/main）；
#   * 不 gc、不 repack，避免在 USB 机械盘上做重活。
set -u

# 2026-11-11 CEO 令：Mac 不再使用移动硬盘。本脚本改为"留痕退出"，
# 冷备由 git 远端（origin）承担；产物字节留在产出机，主控只收清单。
if [ "${FG_BACKUP_EXT_DISK:-0}" != "1" ]; then
  ST="${FG_BACKUP_STATE:-$(cd "$(dirname "$0")/../.." && pwd)/cph4/fleet/state/backup.json}"
  mkdir -p "$(dirname "$ST")" 2>/dev/null
  printf '{"ts":"%s","status":"DISABLED","detail":"external disk retired by CEO order 2026-11-11"}\n' \
    "$(date '+%FT%T')" > "$ST" 2>/dev/null
  echo "[$(date '+%F %T')] DISABLED 移动硬盘冷备已退役（CEO 2026-11-11）；备份走 git 远端"
  exit 0
fi

EXT="${FG_BACKUP_ROOT:-/Volumes/移动硬盘}"
BK="$EXT/Backup/FluxGroup"
LOG="${FG_BACKUP_LOG:-/tmp/fg-backup.log}"

say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# 状态落盘（2026-11-02）：这个脚本以前"盘没挂载就 exit 0"，于是冷备停了也没人知道——
# 实测备份仓落后 341 个提交，所有报表却都是绿的。任何"安静退出"的分支都必须留痕，
# 让"没做"变成可见事实（state/ 是可重建投影目录，只给本机看）。
STATE="${FG_BACKUP_STATE:-$(cd "$(dirname "$0")/../.." && pwd)/cph4/fleet/state/backup.json}"
status() {
  mkdir -p "$(dirname "$STATE")" 2>/dev/null
  printf '{"ts":"%s","status":"%s","detail":"%s","ext":"%s"}\n' \
    "$(date '+%FT%T')" "$1" "$2" "$EXT" > "$STATE" 2>/dev/null
}

[ -d "$EXT" ] || { say "SKIP 外置盘未挂载: $EXT"; status UNMOUNTED "volume not mounted"; exit 0; }
[ -d "$BK/.git" ] || { say "SKIP 备份仓不存在: $BK"; status NO-CLONE "backup clone missing"; exit 0; }

cd "$BK" || { say "FAIL 无法进入备份仓"; exit 1; }

# 外置盘掉过电：如果上次同步被硬断，可能留下锁文件，之后每次都失败。
# 这个克隆只有本脚本在写，超过 30 分钟的锁肯定是死的，可以安全清掉。
for lk in .git/index.lock .git/shallow.lock; do
  if [ -f "$lk" ] && [ -n "$(find "$lk" -mmin +30 2>/dev/null)" ]; then
    rm -f "$lk" && say "NOTE 清理陈旧锁 $lk"
  fi
done

before=$(git rev-parse HEAD 2>/dev/null || echo "")
# 掉盘/重枚举是常态（实测 3 小时 3 次）：先等 20 秒让卷回来，再 fetch；
# fetch 失败区分「盘掉线」与「权限被 TCC 拦」，前者重试一次，后者只留痕不拖红主控脉。
if [ ! -d "$EXT" ]; then
  for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 2
    [ -d "$EXT" ] && { say "NOTE 卷回来了（等了 ${i}0 秒内）"; break; }
  done
fi
fetch_try() {
  out=$(git fetch --prune --quiet origin 2>&1)
  rc=$?
  echo "$out" >> "$LOG" 2>/dev/null
  return $rc
}
if ! fetch_try; then
  sleep 10
  if ! fetch_try; then
    if printf '%s' "$out" | grep -qiE "operation not permitted|permission denied"; then
      say "SKIP 权限被拦（TCC 未授予完全磁盘访问）: $out"
      status TCC-BLOCKED "launchd 写可移除卷被拒；需在 隐私与安全性>完全磁盘访问 加 /usr/bin/python3 与 /bin/bash"
      exit 0
    fi
    say "FAIL fetch（盘掉线或网络）: $out"
    status FAIL "fetch failed: $out"
    exit 1
  fi
fi
git checkout -q main 2>>"$LOG"
git reset --hard -q origin/main 2>>"$LOG" || { say "FAIL reset"; exit 1; }
after=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ "$before" = "$after" ]; then
  say "OK 无变化 @ ${after:0:8}"
  status OK "up to date @ ${after:0:8}"
else
  n=$(git rev-list --count "${before}..${after}" 2>/dev/null || echo "?")
  say "OK ${before:0:8} -> ${after:0:8}（$n 个新提交）"
  status OK "${before:0:8} -> ${after:0:8} (${n} commits)"
fi
exit 0