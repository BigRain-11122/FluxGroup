#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""os_matrix.py - 跨系统辨别与梳理（数据正身=cph4/fleet/OS-MATRIX-v1.json）。

CEO 2026-11-11：「我主控是苹果 mac，其他是 windows 系统都不一样，你好好辨别，然后梳理」。

它把"哪台机是什么系统"与"哪个脚本能在哪台机跑"变成可查的两张表：
  show           五台机的 OS / 解释器 / shell / 路径 / 锁 / 调度器 / 是否已核实
  audit          扫 Tools/fleet，按 POSIX-only / Windows-only 标记分类，
                 列出"只能在 Mac 跑且没有 Windows 伴生"的脚本，并核对配置一致性
  check --station X  这台机能跑哪些工具、哪些被 OS 挡住（未核实 OS 的机器一律拒派）
  --self-test

判据来自 OS-MATRIX-v1.json 的 rules：解释器名、路径盘符、文件锁、调度器、
编码换行、系统专属命令、未验证 OS 不得排卡。
Exit: 0 正常；1 有缺口（audit 报 gap）；2 配置异常
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
MATRIX = os.path.join(FLEET, "OS-MATRIX-v1.json")
STATIONS = os.path.join(FLEET, "STATIONS.json")
TOOLS = os.path.join(ROOT, "Tools", "fleet")
OUT = os.path.join(FLEET, "state", "os-matrix.json")


def load(path=MATRIX):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def classify(text, matrix):
    """按标记分类：cross（与系统无关）/ mac_only / win_only / dual（自己有分支）。

    精度纪律（2026-11-11 首版实测）：`launchctl` 出现在帮助文本/修法提示里也算命中，
    会把 26 个脚本误判成"只能在 Mac 跑"。所以：
      - 库级标记用 import 形态（fcntl/msvcrt 必须是 import，不是注释里提一句）
      - 命令级标记必须伴随 subprocess/os.system（真调用），纯文本提示不算
    """
    import re
    sh = ("subprocess" in text) or ("os.system" in text) or ("check_output" in text)
    mac_imp = bool(re.search(r"^\s*(?:import|from)\s+fcntl\b", text, re.M))
    win_imp = bool(re.search(r"^\s*(?:import|from)\s+msvcrt\b", text, re.M))
    mac_sh = sh and any(k in text for k in ("launchctl", "sysctl -n", "Get-ChildItem -Path /"))
    win_sh = sh and any(k in text for k in ("Get-ScheduledTask", "schtasks", "powershell"))
    mac = mac_imp or mac_sh or "os.getloadavg(" in text or "os.fork(" in text
    win = win_imp or win_sh
    hits = ([k for k in ("fcntl", "launchctl", "sysctl -n", "os.fork") if k in text][:2]
            + [k for k in ("msvcrt", "schtasks", "Get-ScheduledTask", "powershell") if k in text][:2])
    if mac and win:
        return "dual", hits, []
    if mac:
        return "mac_only", hits, []
    if win:
        return "win_only", [], hits
    return "cross", [], []


DEAD_RE = None


def _dead_paths(text):
    """只认"默认值/拼接"形态的死路径；注释、文档串、探测逻辑（判存在性）不算。
    2026-11-11 首版把 /Volumes/ 出现在注释里也算，报出 15 个其实只有几个是真默认值。"""
    import re
    pat = re.compile(r'''(os\.environ\.get\([^)\n]*"/Volumes/|= *"/Volumes/|os\.path\.join\(\s*"/Volumes/|default *= *"/Volumes/)''')
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.strip().startswith("#"):
            continue
        if pat.search(ln):
            out.append(i)
    return out


def has_branch(text):
    return any(k in text for k in ("sys.platform", "platform.system", "os.name", "msvcrt"))


def twin_of(path):
    stem = os.path.splitext(path)[0]
    for ext in (".ps1", ".cmd", ".bat", ".psm1"):
        if os.path.exists(stem + ext):
            return stem + ext
    return None


def scan(tools_dir=TOOLS, matrix=None):
    matrix = matrix or load()
    rows = []
    for name in sorted(os.listdir(tools_dir)):
        if not name.endswith(".py"):
            continue
        p = os.path.join(tools_dir, name)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            continue
        kind, mac, win = classify(text, matrix)
        dead = _dead_paths(text) if "/Volumes/" in text else []
        rows.append({"tool": name, "class": kind, "markers": (mac + win)[:4],
                     "dead_paths": dead, "branch": has_branch(text),
                     "twin": os.path.basename(twin_of(p) or "")})
    return rows


def audit(matrix=None, tools_dir=TOOLS):
    matrix = matrix or load()
    rows = scan(tools_dir, matrix)
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1

    # 只能在 Mac 跑、又没有 Windows 伴生/分支的脚本＝跨机隐患
    declared = set(((matrix.get("control_plane_only") or {}).get("tools")) or [])
    mac_only_all = [r["tool"] for r in rows
                    if r["class"] == "mac_only" and not r["branch"] and not r["twin"]]
    mac_only_gap = [t for t in mac_only_all if t not in declared]
    declared_hit = [t for t in mac_only_all if t in declared]

    # 与 STATIONS / LANES 对齐
    stations = {}
    try:
        with open(STATIONS, encoding="utf-8") as f:
            for s in (json.load(f).get("stations") or []):
                stations[s.get("id")] = s
    except Exception:
        pass
    m_machines = matrix.get("machines") or {}
    only_in_matrix = sorted(set(m_machines) - set(stations))
    only_in_stations = sorted(set(stations) - set(m_machines))
    unverified = sorted(mid for mid, m in m_machines.items() if not m.get("verified"))
    os_mismatch = []
    for mid, s in stations.items():
        if mid in m_machines:
            a = str(s.get("os") or "").lower()
            b = str(m_machines[mid].get("os") or "").lower()
            if a and b and a != b and b != "unverified":
                os_mismatch.append({"station": mid, "stations_json": a, "matrix": b})

    gaps = []
    if unverified:
        gaps.append({"id": "OS-7", "what": "未验证 OS 却可能被排卡",
                     "machines": unverified,
                     "fix": "装机当天按实测回填 OS；回填前任何卡不得落点"})
    dead_path = [r["tool"] for r in rows if r.get("dead_paths")]
    if dead_path:
        gaps.append({"id": "OS-8", "what": "默认值里还指着已退役的移动盘 /Volumes/",
                     "count": len(dead_path), "tools": dead_path[:12],
                     "fix": "改成 环境变量 > 配置 > 显式报错（移动盘 2026-11-11 已清空退出）"})
    if mac_only_gap:
        gaps.append({"id": "OS-1/3", "what": "只能在 Mac 跑且无分支/无伴生脚本",
                     "count": len(mac_only_gap), "tools": mac_only_gap[:12],
                     "fix": "要么加 platform 分支，要么配 .ps1 伴生，要么在卡上声明只排主控"})
    if os_mismatch:
        gaps.append({"id": "OS-0", "what": "STATIONS 与 OS-MATRIX 的系统声明不一致",
                     "detail": os_mismatch, "fix": "以实测为准改一处，不许两处各说一套"})
    if only_in_stations:
        gaps.append({"id": "OS-0", "what": "工位表有而系统矩阵缺的机器",
                     "machines": only_in_stations, "fix": "OS-MATRIX 补齐"})

    return {"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
            "tools_total": len(rows), "counts": counts,
            "mac_only_without_fallback": mac_only_gap,
            "declared_control_plane_only": declared_hit,
            "consistency": {"only_in_matrix": only_in_matrix,
                            "only_in_stations": only_in_stations,
                            "os_mismatch": os_mismatch,
                            "unverified": unverified},
            "gaps": gaps, "rows": rows}


def runnable_for(matrix, station, rows):
    m = (matrix.get("machines") or {}).get(station)
    if not m:
        return {"station": station, "error": "OS-MATRIX 里没有这台"}
    osname = str(m.get("os") or "").lower()
    if not m.get("verified"):
        return {"station": station, "os": osname, "ok": False,
                "why": "OS-7：系统未核实，一律不排卡（先装机实测回填）", "runnable": []}
    ok, blocked = [], []
    for r in rows:
        k = r["class"]
        if k in ("cross", "dual") or (k == "mac_only" and osname == "darwin") \
                or (k == "win_only" and osname == "windows"):
            ok.append(r["tool"])
        else:
            blocked.append({"tool": r["tool"], "class": k})
    return {"station": station, "os": osname, "ok": True,
            "runnable": ok, "blocked": blocked}


def self_test():
    import tempfile
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    m = load()
    # 1) 分类器：三种典型脚本要分对
    chk("含 import fcntl -> mac_only", classify("import fcntl\nx=1", m)[0] == "mac_only")
    chk("真调 powershell/Get-ScheduledTask -> win_only",
        classify("import subprocess\nsubprocess.run(['powershell','Get-ScheduledTask'])", m)[0] == "win_only")
    chk("仅文本提到 launchctl、没有 subprocess -> 仍算 cross（防误判）",
        classify("# 修法：launchctl kickstart -k x\nprint(1)", m)[0] == "cross")
    chk("含 msvcrt+fcntl 双实现 -> dual",
        classify("import fcntl\ntry:\n  import msvcrt", m)[0] == "dual")
    chk("普通脚本 -> cross", classify("print(1)", m)[0] == "cross")

    # 2) 解释器名必须随 OS 变（Windows 无 python3，实测 rc=9009）
    chk("macos 用 python3", "python3" in (m["machines"]["control"]["python"] or ""))
    chk("windows 用 python（不含 python3）",
        "python" in (m["machines"]["delivery"]["python"] or "").lower()
        and "python3" not in (m["machines"]["delivery"]["python"] or "").lower())

    # 3) 未核实 OS 的机器必须被拒派（OS-7）
    r = runnable_for(m, "brain", [{"tool": "a.py", "class": "cross"}])
    chk("未核实 OS 的机器拒派一切", r["ok"] is False and "OS-7" in r["why"], r)

    # 4) Mac 专用脚本不得出现在 Windows 机的可跑清单里
    r = runnable_for(m, "delivery", [{"tool": "pulse.py", "class": "mac_only"},
                                     {"tool": "ok.py", "class": "cross"}])
    chk("mac_only 不进 Windows 可跑清单",
        r["ok"] and [x["tool"] for x in r["blocked"]] == ["pulse.py"], r)

    # 5) 人肉构造一个目录，验证"有分支不算缺口、无分支算缺口"
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "a_branch.py"), "w").write("import sys\nif sys.platform=='darwin':\n  pass\nlaunchctl\n")
        open(os.path.join(td, "b_bare.py"), "w").write("import fcntl\n")
        open(os.path.join(td, "c_twin.py"), "w").write("import fcntl\n")
        open(os.path.join(td, "c_twin.ps1"), "w").write("# twin\n")
        rows = scan(td, m)
        gap = [r["tool"] for r in rows if r["class"] == "mac_only" and not r["branch"] and not r["twin"]]
        chk("有分支或有 .ps1 伴生 -> 不算缺口", gap == ["b_bare.py"], gap)

    # 6) 真实仓库的审计必须能跑通并报出未核实机器
    a = audit(m)
    chk("审计报出未核实的 brain", "brain" in (a["consistency"]["unverified"] or []), a["consistency"])
    chk("审计统计了工具分类", a["tools_total"] > 0 and a["counts"], a["counts"])

    # 7) 规则表齐全（六条判别 + 未验证律）
    rules = [r.get("id") for r in (m.get("rules") or [])]
    chk("规则表含 OS-1..OS-7", all(("OS-%d" % i) in rules for i in range(1, 8)), rules)

    print("[os_matrix] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="show", choices=["show", "audit", "check"])
    ap.add_argument("--station", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    try:
        m = load()
    except Exception as e:
        print("配置读不了：%s" % e)
        return 2

    if a.cmd == "show":
        print("%-9s %-9s %-6s %-12s %-14s %s"
              % ("工位", "系统", "核实", "解释器", "文件锁", "调度器"))
        for mid, d in (m.get("machines") or {}).items():
            print("%-9s %-9s %-6s %-12s %-14s %s"
                  % (mid, d.get("os_label") or d.get("os"),
                     "是" if d.get("verified") else "否",
                     d.get("python"), d.get("lock"), (d.get("scheduler") or "")[:24]))
            if not d.get("verified"):
                print("          ↳ 待决：%s" % (d.get("decision_needed") or ""))
        return 0

    if a.cmd == "check":
        if not a.station:
            print("要给 --station（control/delivery/visual/audio/brain）")
            return 1
        r = runnable_for(m, a.station, scan(TOOLS, m))
        print(json.dumps({k: v for k, v in r.items() if k != "runnable"}, ensure_ascii=False, indent=1))
        print("可跑 %d 个工具" % len(r.get("runnable") or []))
        return 0 if r.get("ok") else 1

    a_report = audit(m)
    print("工具 %d 个：cross %d / dual %d / mac_only %d / win_only %d"
          % (a_report["tools_total"], a_report["counts"].get("cross", 0),
             a_report["counts"].get("dual", 0), a_report["counts"].get("mac_only", 0),
             a_report["counts"].get("win_only", 0)))
    for g in a_report["gaps"]:
        print("  缺口 %-8s %s" % (g["id"], g["what"]))
        if g.get("count"):
            print("      数量 %d，示例：%s" % (g["count"], ", ".join(g.get("tools") or [])))
        if g.get("machines"):
            print("      机器：%s" % ", ".join(g["machines"]))
        if g.get("fix"):
            print("      修法：%s" % g["fix"])
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(a_report, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 1 if a_report["gaps"] else 0


if __name__ == "__main__":
    sys.exit(main())
