#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artifact_push_stage.py - 把"产物回传"做成节点脉冲里的日常站，而不是抢占生产车道的队列卡。

为什么（2026-11-04 实测）：
  回传卡按"解锁下游数量"排序时解锁数=0（bm-a MANIFEST 里全是历史 review JSON，当前没有卡
  在等它们），所以它永远让给内容卡；而它又必须每天跑，否则主控看不到媒体、本机没素材加工。
  结论：基础设施动作不该进"抢车道"的排序，应该像心跳一样按节拍跑。

行为：
  * 非 Windows（Mac/Linux）：直接跳过（回传脚本是 PowerShell，且主控不产媒体）。
  * Windows：一天只跑一次（state/artifact-push-<node>.json 记日期），调 artifact_push.ps1。
Exit: 0 跳过或成功；1 回传有失败（rc 原样透出）；3 脚本缺失
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE_DIR = os.path.join(ROOT, "cph4", "fleet", "state")
PS = os.path.join(ROOT, "Tools", "fleet", "artifact_push.ps1")


def main():
    node = os.environ.get("NODE", "")
    if not node:
        print("[artifact-push] 没有 NODE，跳过")
        return 0
    if os.name != "nt":
        print("[artifact-push] 非 Windows 节点（%s），跳过（主控不产媒体）" % node)
        return 0
    if not os.path.exists(PS):
        print("[artifact-push] 缺 %s（rc=3）" % PS)
        return 3
    stamp = os.path.join(STATE_DIR, "artifact-push-%s.json" % node)
    today = time.strftime("%Y-%m-%d")
    try:
        if json.load(open(stamp, encoding="utf-8")).get("date") == today:
            print("[artifact-push] %s 今天已回传过，跳过" % node)
            return 0
    except Exception:
        pass
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", PS,
           "-Root", ROOT, "-Node", node, "-MaxMB", "2048"]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    sec = round(time.time() - t0, 1)
    tail = ((r.stdout or "") + (r.stderr or "")).strip()[-400:]
    ok = r.returncode == 0
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump({"date": today, "rc": r.returncode, "sec": sec, "tail": tail},
              open(stamp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[artifact-push] %s rc=%s %ss %s" % (node, r.returncode, sec, tail.replace("\n", " ")[:160]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())