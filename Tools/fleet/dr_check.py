# -*- coding: utf-8 -*-
"""dr_check.py - 灾难恢复体检：这台机器坏了之后，多久能重新站起来。

不真做恢复（危险且耗资源），只核对三件会被忽略的事：
  1. 备份是否新鲜、是否可解析（备份存在但打不开 = 没有备份）；
  2. 关键配置是否都在 git 里（不在 git 的配置 = 机器死了就永久丢失）；
  3. 接管清单是否可执行（新机要 clone 什么、装什么、跑什么、验什么）。

RTO/RPO 是本文件的显式声明，不是口号：
  RTO = 主控接管 ≤ 30 分钟（clone + 依赖 + 启动 + 一屏出数）
  RPO = 数据损失 ≤ 24 小时（每日备份一次；队列只在 git，损失为 0）

Usage: dr_check.py [--json]
Exit: 0 可恢复；1 有缺口
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
BACKUP = os.path.join(STATE, "backup.json")
OUT = os.path.join(FLEET, "DR-PLAN.md")

RTO_MIN = 30
RPO_HOURS = 24
# 机器死了不能丢的东西：必须在 git 里
CRITICAL_TRACKED = [
    "Tools/fleet/master_pulse.py", "Tools/fleet/lane_agent.py", "Tools/fleet/fleet_lane.py",
    "Tools/fleet-nodes.json", "cph4/fleet/AUTONOMY-CONFIG.json",
    "cph4/fleet/LOCAL-MODEL-POLICY.json", "cph4/fleet/MODEL-POLICY.json",
    "cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/COMMAND-CADENCE-v3.json",
    "CODELY.md",
]
PARSEABLE = ["Tools/fleet-nodes.json", "cph4/fleet/AUTONOMY-CONFIG.json",
             "cph4/fleet/LOCAL-MODEL-POLICY.json", "cph4/fleet/MODEL-POLICY.json",
             "cph4/fleet/COMMAND-CADENCE-v3.json", "cph4/fleet/SERVICE-LEVEL-v1.json"]
TAKEOVER_STEPS = [
    ("1", "装基础依赖", "git / python3 / ffmpeg / ollama（winget 或 brew，见 bootstrap-machine.ps1）"),
    ("2", "拉控制面", "git clone git@github.com:BigRain-11122/FluxGroup.git && cd FluxGroup"),
    ("3", "装模型", "ollama pull qwen3.5:4b-mlx && ollama pull qwen3-embedding:0.6b"),
    ("4", "起常驻脉", "python3 Tools/fleet/master_pulse.py --no-pull 冒烟一次，再 launchctl/kickstart 常驻"),
    ("5", "验三件事", "COMMAND-BOARD.md 有数 / CEO-NEXT.md 有 top / cadence.py --check 为 PASS"),
    ("6", "接入机队", "改 Tools/fleet-nodes.json 的本机 root，然后逐台 /poke 唤醒"),
]


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def tracked_set():
    try:
        p = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return set((p.stdout or "").splitlines())
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tracked = tracked_set()
    gaps = []

    # 1 关键文件是否在 git
    missing = [f for f in CRITICAL_TRACKED if f not in tracked and not os.path.exists(
        os.path.join(ROOT, f))]
    untracked = [f for f in CRITICAL_TRACKED
                 if os.path.exists(os.path.join(ROOT, f)) and f not in tracked]
    if missing:
        gaps.append("关键文件既不在 git 也不在盘：%s" % missing[:4])
    if untracked:
        gaps.append("%d 个关键文件未跟踪（机器死了会丢）：%s" % (len(untracked), untracked[:4]))

    # 2 关键配置能否解析
    bad_parse = []
    for rel in PARSEABLE:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        if jload(p) is None:
            bad_parse.append(rel)
    if bad_parse:
        gaps.append("配置无法解析（备份等于坏件）：%s" % bad_parse)

    # 3 备份新鲜度
    b = jload(BACKUP, {}) or {}
    bts = str(b.get("ts") or b.get("updated") or "")
    age_h = None
    if bts:
        try:
            age_h = round((time.time() - time.mktime(
                time.strptime(bts[:19], "%Y-%m-%dT%H:%M:%S"))) / 3600.0, 1)
        except Exception:
            age_h = None
    if not b:
        gaps.append("没有备份记录（backup 阶段尚未产出 state/backup.json）")
    elif age_h is not None and age_h > RPO_HOURS:
        gaps.append("备份已 %.1f 小时，超过 RPO %d 小时" % (age_h, RPO_HOURS))

    # 4 车道与队列是否可重建（机队接管的前提）
    for rel in ("cph4/fleet/PRODUCTION-QUEUE.jsonl",):
        if rel not in tracked:
            gaps.append("%s 未进 git，机队无法接管" % rel)

    verdict = "GAPS" if gaps else "OK"
    L = ["# 灾难恢复计划 %s" % time.strftime("%Y-%m-%dT%H:%M:%S"), "",
         "判定：**%s**｜RTO ≤ %d 分钟｜RPO ≤ %d 小时" % (verdict, RTO_MIN, RPO_HOURS), "",
         "## 天空是斜的假设：这台机器今天坏掉", "",
         "队列与代码在 git，损失为 0；本地机时不重要。真正会丢的是**没有提交的改动**。", ""]
    L.append("## 新机接管六步（≤%d 分钟）" % RTO_MIN)
    L.append("")
    for no, name, how in TAKEOVER_STEPS:
        L.append("%s. **%s**：`%s`" % (no, name, how))
    L.append("")
    L.append("## 体检结果")
    L.append("")
    if gaps:
        for g in gaps:
            L.append("- ❌ %s" % g)
    else:
        L.append("- ✅ 关键文件在 git、配置可解析、备份在 RPO 内、队列可接管")
    L.append("")
    L.append("## 备份状态")
    L.append("")
    L.append("- 记录：%s" % (bts or "无"))
    L.append("- 年龄：%s" % (("%.1f 小时" % age_h) if age_h is not None else "未知"))
    L.append("")
    L.append("## 已知不可恢复项（如实列）")
    L.append("")
    L.append("1. 未提交的工作区改动（工作树共用导致）；")
    L.append("2. `state/` 下的运行时状态（按设计不进 git，可从队列与回执重建）；")
    L.append("3. 云端凭据与平台账号（在密码管理器里，不在此仓）。")
    L.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "dr-check.json"), "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": verdict,
                   "gaps": gaps, "backup_age_h": age_h, "rto_min": RTO_MIN,
                   "rpo_hours": RPO_HOURS}, f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": verdict, "gaps": len(gaps), "backup_age_h": age_h,
                      "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    for g in gaps[:6]:
        print("  GAP", g)
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())