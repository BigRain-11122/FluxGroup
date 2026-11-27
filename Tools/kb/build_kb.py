#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_kb.py — 生成 AI 可读的集团资料库（AI-KB/）。

为什么（CEO 2026-11-08 原话）：「建立一个我现在开发的资料库，要 ai 能快速识别的，
让他们完全能理解我要做什么，业务方向，实现方式，进度，产量，skill 库等等全部，
专门开一个文件夹，分类写好，要颗粒度非常细，用本地的大模型去写」。

三条设计铁律：
  1. 事实由规则抽取（90-machine/facts.json），模型只写叙述——数字不交 4B，
     模型返回空就用模板回落，绝不编造。
  2. 每篇文档带机读 front-matter（id/title/layer/questions/facts/generated_at），
     外加 INDEX.json，AI 先读索引再按需下钻，不必全文检索。
  3. 可重生成：再次运行即刷新，不手改产物；`--check` 校验每篇是否合规、事实是否过期。

用法：
  python Tools/kb/build_kb.py            # 全量生成（调用本地模型写叙述）
  python Tools/kb/build_kb.py --no-llm   # 只出事实与模板（不调模型，秒级）
  python Tools/kb/build_kb.py --only lines
  python Tools/kb/build_kb.py --check    # 校验产物是否齐全/新鲜
Exit: 0 成功；1 有文档缺失或事实过期；2 输入缺失（队列/注册表不在）
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
KB = os.path.join(ROOT, "AI-KB")
STATE = os.path.join(FLEET, "state")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


# ------------------------------------------------------------------ 事实抽取
def _json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _lines(path):
    out = []
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _first_doc_line(path, limit=240):
    """取 .py 模块 docstring 的第一句（工具的一句话职责）。"""
    try:
        src = open(path, encoding="utf-8", errors="replace").read(6000)
    except Exception:
        return ""
    m = re.match(r'# -\*-.*?-\*-\s*\n?"""(.*?)"""', src, re.S) or re.match(r'"""(.{10,}?)"""', src, re.S)
    body = (m.group(1) if m else "").strip()
    body = re.sub(r"\s+", " ", body)
    return body[:limit]


def facts_lines():
    reg = _json(os.path.join(FLEET, "LINE-REGISTRY.json"), {}) or {}
    st = _json(os.path.join(STATE, "lines.json"), {}) or {}
    observed = {l.get("id"): l for l in (st.get("lines") or [])}
    q = _lines(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    by_line = {}
    for r in q:
        lid = r.get("line") or "unfiled"
        d = by_line.setdefault(lid, {"total": 0, "by_state": {}, "last_done": ""})
        d["total"] += 1
        s = r.get("state") or "NONE"
        d["by_state"][s] = d["by_state"].get(s, 0) + 1
        if s == "DONE":
            ts = str(r.get("finished_at") or r.get("closed_at") or "")
            if ts > d["last_done"]:
                d["last_done"] = ts
    out = []
    for l in (reg.get("lines") or []):
        lid = l.get("id")
        ob = observed.get(lid) or {}
        out.append({
            "id": lid, "name": l.get("name") or lid, "priority": l.get("priority"),
            "org": l.get("org"), "status": l.get("status"), "owner": l.get("owner"),
            "stale_after_h": l.get("stale_after_h"),
            "stages": [{"id": s.get("id"), "name": s.get("name"), "owner": s.get("owner"),
                        "model": s.get("model"), "lane": s.get("lane"),
                        "evidence": (s.get("evidence") or [])[:2]}
                       for s in (l.get("stages") or [])],
            "repos": l.get("repos") or [],
            "observed": ob.get("observed"), "age_h": ob.get("age_h"),
            "newest": ob.get("newest"),
            "queue": by_line.get(lid, {"total": 0, "by_state": {}, "last_done": ""}),
        })
    return out


def facts_fleet():
    cfg = _json(os.path.join(ROOT, "Tools", "fleet-nodes.json"), [])
    nodes = []
    for n in (cfg if isinstance(cfg, list) else (cfg.get("nodes") or [])):
        name = n.get("id") or n.get("name")
        lane = _json(os.path.join(FLEET, "lanes", "%s.json" % name), {}) or {}
        nodes.append({"id": name, "host": n.get("host"),
                      "lanes": lane.get("jobs") and len(lane.get("jobs") or []) or 0,
                      "lane_ts": lane.get("ts"), "idle_reason": lane.get("idle_reason")})
    conf = _json(os.path.join(FLEET, "AUTONOMY-CONFIG.json"), {}) or {}
    pulse = _json(os.path.join(FLEET, "dispatcher", "PULSE.json"), {}) or {}
    return {"nodes": nodes,
            "slots": ((conf.get("supply") or {}).get("slots_per_node") or {}),
            "pulse_ts": pulse.get("ts"), "pulse_sec": pulse.get("sec"),
            "pulse_stages": len(pulse.get("stages") or {})}


def facts_queue():
    q = _lines(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    by_state, by_line, by_day = {}, {}, {}
    for r in q:
        s = r.get("state") or "NONE"
        by_state[s] = by_state.get(s, 0) + 1
        lid = r.get("line") or "unfiled"
        by_line[lid] = by_line.get(lid, 0) + 1
        day = str(r.get("created_at") or "")[:10]
        if day:
            by_day[day] = by_day.get(day, 0) + 1
    open_cards = [{"id": r.get("id"), "cmd": (r.get("cmd") or "")[:120],
                   "deliverable": r.get("deliverable"), "line": r.get("line")}
                  for r in q if r.get("state") in ("OPEN", "RUNNING")][:40]
    return {"total": len(q), "by_state": by_state, "by_line": by_line,
            "by_day": dict(sorted(by_day.items())[-14:]), "live_cards": open_cards}


def facts_skills():
    """技能库：全局 ~/.codely-cli/skills 与集团 cph4/skills 两处，读 SKILL.md 头。"""
    out = []
    for base, scope in ((os.path.expanduser("~/.codely-cli/skills"), "global"),
                        (os.path.join(ROOT, "cph4", "skills"), "group")):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name, "SKILL.md")
            if not os.path.isfile(p):
                continue
            try:
                head = open(p, encoding="utf-8", errors="replace").read(3000)
            except Exception:
                continue
            m = re.search(r"^description:\s*(.+?)(?:\n[a-z_]+:|\n---)", head, re.S | re.M)
            desc = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
            trig = re.search(r"^description:.*?\n(?:.*?)?$", head, re.S)
            if not desc:
                m2 = re.search(r"^#\s+(.+)$", head, re.M)
                desc = (m2.group(1) if m2 else "")[:200]
            out.append({"name": name, "scope": scope, "path": os.path.relpath(p, ROOT)
                        if scope == "group" else p.replace(os.path.expanduser("~"), "~"),
                        "description": desc[:400]})
    return out


def facts_tools():
    tool_dir = os.path.join(ROOT, "Tools")
    fleet_dir = os.path.join(tool_dir, "fleet")
    items = []
    for d, tag in ((fleet_dir, "fleet"), (tool_dir, "root")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".py"):
                continue
            p = os.path.join(d, f)
            items.append({"file": os.path.relpath(p, ROOT), "scope": tag,
                          "one_line": _first_doc_line(p, 160)})
    return items


def facts_outputs():
    """产量：按目录数真实产物（只数本机盘上有的文件，不猜远端）。"""
    roots = {"media": os.path.join(ROOT, "media"),
             "archive": os.path.join(FLEET, "archive"),
             "gaming": os.path.join(ROOT, "gaming"),
             "quant": os.path.join(ROOT, "quant"),
             "软著申请材料": os.path.join(ROOT, "软著申请材料")}
    out = {}
    for k, base in roots.items():
        n, ext, newest, newest_name = 0, {}, "", ""
        if not os.path.isdir(base):
            out[k] = {"exists": False}
            continue
        for dp, _dn, fn in os.walk(base):
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    mt = os.path.getmtime(p)
                except OSError:
                    continue
                n += 1
                e = os.path.splitext(f)[1].lower() or "(none)"
                ext[e] = ext.get(e, 0) + 1
                if mt > (os.path.getmtime(newest) if newest else 0):
                    newest, newest_name = p, os.path.relpath(p, ROOT)
        out[k] = {"exists": True, "files": n,
                  "by_ext": dict(sorted(ext.items(), key=lambda kv: -kv[1])[:8]),
                  "newest": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(
                      os.path.getmtime(newest))) if newest else "",
                  "newest_file": newest_name}
    return out


def facts_progress():
    st = _json(os.path.join(STATE, "lines.json"), {}) or {}
    inv = _json(os.path.join(STATE, "invariants.json"), {}) or {}
    fork = _json(os.path.join(FLEET, "FORK-STATUS.json"), {}) or {}
    return {"lines_summary": st.get("summary") or {},
            "declared_active_no_disk": [l for l in (st.get("lines") or [])
                                        if l.get("declared") == "ACTIVE"
                                        and l.get("observed") != "OBSERVED"],
            "invariants": inv if isinstance(inv, dict) else {},
            "fork_status": fork}


def collect():
    if not os.path.isdir(FLEET):
        print("[kb] E-INPUT: cph4/fleet 不存在")
        sys.exit(2)
    f = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "repo_root": ROOT,
         "lines": facts_lines(),
         "fleet": facts_fleet(),
         "queue": facts_queue(),
         "skills": facts_skills(),
         "tools": facts_tools(),
         "outputs": facts_outputs(),
         "progress": facts_progress()}
    return f


# ------------------------------------------------------------------ 本地模型
def llm(prompt, cls="big", timeout=120):
    try:
        import local_model as lm
        return (lm.generate(prompt, cls=cls, timeout=timeout) or "").strip()
    except Exception:
        return ""


GROUND = ("你只能使用下面「事实」里出现的内容写文档。没出现的数字、时间、人名、结论一律不许写；"
          "缺什么就写「未测/未知」。不要寒暄、不要总结自己的写作过程、不要用表格堆砌。"
          "输出中文 Markdown，结构照给定的骨架，每节 2-5 句，句子短。")


def doc_body(facts_slice, skeleton, cls="big", must=None):
    """模型写；空、编数字、或漏掉必提事实 → 回落模板。宁可平实，不许失实。"""
    hard = ""
    if must:
        hard = ("\n\n正文里必须原样出现这些字符串（漏一个就算不合格）："
                + "、".join("「%s」" % m for m in must if m))
    prompt = "%s%s\n\n骨架：\n%s\n\n事实（JSON）：\n%s" % (
        GROUND, hard, skeleton, json.dumps(facts_slice, ensure_ascii=False)[:6000])
    text = llm(prompt, cls=cls)
    if text and len(text) > 40:
        raw = json.dumps(facts_slice, ensure_ascii=False)
        if re.search(r"[一二三四五六七八九十百千万零两]{2,}", text):
            return None, "template(reject-cn-num)"
        nums = set(re.findall(r"\d+(?:\.\d+)?", text))
        bogus = [n for n in nums if n not in raw and n not in ("1", "2", "3", "0")]
        if bogus:
            return None, "template(reject-num:%s)" % ",".join(bogus[:3])
        miss = [t for t in (must or []) if str(t) and str(t) not in text]
        if miss:
            return None, "template(reject-miss:%s)" % "、".join(miss[:3])
        return text, "local-llm"
    return None, "template"


def fmt(v, empty="未测"):
    if v is None or v == "" or v == [] or v == {}:
        return empty
    if isinstance(v, (list, tuple)):
        return "、".join(str(x) for x in v) if v else empty
    if isinstance(v, dict):
        return "，".join("%s=%s" % (k, v[k]) for k in list(v)[:8])
    return str(v)


def template_lines(ln):
    stages = ln.get("stages") or []
    st_txt = "；".join("%s（%s，%s）" % (s.get("name"), fmt(s.get("owner")), fmt(s.get("model")))
                       for s in stages) or "未登记工序"
    q = ln.get("queue") or {}
    return "\n".join([
        "## 一句话", "%s：%s，优先级 %s，归属 %s。" % (
            ln["name"], fmt(ln.get("status")), fmt(ln.get("priority")), fmt(ln.get("org"))),
        "## 谁负责 / 怎么判", "负责人：%s；判新鲜度阈值：%s 小时。" % (
            fmt(ln.get("owner")), fmt(ln.get("stale_after_h"))),
        "## 工序与用哪台机", st_txt + "。",
        "## 现在的产出", "盘上最近产物时间 %s（距今 %s 小时，状态 %s）；队列累计 %s 张，其中完成 %s 张。" % (
            fmt(ln.get("newest")), fmt(ln.get("age_h")), fmt(ln.get("observed")),
            fmt(q.get("total")), fmt((q.get("by_state") or {}).get("DONE"))),
        "## 怎么验证", "看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。",
        "## 下一步", "该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。",
        "## 我不知道的", "本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。",
    ])


def one_liner(facts_slice, must=None, cls="big"):
    """让本地模型只写一句概述：短、必须含给定事实词、不许出现事实里没有的数字。

    为什么不全篇交给模型：4B 会把"总数"说成"待处理"、用中文数字绕过数字闸，
    准确度反而低于模板。事实骨架留在模板里，模型只负责把它说人话。
    """
    obj = json.dumps(facts_slice, ensure_ascii=False)[:1500]
    prompt = ("用一句中文（不超过 45 字）概括下面这条业务事实，必须原样包含：%s。"
              "只输出这一句，不要标题、不要解释。事实：%s"
              % ("、".join(must or []), obj))
    text = llm(prompt, cls=cls, timeout=60)
    text = (text or "").strip().strip('"').split("\n")[0].strip()
    if not text or len(text) > 90:
        return None
    if re.search(r"[一二三四五六七八九十百千万零两]{2,}", text):
        return None
    raw = json.dumps(facts_slice, ensure_ascii=False)
    if [n for n in re.findall(r"\d+(?:\.\d+)?", text) if n not in raw and n not in ("1", "2", "3", "0")]:
        return None
    if [m for m in (must or []) if m and m not in text]:
        return None
    return text


SKEL_LINE = """## 一句话
## 谁负责 / 怎么判
## 工序与用哪台机
## 现在的产出
## 怎么验证
## 下一步
## 我不知道的"""

SKEL_ENG = """## 一句话
## 结构（有哪些层/进程/目录）
## 数据怎么流
## 关键约定（不许违反的）
## 怎么验证它在工作
## 我不知道的"""


def write_doc(path, meta, body, model="template"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 「我不知道的」是硬要求：写不出边界=在装懂。模型漏了就在这里补齐，不让它混过去。
    if "我不知道的" not in body:
        body = body.rstrip() + ("\n## 我不知道的\n本页只覆盖仓库里可核验的事实；"
                                "各机运行时状态、商业数据与对外承诺不在本页。")
    fm = ["---",
          "id: %s" % meta["id"],
          "title: %s" % meta["title"],
          "layer: %s" % meta["layer"],
          "questions: %s" % json.dumps(meta["questions"], ensure_ascii=False),
          "facts: %s" % json.dumps(meta["facts"], ensure_ascii=False),
          "generated_at: %s" % meta["generated_at"],
          "generator: Tools/kb/build_kb.py",
          "written_by: %s" % model,
          "---", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(fm) + body.strip() + "\n")
    meta["path"] = os.path.relpath(path, ROOT)
    meta["written_by"] = model
    return meta


# ------------------------------------------------------------------ 文档计划
def build(only=None, use_llm=True):
    F = collect()
    os.makedirs(KB, exist_ok=True)
    os.makedirs(os.path.join(KB, "90-machine"), exist_ok=True)
    with open(os.path.join(KB, "90-machine", "facts.json"), "w", encoding="utf-8") as f:
        json.dump(F, f, ensure_ascii=False, indent=1)
    now = F["generated_at"]
    metas = []

    def want(name):
        return (not only) or only == name

    # ---- 00 identity
    if want("identity"):
        facts = {"repo": ROOT,
                 "top_dirs": sorted([d for d in os.listdir(ROOT)
                                     if os.path.isdir(os.path.join(ROOT, d))
                                     and not d.startswith(".")]),
                 "lines_count": len(F["lines"]),
                 "lines": [{"id": l["id"], "name": l["name"], "prio": l["priority"],
                            "org": l["org"], "status": l["status"]} for l in F["lines"]],
                 "queue": F["queue"]["by_state"],
                 "fleet": [n["id"] for n in F["fleet"]["nodes"]]}
        body, how = doc_body(facts, """## 这是什么组织
## 现在同时在做的业务（按优先级）
## 谁做决定、谁执行
## 三条最容易被误解的地方
## 怎么快速判断一条业务是真的在做还是在纸面上
## 我不知道的""", must=[str(len(F["lines"]))] + [n["id"] for n in F["fleet"]["nodes"]]) if use_llm else (None, "template")
        if not body:
            body = "\n".join([
                "## 这是什么组织",
                "一个由 CEO 定方向、AI 机队执行的内容与游戏集团，仓库根目录 `%s`。" % ROOT,
                "## 现在同时在做的业务（按优先级）",
                "共 %d 条业务线：%s。" % (len(F["lines"]), "；".join(
                    "%s(%s/%s)" % (l["name"], l["priority"], l["status"]) for l in F["lines"])),
                "## 谁做决定、谁执行",
                "CEO 只做方向、红线、花钱三类决定；其余由主控与各线自决推进。执行落在机队"
                "（%s）与各业务目录。" % "、".join(n["id"] for n in F["fleet"]["nodes"]),
                "## 三条最容易被误解的地方",
                "1) 「卡完成」不等于产物在盘；2) 主控不做生产，只出卡/裁决/告警/一屏；"
                "3) 远端机器上的产物主控看不到，不能判成缺失。",
                "## 怎么快速判断一条业务是真的在做还是在纸面上",
                "看该线最新产物 mtime + 队列里是否有在飞卡 + 回执是否带 rc 与字节数，三者同时更新才算真做。",
                "## 我不知道的",
                "各线商业目标与实际营收不在本仓，未测。"])
            how = "template"
        metas.append(write_doc(os.path.join(KB, "00-identity", "01-who-we-are.md"),
                               {"id": "identity.who", "title": "集团与业务总览",
                                "layer": "identity", "questions": ["这家在做什么", "有几条线", "谁决策"],
                                "facts": ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"],
                                "generated_at": now}, body, how))

        facts2 = {"progress": F["progress"], "queue": F["queue"]["by_state"]}
        body2, how2 = doc_body(facts2, """## 铁律（违反即返工）
## 决策边界
## 不许做的事
## 汇报形式要求""") if use_llm else (None, "template")
        if not body2:
            body2 = "\n".join([
                "## 铁律（违反即返工）",
                "产物必须落盘（文件 + mtime + 字节），回执/心跳/自述不算产物；假绿比空转更糟；"
                "不许拿 swap 当内存假装在跑。",
                "## 决策边界",
                "CEO：方向变更、新方向署名、红线裁决、资源调配。其余默认自动放行，"
                "闸只保留「不可逆 / 对外发布 / 花钱超限」三类。",
                "## 不许做的事",
                "主控不写生产链、不出图不渲染、不代签代发；对外账号与发言权在 CEO；不碰解密他人包体。",
                "## 汇报形式要求",
                "编号列表、短句、可扫读；先结论后证据；每个数字要能指到文件。",
                "## 我不知道的",
                "本页是可机检的红线摘要，全文以 docs/governance.md 与 docs/orders.md 为准。"])
            how2 = "template"
        metas.append(write_doc(os.path.join(KB, "00-identity", "02-redlines.md"),
                               {"id": "identity.redlines", "title": "红线与治理摘要",
                                "layer": "identity",
                                "questions": ["什么不能做", "谁能拍板", "怎么汇报"],
                                "facts": ["docs/governance.md", "docs/orders.md", "CODELY.md"],
                                "generated_at": now}, body2, how2))

    # ---- 10 business: 每条线一页
    if want("lines"):
        for ln in F["lines"]:
            facts = dict(ln)
            # 必提事实只放"短、可原样复述"的字段；带括号/长句的所有者名不好复述，
            # 会把它变成"永远不合格"的假闸（实测 12/15 被误杀）。
            # 全篇交给 4B 会失真（实测把"总数"写成"待处理"、用中文数字绕过数字闸），
            # 所以事实骨架固定用模板，只让模型写那句概述。
            body, how = (None, "template")
            if not body:
                body, how = template_lines(ln), "template"
                one = one_liner({k: ln[k] for k in ("name", "priority", "status", "observed",
                                                    "age_h", "newest")} ,
                                must=[ln["name"], fmt(ln.get("priority"))])
                if one:
                    body = body.replace("## 一句话\n%s：%s，优先级 %s，归属 %s。" % (
                        ln["name"], fmt(ln.get("status")), fmt(ln.get("priority")),
                        fmt(ln.get("org"))), "## 一句话\n" + one, 1)
                    how = "template+local-llm"
            metas.append(write_doc(
                os.path.join(KB, "10-business", "%s.md" % ln["id"]),
                {"id": "line.%s" % ln["id"], "title": ln["name"], "layer": "business",
                 "questions": ["这条线做什么", "谁负责", "做到哪了", "怎么验证"],
                 "facts": ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"],
                 "generated_at": now}, body, how))

        rows = []
        for ln in F["lines"]:
            q = ln.get("queue") or {}
            rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                ln["id"], ln["name"], fmt(ln["priority"]), fmt(ln["status"]),
                fmt(ln.get("age_h")), fmt((q.get("by_state") or {}).get("DONE")),
                fmt((q.get("by_state") or {}).get("OPEN"))))
        body = ("## 一句话\n%d 条业务线，按 P0 内容 / P1 战略 / P2 城市 / P3 平台分组。\n\n"
                "## 全景表\n| 线 | 名称 | 优先级 | 声明 | 产物年龄(h) | DONE | OPEN |\n|---|---|---|---|---|---|---|\n%s\n\n"
                "## 怎么读这张表\n产物年龄超过该线阈值或声明 ACTIVE 但 observed 不是 OBSERVED，"
                "就是「纸面在做」，要去看卡和输入。\n\n## 我不知道的\n远端产物本机不可见，按远端待查处理。"
                % (len(F["lines"]), "\n".join(rows)))
        metas.append(write_doc(os.path.join(KB, "10-business", "_portfolio.md"),
                               {"id": "business.portfolio", "title": "业务组合总表",
                                "layer": "business",
                                "questions": ["一共有哪些线", "哪条快断了"],
                                "facts": ["LINE-REGISTRY.json", "state/lines.json"],
                                "generated_at": now}, body, "template"))

    # ---- 20 engineering
    if want("engineering"):
        facts = {"tools_fleet": len([t for t in F["tools"] if t["scope"] == "fleet"]),
                 "tools_root": len([t for t in F["tools"] if t["scope"] == "root"]),
                 "top_dirs": sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))]),
                 "fleet": F["fleet"], "lines": [{"id": l["id"], "stages": len(l["stages"])} for l in F["lines"]]}
        body, how = (doc_body(facts, SKEL_ENG,
                                  must=[str(F["fleet"]["pulse_stages"])] +
                                       [n["id"] for n in F["fleet"]["nodes"]][:3])
                          if use_llm else (None, "template"))
        if not body:
            body = "\n".join([
                "## 一句话", "一个大仓 + 多台 Windows 生产机；主控（bm-m）只调度，生产和产物在各机与各业务目录。",
                "## 结构（有哪些层/进程/目录）",
                "控制面：`Tools/fleet/`（%d 个脚本，主控脉 master_pulse 串起 %d 个阶段）；"
                "生产面：`media/`、`gaming/`、`quant/`、`cph4/fleet/archive/`；"
                "契约面：`cph4/fleet/*.json`（线注册表、自主配置、卡策略、模型矩阵）。"
                % (facts["tools_fleet"], facts["fleet"]["pulse_stages"]),
                "## 数据怎么流",
                "夜计划/巡逻生成卡 → 队列 PRODUCTION-QUEUE.jsonl → 派单写 lanes/<node>.json → "
                "机器取卡执行 → 回执 queue-receipts/ → closer 判 rc 与产物 → 主控出屏。",
                "## 关键约定（不许违反的）",
                "一行一卡；状态只认 OPEN/RUNNING/DONE/FAILED/BLOCKED/CANCELLED/ARCHIVED；"
                "同一命令同一刻只派一张；归档是终态；阈值只能来自 cph4/fleet 下的 JSON。",
                "## 怎么验证它在工作",
                "PULSE.json 的 ts 在推进 + lanes/*.json 有新 job + queue-receipts 新回执三者同时成立。",
                "## 我不知道的", "各机上自装的运行时（ComfyUI/IndexTTS/团结引擎）版本未测。"])
            how = "template"
        metas.append(write_doc(os.path.join(KB, "20-engineering", "01-architecture.md"),
                               {"id": "eng.architecture", "title": "系统架构与数据流",
                                "layer": "engineering",
                                "questions": ["系统由什么组成", "数据怎么流", "关键约定"],
                                "facts": ["Tools/fleet/master_pulse.py", "Tools/fleet-nodes.json",
                                          "cph4/fleet/AUTONOMY-CONFIG.json"],
                                "generated_at": now}, body, how))

        rows = ["| 工具 | 职责 |", "|---|---|"]
        for t in F["tools"]:
            if t["scope"] == "fleet" and t["one_line"]:
                rows.append("| `%s` | %s |" % (t["file"], t["one_line"]))
        body = ("## 一句话\n主控与机队全部自动化脚本目录：`Tools/fleet/`（%d 个），根 `Tools/`（%d 个）。\n\n"
                "## 工具清单（按文件名字典序，职责取自模块首行）\n%s\n\n"
                "## 怎么用这份清单\n先按职责关键词找工具，再用 `--help` 看参数；"
                "工具缺输入时应当 rc=3 而不是伪造产物。\n\n## 我不知道的\n各工具在远端机器上的实际版本可能落后于本仓。"
                % (len([t for t in F["tools"] if t["scope"] == "fleet"]),
                   len([t for t in F["tools"] if t["scope"] == "root"]), "\n".join(rows)))
        metas.append(write_doc(os.path.join(KB, "20-engineering", "02-tool-catalog.md"),
                               {"id": "eng.tools", "title": "工具目录（职责速查）",
                                "layer": "engineering",
                                "questions": ["做某件事该用哪个脚本", "有哪些自动化"],
                                "facts": ["Tools/**/*.py"],
                                "generated_at": now}, body, "template"))

        out_rows = []
        for k, v in F["outputs"].items():
            if not v.get("exists"):
                out_rows.append("| %s | 不存在 | - | - |" % k)
                continue
            out_rows.append("| %s | %s | %s | %s |" % (
                k, v.get("files"), fmt(v.get("by_ext")), v.get("newest")))
        body = ("## 一句话\n本机盘上真实产物按目录统计（只数本机，远端不算）。\n\n"
                "## 产量表\n| 目录 | 文件数 | 类型分布 | 最新 mtime |\n|---|---|---|---|\n%s\n\n"
                "## 怎么读\n文件数是存量，最新 mtime 才是产量；mtime 不动 = 这条线没在产。\n\n"
                "## 我不知道的\n媒体成品多数在 bm-a/bm-c 的本地盘，本仓只能看到同步回来的部分。"
                % "\n".join(out_rows))
        metas.append(write_doc(os.path.join(KB, "20-engineering", "03-output-inventory.md"),
                               {"id": "eng.outputs", "title": "本机产物清单",
                                "layer": "engineering",
                                "questions": ["现在有多少产物", "最新是什么时候"],
                                "facts": ["media/", "cph4/fleet/archive/", "gaming/", "quant/"],
                                "generated_at": now}, body, "template"))

    # ---- 30 operations
    if want("ops"):
        facts = {"fleet": F["fleet"], "queue": F["queue"]["by_state"]}
        body, how = (doc_body(facts, SKEL_ENG,
                                  must=[str(F["fleet"]["pulse_stages"])] +
                                       [n["id"] for n in F["fleet"]["nodes"]][:3])
                          if use_llm else (None, "template"))
        if not body:
            nodes = F["fleet"]["nodes"]
            body = "\n".join([
                "## 一句话", "机队由 %d 台机器组成，主控只发卡与裁决，机器各自取卡执行。" % len(nodes),
                "## 结构（有哪些层/进程/目录）",
                "；".join("%s（车道文件 %s，在飞 %s）" % (n["id"], fmt(n.get("lane_ts")),
                                                    fmt(n.get("lanes"))) for n in nodes) + "。",
                "## 数据怎么流", "主控写 lanes/<node>.json → 机器读并执行 → 回执进 queue-receipts → 主控判 rc 与产物。",
                "## 关键约定（不许违反的）",
                "主控不做生产；一台机可有多个槽位（配置 supply.slots_per_node）；"
                "节点仓库分叉时 poke(/poke 只做 pull --ff-only) 会假受理，必须先在机器上收口。",
                "## 怎么验证它在工作",
                "该机最近回执时间 + 车道文件 ts + 心跳三信号；只有心跳没有回执 = 在网上但没干活。",
                "## 我不知道的", "各机 FleetLink 端口是否在监听需逐台探活（本机实测过 /health）。"])
            how = "template"
        metas.append(write_doc(os.path.join(KB, "30-operations", "01-fleet.md"),
                               {"id": "ops.fleet", "title": "机队与跨机执行",
                                "layer": "operations",
                                "questions": ["有几台机器", "怎么给机器派活", "怎么判断机器真在干活"],
                                "facts": ["Tools/fleet-nodes.json", "cph4/fleet/lanes/",
                                          "cph4/fleet/queue-receipts/"],
                                "generated_at": now}, body, how))

        body = ("## 一句话\n主控脉是唯一的常驻身体：按节奏跑 %d 个阶段，出卡、派单、验收、出屏。\n\n"
                "## 结构（有哪些层/进程/目录）\nmaster_pulse（launchd 常驻）→ 各阶段脚本 → "
                "state/ 下的机读状态 + 根目录的一屏 markdown。\n\n"
                "## 数据怎么流\n节奏表（cadence）定周期 → 阶段执行 → 写 PULSE.json/stage-last.json "
                "→ 看板与 CEO-NEXT 汇总。\n\n"
                "## 关键约定（不许违反的）\n"
                "阶段必须留下「最后一次真跑」记录；同一工具不得被两个阶段重复登记；"
                "阈值只在 cph4/fleet/*.json 里改。\n\n"
                "## 怎么验证它在工作\n"
                "`PULSE.json.ts` 在推进，且 `state/stage-last.json` 里各阶段时间在更新；"
                "launchctl 的 PID 不可信。\n\n## 我不知道的\n慢批阶段单轮耗时会超过标称节拍。" %
                F["fleet"]["pulse_stages"])
        metas.append(write_doc(os.path.join(KB, "30-operations", "02-automation-loop.md"),
                               {"id": "ops.loop", "title": "主控脉与节奏",
                                "layer": "operations",
                                "questions": ["自动化怎么跑起来", "怎么判断脉健康"],
                                "facts": ["Tools/fleet/master_pulse.py", "cph4/fleet/dispatcher/PULSE.json",
                                          "cph4/fleet/state/stage-last.json"],
                                "generated_at": now}, body, "template"))

        body = ("## 一句话\n卡是唯一的工作单元；队列是唯一权威，回执是唯一验收凭据。\n\n"
                "## 结构（有哪些层/进程/目录）\n"
                "`PRODUCTION-QUEUE.jsonl`（一行一卡）→ `lanes/<node>.json`（派单）→ "
                "`queue-receipts/`（回执）→ 状态机。\n\n"
                "## 数据怎么流\n"
                "OPEN → RUNNING（owner + lease）→ DONE/FAILED/BLOCKED；CANCELLED 与 ARCHIVED 是终态，"
                "只有显式 requeued_by 能重开。\n\n"
                "## 关键约定（不许违反的）\n"
                "交付物必须与 cmd 真实产出路径一致；同一命令同一刻只派一张；坏卡要归档不要反复重试。\n\n"
                "## 怎么验证它在工作\n近期状态分布与在飞卡：%s。\n\n## 我不知道的\n历史卡里仍有个别空壳。" %
                fmt(F["queue"]["by_state"]))
        metas.append(write_doc(os.path.join(KB, "30-operations", "03-queue-and-cards.md"),
                               {"id": "ops.queue", "title": "队列、卡与状态机",
                                "layer": "operations",
                                "questions": ["一张卡长什么样", "状态怎么流转", "怎么验收"],
                                "facts": ["cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/CARD-POLICY-v1.json"],
                                "generated_at": now}, body, "template"))

    # ---- 40 progress
    if want("progress"):
        rows = ["| 线 | 声明 | 观测 | 产物年龄(h) | DONE | 总卡 |", "|---|---|---|---|---|---|"]
        for ln in F["lines"]:
            q = ln.get("queue") or {}
            rows.append("| %s | %s | %s | %s | %s | %s |" % (
                ln["name"], fmt(ln.get("status")), fmt(ln.get("observed")),
                fmt(ln.get("age_h")), fmt((q.get("by_state") or {}).get("DONE")),
                fmt(q.get("total"))))
        body = ("## 一句话\n当前进度以磁盘事实为准：队列 %s 张，状态分布 %s。\n\n"
                "## 全景\n%s\n\n"
                "## 判断规则\n声明 ACTIVE 但盘上无产物 = 纸面；产物年龄超阈值 = 停摆；"
                "有卡在飞且回执新鲜 = 真在推进。\n\n"
                "## 我不知道的\n远端产物未回传时无法判定。" % (
                    F["queue"]["total"], fmt(F["queue"]["by_state"]), "\n".join(rows)))
        metas.append(write_doc(os.path.join(KB, "40-progress", "01-snapshot.md"),
                               {"id": "progress.snapshot", "title": "进度快照（事实）",
                                "layer": "progress",
                                "questions": ["现在做到哪", "哪条停了"],
                                "facts": ["state/lines.json", "PRODUCTION-QUEUE.jsonl"],
                                "generated_at": now}, body, "template"))

        live = F["queue"]["live_cards"]
        rows = ["| 卡 | 交付物 | 线 |", "|---|---|---|"]
        for c in live:
            rows.append("| `%s` | %s | %s |" % (c["id"], fmt(c["deliverable"]), fmt(c["line"])))
        body = ("## 一句话\n在飞卡 %d 张（OPEN+RUNNING 前 40 条）。\n\n## 在飞清单\n%s\n\n"
                "## 我不知道的\n卡在机器上真正跑到哪一步，只能靠回执与产物判断。" % (len(live), "\n".join(rows)))
        metas.append(write_doc(os.path.join(KB, "40-progress", "02-in-flight.md"),
                               {"id": "progress.inflight", "title": "在飞工作清单",
                                "layer": "progress",
                                "questions": ["现在有哪些活在做"],
                                "facts": ["PRODUCTION-QUEUE.jsonl"],
                                "generated_at": now}, body, "template"))

        gaps = F["progress"].get("declared_active_no_disk") or []
        rows = ["- %s（声明 %s，观测 %s）" % (g.get("name") or g.get("id"),
                                         g.get("declared"), g.get("observed")) for g in gaps]
        body = ("## 一句话\n缺口分两类：声明在做但盘上没产物（%d 条），以及已知结构性堵点。\n\n"
                "## 纸面业务\n%s\n\n"
                "## 已知堵点形态\n"
                "1) 卡指向的输入不存在（目录/成片/语料）→ 天天重试空转；\n"
                "2) 三个生成器发同一命令的重复卡 → 多机做同一件事；\n"
                "3) 归档不是终态时死卡会被旧 claim 复活；\n"
                "4) 远端产物被本机判成缺失（假红）；\n"
                "5) 节点仓库分叉导致改码到不了机器。\n\n"
                "## 怎么验证\n每条缺口都要能回答「现在还能不能修、谁来修、缺什么输入」。"
                % (len(gaps), "\n".join(rows) or "（暂无）"))
        metas.append(write_doc(os.path.join(KB, "40-progress", "03-gaps.md"),
                               {"id": "progress.gaps", "title": "缺口与堵点",
                                "layer": "progress",
                                "questions": ["哪里断了", "为什么断"],
                                "facts": ["state/lines.json", "cph4/fleet/BLOCKERS.md"],
                                "generated_at": now}, body, "template"))

    # ---- 50 skills
    if want("skills"):
        sk = F["skills"]
        rows = ["| 技能 | 作用域 | 一句话 |", "|---|---|---|"]
        for s in sk:
            rows.append("| `%s` | %s | %s |" % (s["name"], s["scope"], s["description"][:160]))
        body = ("## 一句话\n可调用技能 %d 个（全局 %d / 集团 %d），每个技能是一段可加载的操作规程。\n\n"
                "## 技能清单\n%s\n\n"
                "## 怎么用\n先按任务关键词选技能，再 `activate_skill` 载入其 SKILL.md；"
                "技能给的是流程与判据，不替代产物。\n\n## 我不知道的\n技能的实际生效版本以文件为准。"
                % (len(sk), len([s for s in sk if s["scope"] == "global"]),
                   len([s for s in sk if s["scope"] == "group"]), "\n".join(rows)))
        metas.append(write_doc(os.path.join(KB, "50-skills", "01-skills.md"),
                               {"id": "skills.catalog", "title": "技能库目录",
                                "layer": "skills",
                                "questions": ["有哪些技能", "做某事该载入哪个技能"],
                                "facts": ["~/.codely-cli/skills", "cph4/skills"],
                                "generated_at": now}, body, "template"))

        body = ("## 一句话\n常驻角色不是人，是分工：每条线的工序都标了 owner 与用哪台机。\n\n"
                "## 角色清单（取自线注册表 stages）\n" + "\n".join(
                    "- %s：%s" % (ln["name"], "；".join("%s(%s)" % (s.get("name"), fmt(s.get("owner")))
                                                      for s in ln["stages"]) or "未登记")
                    for ln in F["lines"]) +
                "\n\n## 怎么用\n派活时按 stage 找 owner；owner 不等于机器，lane 才是机器。\n\n"
                "## 我不知道的\n各席的决策权限细节分散在 cph4/council 与 docs/decisions.md。")
        metas.append(write_doc(os.path.join(KB, "50-skills", "02-seats.md"),
                               {"id": "skills.seats", "title": "席位与工序分工",
                                "layer": "skills",
                                "questions": ["谁负责哪道工序", "哪台机跑"],
                                "facts": ["LINE-REGISTRY.json(stages)", "cph4/agents/AGENT-LIBRARY.md"],
                                "generated_at": now}, body, "template"))

    # ---- INDEX + README
    idx = {"generated_at": now, "repo_root": ROOT,
           "how_to_use": ["先读 AI-KB/README.md", "再读 INDEX.json 选文档",
                          "数字以 90-machine/facts.json 为准，正文是解释"],
           "count": len(metas), "docs": metas}
    with open(os.path.join(KB, "INDEX.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)

    readme = """# AI-KB｜集团资料库（给 AI 读的）

> 本目录由 `Tools/kb/build_kb.py` 生成，**不要手改产物**；要改就改事实源或生成器，再跑一次。

## 给 AI 的三步读法
1. 读 `INDEX.json`：每篇文档的 id、路径、回答哪些问题、事实来源、生成时间。
2. 按层读：`00-identity`（是谁、红线）→ `10-business`（做什么）→ `20-engineering`（怎么做）
   → `30-operations`（怎么跑）→ `40-progress`（做到哪）→ `50-skills`（有什么能力）。
3. 要数字时读 `90-machine/facts.json`——正文里的数字都是它的转述，冲突时以它为准。

## 目录
| 目录 | 内容 | 什么时候读 |
|---|---|---|
| `00-identity/` | 组织、红线、术语 | 任何任务开始前 |
| `10-business/` | 15 条业务线逐线一页 + 组合总表 | 判断优先级与归属 |
| `20-engineering/` | 架构、工具目录、产物清单 | 动手改代码前 |
| `30-operations/` | 机队、主控脉、队列与卡 | 派单、排障 |
| `40-progress/` | 进度快照、在飞清单、缺口 | 汇报与决策 |
| `50-skills/` | 技能库、席位分工 | 选技能、找人 |
| `90-machine/` | facts.json（机读事实） | 需要精确数字 |

## 每篇文档的固定骨架
`front-matter`（id/title/layer/questions/facts/generated_at/written_by）+
`一句话 / 结构 / 关键约定 / 怎么验证 / 我不知道的`。
「我不知道的」一节是硬要求：写不出来就说明这篇在装懂。

## 新鲜度
`generated_at` 超过 24 小时即视为过期，重新生成：
```
python Tools/kb/build_kb.py            # 调本地模型写叙述
python Tools/kb/build_kb.py --no-llm   # 只刷事实与模板
python Tools/kb/build_kb.py --check    # 校验齐全与新鲜
```
"""
    with open(os.path.join(KB, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    print("[kb] 生成 %d 篇 → %s" % (len(metas), os.path.relpath(KB, ROOT)))
    for m in metas:
        print("   %-46s %-10s %s" % (m["path"], m["written_by"], m["title"]))
    return metas


# ------------------------------------------------------------------ 校验
def check():
    idx_p = os.path.join(KB, "INDEX.json")
    if not os.path.exists(idx_p):
        print("[kb] E-MISSING: INDEX.json 不存在，先跑 build")
        return 1
    idx = _json(idx_p, {}) or {}
    bad = []
    now = time.time()
    for d in idx.get("docs") or []:
        p = os.path.join(ROOT, d.get("path") or "")
        if not os.path.exists(p):
            bad.append("%s 缺失" % d.get("id"))
            continue
        try:
            head = open(p, encoding="utf-8").read(1200)
        except Exception:
            bad.append("%s 读不出" % d.get("id"))
            continue
        for k in ("id:", "title:", "layer:", "facts:", "generated_at:"):
            if k not in head:
                bad.append("%s 缺 front-matter 字段 %s" % (d.get("id"), k))
        if "## 我不知道的" not in head and "我不知道的" not in open(p, encoding="utf-8").read():
            bad.append("%s 缺「我不知道的」一节" % d.get("id"))
        ts = str(d.get("generated_at") or "")
        try:
            age = (now - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) / 3600.0
            if age > 24:
                bad.append("%s 已过期 %.1f 小时" % (d.get("id"), age))
        except Exception:
            bad.append("%s generated_at 解析失败" % d.get("id"))
    if bad:
        print("[kb] CHECK FAIL（%d）" % len(bad))
        for b in bad[:15]:
            print("   -", b)
        return 1
    print("[kb] CHECK PASS：%d 篇齐全、字段合规、24 小时内" % len(idx.get("docs") or []))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.check:
        return check()
    build(only=a.only or None, use_llm=not a.no_llm)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))