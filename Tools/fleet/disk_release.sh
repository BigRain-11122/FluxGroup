#!/bin/bash
# disk_release.sh - 一键把外接盘交还给系统：让机队停手 → 同步 → 干净卸卷。
#
# 为什么（2026-11-04 CEO「一直提示我外接移动硬盘没正常工作」）：
#   盘本身 fsck 通过、日志里没有 USB 复位或"未正常推出"，但机队的 intake/打标/资产核验
#   会持续在这个卷上开文件。macOS 判定"盘正在使用"时拒绝推出，用户拔线就收到未正常推出提示。
#   彻底解决=不是让用户去追哪个进程，而是给一个"我要拔盘"的开关：置旗 → 各任务跳过该卷 →
#   同步 → unmount；用完再放旗恢复。
#
# 用法：
#   bash Tools/fleet/disk_release.sh status       # 看旗标与占用情况
#   bash Tools/fleet/disk_release.sh release      # 置旗 + 干净卸卷（可安全拔线）
#   bash Tools/fleet/disk_release.sh restore      # 放旗并重新挂回
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FLAG="$HOME/.fluxgroup-disk-release"
VOL="${FLUX_EXT:-/Volumes/移动硬盘}"

say() { printf '[disk] %s\n' "$*"; }

case "${1:-status}" in
  status)
    [ -f "$FLAG" ] && say "旗标：已置（机队会跳过 $VOL）" || say "旗标：未置（机队正常使用）"
    if mount | grep -q "$VOL"; then say "挂载：是"; else say "挂载：否"; fi
    n=$(lsof +D "$VOL" 2>/dev/null | wc -l | tr -d ' ')
    say "打开该卷的文件句柄：$n"
    lsof +D "$VOL" 2>/dev/null | awk 'NR>1{print "  "$1" pid="$2" "$9}' | head -8
    ;;
  release)
    touch "$FLAG"; say "已置旗：新任务不再碰该卷"
    say "等待在跑的读写结束（最多 20s）…"; sleep 20
    sync
    if diskutil unmount "$VOL" 2>&1 | tail -2; then say "已干净卸卷，可以拔线"; else
      say "卸卷受阻，列出占用者："; lsof +D "$VOL" 2>/dev/null | awk 'NR>1{print "  "$1" pid="$2}' | head -10
      exit 2
    fi
    ;;
  restore)
    rm -f "$FLAG"; say "已放旗"
    if ! mount | grep -q "$VOL"; then
      # 卸卷后挂载点会消失，必须按设备节点挂回（实测 `diskutil mount /Volumes/移动硬盘`
      # 会报 Failed to find disk）
      dev=$(diskutil list | awk '/移动硬盘/{print $NF}' | tail -1)
      if [ -n "$dev" ]; then
        diskutil mount "$dev" 2>&1 | tail -2 || say "挂载失败：请重新插一次线"
      else
        say "找不到该卷的设备节点：请重新插一次线"
      fi
    fi
    ;;
  *)
    say "用法: $0 {status|release|restore}"; exit 2;;
esac