#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artifact_status.py - 核对「机队声称产出的东西」是否真的落到了移动盘上。

契约见 cph4/fleet/ARTIFACT-BACKUP-RULES-v1.md：
  机队侧  cph4/fleet/artifacts/<node>/MANIFEST.jsonl  声明产出了什么（进 git）
  主控侧  <外置盘>/Backup/artifacts-index.jsonl       实收清单（收件口写的）
本工具按 sha256+bytes 对齐两边，输出「声明数 / 已备 / 未备」，并把结果写进
cph4/fleet/artifacts/COVERAGE.md 供主控简报与 CEO 查阅。

没有这一层，备份就只是"应该备了"——而 CEO 要的是可核验的磁盘事实。
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, "cph4", "fleet", "artifacts")
# 外置盘（移动硬盘）2026-11-11 已清空退出长期存储：未配置就明确报错，
# 不许指着一个不存在的盘把"没收到"当成"机队没产出"（那会把假红洗成结论）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault as _vault
EXT = os.environ.get("INTAKE_ROOT") or _vault.root()
INDEX = os.path.join(EXT, "Backup", "artifacts-index.jsonl")
OUT = os.path.join(ART, "COVERAGE.md")


def jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def human(n):
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return "%.1f %s" % (n, u)
        n /= 1024.0


def main():
    # 外置盘（移动硬盘）2026-11-11 已清空退出长期存储，冷备由 git 远端承担。
    # 没有外置盘还照跑，只会把 52 件声明全判"未备"——那是假红，比不跑更糟。
    # 判据：没有收件清单（INDEX）就没有"备了什么"的事实，缺它时算覆盖率＝凭空造红。
    if not os.path.exists(INDEX):
        print("收件清单不存在（%s）：外置盘/收件口已退役（2026-11-11 清空，冷备走 git 远端），"
              "没有清单就无法判定覆盖度，不生成 COVERAGE.md。" % INDEX)
        return 2
    if not EXT or not os.path.isdir(EXT):
        print("外置盘路径不存在（%s）：移动盘已于 2026-11-11 清空退出，冷备走 git 远端。"
              "在这种状态下算覆盖度只会把全部声明判未备＝假红，故不生成 COVERAGE.md。"
              % (EXT or "未配置"))
        return 2
    have = {}
    for r in jsonl(INDEX):
        key = (str(r.get("sha256") or "").lower(), int(r.get("bytes") or 0))
        if key[0]:
            have[key] = r

    nodes = sorted([d for d in os.listdir(ART)
                    if os.path.isdir(os.path.join(ART, d))]) if os.path.isdir(ART) else []
    rows, totals = [], {"declared": 0, "covered": 0, "bytes_declared": 0, "bytes_covered": 0}
    for n in nodes:
        man = jsonl(os.path.join(ART, n, "MANIFEST.jsonl"))
        cov = miss = 0
        bd = bc = 0
        missing = []
        for m in man:
            sha = str(m.get("sha256") or "").lower()
            size = int(m.get("bytes") or 0)
            bd += size
            totals["declared"] += 1
            totals["bytes_declared"] += size
            if sha and (sha, size) in have:
                cov += 1
                bc += size
                totals["covered"] += 1
                totals["bytes_covered"] += size
            else:
                miss += 1
                if len(missing) < 5:
                    missing.append(os.path.basename(str(m.get("path") or "?")))
        rows.append({"node": n, "declared": len(man), "covered": cov, "missing": miss,
                     "bytes": bd, "missing_sample": missing})

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    mounted = os.path.isdir(EXT)
    lines = ["# 产出备份覆盖度 %s" % ts, "",
             "- 外置盘：%s（%s）" % (EXT, "已挂载" if mounted else "**未挂载**"),
             "- 合计：声明 %d 件 / 已备 %d 件 / 未备 **%d** 件；%s → %s"
             % (totals["declared"], totals["covered"],
                totals["declared"] - totals["covered"],
                human(totals["bytes_declared"]), human(totals["bytes_covered"])), ""]
    if rows:
        lines += ["| 机器 | 声明 | 已备 | 未备 | 声明体量 | 未备样例 |", "|---|---|---|---|---|---|"]
        for r in rows:
            lines.append("| %s | %d | %d | %d | %s | %s |"
                         % (r["node"], r["declared"], r["covered"], r["missing"],
                            human(r["bytes"]), ", ".join(r["missing_sample"]) or "-"))
    else:
        lines.append("_还没有任何机器提交 MANIFEST.jsonl。_")
    text = "\n".join(lines) + "\n"
    os.makedirs(ART, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())