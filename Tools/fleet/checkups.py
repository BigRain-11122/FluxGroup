#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checkups.py - 体检执行器：一张单子一条线，一个执行器跑所有线。

主张（2026-11-02）：要"多张体检单"，不要"多个常驻大脑"。
加一条线＝加一张单，不加人；判定是确定性的，只有归因交给总管。

单子：cph4/fleet/checkups/<line>.json
  {"line","priority","evidence":[...],"checks":[{"name","type",...}]}
支持类型：
  glob     {path,pattern,min}        文件数不少于 min
  age_h    {path,max}                该目录最新文件不超过 max 小时
  json_keys{path,required[]}         目录下任一 json 含全部键
  size_min {path,pattern,min_mb}     有文件且不小于
  exists   {path}

输出：cph4/fleet/state/checkups.json + 一屏；退出码 0 全过 / 2 有失败。
用法：python3 checkups.py [--json] [--line X]
"""
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
DIRS = os.path.join(FLEET, "checkups")
STATE = os.path.join(FLEET, "state")


def resolve(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def files(path, pattern="*"):
    import fnmatch
    root = resolve(path)
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        for n in names:
            if fnmatch.fnmatch(n, pattern):
                out.append(os.path.join(dirpath, n))
    return out


def check(c):
    """返回 (True/False/None, detail)。None = 本机没有这个仓/目录，不该判红也不该判绿。"""
    t = c.get("type")
    p = c.get("path", "")
    if t != "exists" and p and not os.path.exists(resolve(p)):
        return None, "本机无此目录（远端）"
    try:
        if t == "glob":
            n = len(files(p, c.get("pattern", "*")))
            return n >= int(c.get("min", 1)), "%d 个" % n
        if t == "age_h":
            fs = files(p, c.get("pattern", "*"))
            if not fs:
                return False, "无文件"
            newest = max(os.path.getmtime(f) for f in fs)
            age = (time.time() - newest) / 3600.0
            return age <= float(c.get("max", 48)), "%.1fh" % age
        if t == "json_keys":
            req = c.get("required") or []
            for f in files(p, "*.json"):
                try:
                    d = json.load(open(f, encoding="utf-8-sig"))
                except Exception:
                    continue
                flat = json.dumps(d, ensure_ascii=False)
                if all(k in flat for k in req):
                    return True, "齐"
            return False, "缺键"
        if t == "size_min":
            fs = files(p, c.get("pattern", "*"))
            big = [f for f in fs if os.path.getsize(f) >= float(c.get("min_mb", 0)) * 1048576]
            return bool(big), "%d 个够大" % len(big)
        if t == "exists":
            return os.path.exists(resolve(p)), "在" if os.path.exists(resolve(p)) else "缺"
    except Exception as e:
        return False, "err:%s" % str(e)[:30]
    return True, "skip"


def main(argv):
    only = ""
    for i, a in enumerate(argv):
        if a == "--line" and i + 1 < len(argv):
            only = argv[i + 1]
    os.makedirs(STATE, exist_ok=True)
    rows = []
    if not os.path.isdir(DIRS):
        print("没有体检单目录")
        return 2
    for n in sorted(os.listdir(DIRS)):
        if not n.endswith(".json"):
            continue
        spec = json.load(open(os.path.join(DIRS, n), encoding="utf-8-sig"))
        if only and spec.get("line") != only:
            continue
        res = []
        for c in spec.get("checks") or []:
            ok, detail = check(c)
            res.append({"name": c.get("name"), "pass": ok, "detail": detail})
        failed = [r for r in res if r["pass"] is False]
        neutral = [r for r in res if r["pass"] is None]
        status = "FAIL" if failed else ("REMOTE" if len(neutral) == len(res) else "PASS")
        rows.append({"line": spec.get("line"), "priority": spec.get("priority"),
                     "status": status, "failed": failed, "total": len(res)})
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "lines": rows}
    json.dump(out, open(os.path.join(STATE, "checkups.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if not any(r["status"] == "FAIL" for r in rows) else 2
    for r in rows:
        mark = {"PASS": "✓", "FAIL": "✗", "REMOTE": "△"}[r["status"]]
        print("%s %-18s %-3s %d/%d %s" % (
            mark, r["line"], r["priority"], r["total"] - len(r["failed"]), r["total"],
            "" if r["status"] != "FAIL" else "｜" + "、".join("%s(%s)" % (f["name"], f["detail"])
                                                for f in r["failed"][:3])))
    bad = sum(1 for r in rows if r["status"] == "FAIL")
    print("不合格线 %d / %d -> state/checkups.json" % (bad, len(rows)))
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))