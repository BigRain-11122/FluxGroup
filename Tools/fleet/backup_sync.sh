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

EXT="${FG_BACKUP_ROOT:-/Volumes/移动硬盘}"
BK="$EXT/Backup/FluxGroup"
LOG="${FG_BACKUP_LOG:-/tmp/fg-backup.log}"

say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

[ -d "$EXT" ] || { say "SKIP 外置盘未挂载: $EXT"; exit 0; }
[ -d "$BK/.git" ] || { say "SKIP 备份仓不存在: $BK"; exit 0; }

cd "$BK" || { say "FAIL 无法进入备份仓"; exit 1; }

# 外置盘掉过电：如果上次同步被硬断，可能留下锁文件，之后每次都失败。
# 这个克隆只有本脚本在写，超过 30 分钟的锁肯定是死的，可以安全清掉。
for lk in .git/index.lock .git/shallow.lock; do
  if [ -f "$lk" ] && [ -n "$(find "$lk" -mmin +30 2>/dev/null)" ]; then
    rm -f "$lk" && say "NOTE 清理陈旧锁 $lk"
  fi
done

before=$(git rev-parse HEAD 2>/dev/null || echo "")
git fetch --prune --quiet origin 2>>"$LOG" || { say "FAIL fetch（盘可能掉线）"; exit 1; }
git checkout -q main 2>>"$LOG"
git reset --hard -q origin/main 2>>"$LOG" || { say "FAIL reset"; exit 1; }
after=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ "$before" = "$after" ]; then
  say "OK 无变化 @ ${after:0:8}"
else
  n=$(git rev-list --count "${before}..${after}" 2>/dev/null || echo "?")
  say "OK ${before:0:8} -> ${after:0:8}（$n 个新提交）"
fi
exit 0