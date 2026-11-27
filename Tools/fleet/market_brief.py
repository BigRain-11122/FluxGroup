#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""market_brief.py - 市场调研门：没有市场依据，不许开工生产。

为什么（2026-11-03 CEO「务必有质量验收和市场调研，不要产出垃圾」）：过去每条线都在
"凭感觉做"，做完才发现没人买。本工具不生产数据，只做两件事：
  1) 判定某条线的市场简报是否够用（五要素 + 新鲜度 + 有来源链接）；
  2) 生成可填的骨架，逼着填空而不是写着舒服就完事。

五要素（缺一即不合格，QUALITY-BAR 同一条规矩：不许用页数交差）：
   谁买 / 竞品≥3 / 价格带 / 我们的差异点 / 证据链接≥2
新鲜度：默认 30 天；过期即不合格（市场会变，旧结论当垃圾处理）。

用法：
  python3 market_brief.py check --line bigstream-duanju [--json]
  python3 market_brief.py scaffold --line bigstream-duanju   # 生成骨架，不编数据
Exit: 0 = 合格；2 = 不合格（列出缺什么）；1 = 用法错。
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
MKT = os.path.join(FLEET, "market")
STATE = os.path.join(FLEET, "state")
MAX_AGE_DAYS = 30

SECTIONS = ("谁买", "竞品", "价格带", "差异点", "证据")
LINES = ("bigstream-mv", "bigstream-duanju", "bigstream-drama", "biggame", "bigmoney")


def path_of(line):
    return os.path.join(MKT, "%s.md" % line)


def parse(text):
    """Return {section: body} for '## 谁买' style headings."""
    out = {}
    cur = None
    for ln in text.splitlines():
        m = re.match(r"^#{2,3}\s*(.+?)\s*$", ln)
        if m:
            cur = m.group(1).strip()
            out.setdefault(cur, [])
            continue
        if cur:
            out[cur].append(ln)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def bullets(body):
    return [l.strip() for l in (body or "").splitlines() if l.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "5."))]


def check(line):
    p = path_of(line)
    gaps, facts = [], {}
    if not os.path.exists(p):
        return {"line": line, "verdict": "FAIL", "gaps": ["没有市场简报文件：%s" % os.path.relpath(p, ROOT)],
                "file": None}
    text = open(p, encoding="utf-8").read()
    sec = parse(text)
    mdate = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    age = None
    if mdate:
        try:
            age = (date.today() - datetime.fromisoformat(mdate.group(1)).date()).days
        except Exception:
            age = None
    if age is None:
        gaps.append("没写日期（无法判断新鲜度）")
    elif age > MAX_AGE_DAYS:
        gaps.append("过期 %d 天（上限 %d）——市场变了，旧结论按垃圾处理" % (age, MAX_AGE_DAYS))
    for s in SECTIONS:
        body = sec.get(s)
        if body is None:
            gaps.append("缺要素：%s" % s)
            continue
        if s == "竞品" and len(bullets(body)) < 3:
            gaps.append("竞品不足 3 个（现在 %d）" % len(bullets(body)))
        if s == "证据":
            links = re.findall(r"https?://\S+", body)
            if len(links) < 2:
                gaps.append("证据链接不足 2 条（现在 %d）" % len(links))
            facts["links"] = len(links)
        if s in ("谁买", "价格带", "差异点") and len(body.strip()) < 8:
            gaps.append("%s 写得太空（<8 字）" % s)
    facts.update({"date": mdate.group(1) if mdate else None, "age_days": age,
                  "sections": sorted(sec)})
    return {"line": line, "verdict": "PASS" if not gaps else "FAIL", "gaps": gaps,
            "file": os.path.relpath(p, ROOT), "facts": facts}


SCAFFOLD = """# 市场简报 · {line}

- 日期：{today}
- 线：{line}
- 结论一句话：（这条线现在值不值得做，一句话）

## 谁买
（写清楚：具体是谁、在哪个平台、为什么现在会买；不要写"年轻人"这种空话）

## 竞品
- （竞品1：名字 / 平台 / 数据或评价 / 链接）
- （竞品2：…）
- （竞品3：…）

## 价格带
（写实际见到的价格与档位，不要拍脑袋；说明我们落在哪一档）

## 差异点
（我们凭什么被选中：一句能被验证的话，不写"更好更便宜"）

## 证据
- 来源1：（链接 + 抓取日期）
- 来源2：（链接 + 抓取日期）

## 对我们的要求（写进入工序的硬约束）
- （例：单集≤90秒 / 首3秒必须有钩子 / 上架价位 X）
"""


def scaffold(line):
    os.makedirs(MKT, exist_ok=True)
    p = path_of(line)
    if os.path.exists(p):
        print("已存在，不覆盖：%s" % os.path.relpath(p, ROOT))
        return 0
    with open(p, "w", encoding="utf-8") as f:
        f.write(SCAFFOLD.format(line=line, today=date.today().isoformat()))
    print("已生成骨架（需要人/调研席填真数据，工具不编）：%s" % os.path.relpath(p, ROOT))
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(rest)
    if cmd == "scaffold":
        return scaffold(a.line)
    if a.all or not a.line:
        outs = [check(l) for l in LINES]
        bad = [o for o in outs if o["verdict"] != "PASS"]
        for o in outs:
            print("MARKET %-18s %s" % (o["line"], o["verdict"]))
            for g in o["gaps"][:3]:
                print("   ! %s" % g)
        return 0 if not bad else 2
    out = check(a.line)
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "market-%s.json" % a.line), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("MARKET %-18s %s" % (a.line, out["verdict"]))
        for g in out["gaps"]:
            print("   ! %s" % g)
    return 0 if out["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))