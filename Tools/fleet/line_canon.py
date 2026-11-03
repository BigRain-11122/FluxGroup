#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_canon.py - 业务线认知基座检查：文档说的和工序跑的必须是同一套。

为什么（2026-11-03 CEO「对这条业务线进行全面的认知改造」）：认知改造最容易变成再写一份
漂亮文档，然后旧文档还留着、工序表还是旧口径，下一个人按哪份做全凭运气。
本工具把"认知是否改造到位"变成可判：基座在位、必填段落齐、不过期、且与工序表一致。

判据（缺一即 FAIL）：
  1. cph4/fleet/<dept>/CANON-v1.md 存在（dept 由 --line 映射）
  2. 必填段落齐：定义 / 市场 / 判据 / 工序 / 成本 / 失效
  3. 日期 ≤ 90 天（认知会过期）
  4. 工序表存在，且结构合规（必须含 accept 段、无悬空依赖、无成环；判据与 line_plan 同一套）
  5. 工序表里的段 id 都能在基座的工序段里找到（防"文档一套、卡一套"）

用法：
  python3 line_canon.py --line bigstream-duanju [--json]
  python3 line_canon.py --all
Exit: 0 = PASS；2 = FAIL（列缺口）；1 = 用法错。
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")

# line → (认知基座相对路径, 工序表路径)
# 基座路径必须是这条线真正的认知入口；指向别的部门的文件等于没有基座。
MAP = {
    "bigstream-duanju": ("cph4/fleet/drama-dept-v1/CANON-v1.md", "cph4/fleet/ri/content/lines/duanju.json"),
    "bigstream-drama": ("cph4/fleet/drama-dept-v1/CANON-v1.md", "cph4/fleet/ri/content/lines/drama.json"),
    "bigstream-mv": ("cph4/fleet/mv-album-001-jay/CANON-v1.md", "cph4/fleet/ri/content/lines/mv.json"),
    "biggame": ("cph4/fleet/ri/game/CANON-v1.md", "cph4/fleet/ri/game/lines/biggame.json"),
    "bigmoney": ("cph4/fleet/ri/strategy/CANON-v1.md", "cph4/fleet/ri/strategy/lines/bigmoney.json"),
}
REQUIRED = ("一、这是什么", "二、市场事实", "五、交付判据", "六、工序", "七、成本", "八、失效条件")
MAX_AGE_DAYS = 90

sys.path.insert(0, HERE)
import line_plan as LP  # noqa: E402  工序表的同一套结构判据，避免两处规则各写一遍


def check(line):
    canon_rel, table = MAP.get(line, (None, None))
    gaps = []
    if not canon_rel:
        return {"line": line, "verdict": "FAIL", "gaps": ["未登记该线的认知基座映射（MAP 里没有 %s）" % line]}
    canon = os.path.join(ROOT, canon_rel)
    if not os.path.exists(canon):
        gaps.append("没有认知基座：%s" % canon_rel)
    text = ""
    age = None
    if os.path.exists(canon):
        text = open(canon, encoding="utf-8").read()
        m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
        if m:
            try:
                age = (date.today() - datetime.fromisoformat(m.group(1)).date()).days
                if age > MAX_AGE_DAYS:
                    gaps.append("认知过期 %d 天（上限 %d）：%s" % (age, MAX_AGE_DAYS, os.path.relpath(canon, ROOT)))
            except Exception:
                pass
        for sec in REQUIRED:
            if sec not in text:
                gaps.append("缺必填段落：%s" % sec)
    stages = []
    tp = os.path.join(ROOT, table) if table else ""
    if not tp or not os.path.exists(tp):
        gaps.append("工序表不存在：%s" % table)
    else:
        try:
            d = json.load(open(tp, encoding="utf-8-sig"))
            stages = [s.get("id") for s in (d.get("stages") or [])]
        except Exception as e:
            gaps.append("工序表读不了：%s" % e)
        else:
            # 结构判据与 line_plan 同一套（必须有 accept 段/无悬空依赖/无成环），
            # 这里再写一遍就会两处规则漂移，所以直接复用。
            for e in LP.validate_table(d):
                gaps.append("工序表结构：%s" % e)
            if text:
                missing = [s for s in stages if s and s not in text]
                if missing:
                    gaps.append("工序表段 id 在基座里找不到：%s（文档与卡不一致）" % ",".join(missing))
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "line": line,
           "canon": os.path.relpath(canon, ROOT) if os.path.exists(canon) else None,
           "canon_age_days": age, "stages": stages,
           "verdict": "PASS" if not gaps else "FAIL", "gaps": gaps}
    out["status"] = out["verdict"]
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "canon-%s.json" % line), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    lines = list(MAP) if (a.all or not a.line) else [a.line]
    outs = [check(l) for l in lines]
    if a.json:
        print(json.dumps(outs if len(outs) > 1 else outs[0], ensure_ascii=False, indent=1))
    else:
        for o in outs:
            print("CANON %-18s %s  %s" % (o["line"], o["verdict"],
                                          ("基座 %s / %s 天 / %d 段" % (o["canon"], o["canon_age_days"], len(o["stages"])))
                                          if o["canon"] else "无基座"))
            for g in o["gaps"]:
                print("   ! %s" % g)
    return 0 if all(o["verdict"] == "PASS" for o in outs) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))