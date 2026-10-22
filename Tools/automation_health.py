# -*- coding: utf-8 -*-
"""automation_health.py —— 自动化健康检查（PROCESS-REVIEW-v1 M10）

检查：计划任务是否还会触发、inbox 是否积压、worker 日志是否在写。
异常只写台账，不弹窗。
"""
import json, os, subprocess, datetime, glob

OUT = r"D:\FleetWorker\logs\automation-health.log"
INBOX = r"D:\FleetWorker\inbox"
STATE = r"D:\FleetWorker\state"
TASKS = ["ComputeWorker", "ComputeGuard"]


def log(lines):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")


def ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, errors="replace")
    return r.stdout.strip()


def main():
    now = datetime.datetime.now()
    issues, lines = [], ["=== %s ===" % now.strftime("%Y-%m-%d %H:%M")]

    for t in TASKS:
        raw = ps("$i=Get-ScheduledTaskInfo -TaskName %s; "
                 "\"$($i.NextRunTime)|$($i.LastRunTime)|$($i.LastTaskResult)\"" % t)
        parts = raw.split("|")
        nxt = parts[0] if parts else ""
        lines.append("task %-14s next=%s last=%s rc=%s" % (t, nxt, parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""))
        if not nxt or nxt == "":
            issues.append("%s 的 NextRunTime 为空（触发器可能已失效）" % t)
        else:
            try:
                dt = datetime.datetime.strptime(nxt.strip(), "%Y/%m/%d %H:%M:%S")
                if dt < now - datetime.timedelta(hours=1):
                    issues.append("%s 的下次运行时间在过去：%s" % (t, nxt))
            except Exception:
                pass

    pend = [f for f in glob.glob(os.path.join(INBOX, "*.json"))]
    lines.append("inbox 待执行: %d 件" % len(pend))
    if len(pend) > 5:
        issues.append("inbox 积压 %d 件" % len(pend))

    wlogs = sorted(glob.glob(r"D:\FleetWorker\logs\worker-*.log"))
    if wlogs:
        age_h = (now - datetime.datetime.fromtimestamp(os.path.getmtime(wlogs[-1]))).total_seconds() / 3600
        lines.append("最近 worker 日志: %s（%.1f 小时前）" % (os.path.basename(wlogs[-1]), age_h))
        if age_h > 26:
            issues.append("worker 日志 %.0f 小时未更新（可能已停摆）" % age_h)
    else:
        issues.append("找不到 worker 日志")

    lines.append("问题: %d" % len(issues))
    for i in issues:
        lines.append("  ! " + i)
    log(lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()