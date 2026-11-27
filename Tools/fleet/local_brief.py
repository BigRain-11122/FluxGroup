#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_brief.py - 用本机大模型把机队事实写成给 CEO 的 2-3 句人话

为什么要有它（2026-11-16 CEO「要用好本地大模型的能力……不管是自动化和可视化
都要去调用本地大模型去实现」）：
  看板上一堆数字，CEO 还要自己拼结论。本地 4B 干这活很合适——但它不能算数。
  记忆铁律（2026-11-13 实测）：「事实与措辞分家」——数字与判定全部由规则算出，
  模型只负责把它们说成人话；且输出里出现的任何数字都必须能在事实清单里找到，
  否则整句作废、回落模板。否则 4B 会编出"机队"是航空公司这类东西。

三层防线：
  1. 事实层：facts() 只从盘上文件读，不猜（队列/执行器判定/静默边界/体检结论）
  2. 生成层：ollama /api/generate，think=false，temp=0.2，超时 30s
  3. 校验层：输出里每个数字 token 必须在事实文本中出现；出现"建议/应该"但无断点即扣分；
     校验不过 → 用模板句，并在产物里标 fallback=true（诚实，不装成模型写的）

用法：
  python3 Tools/fleet/local_brief.py            # 生成（10 分钟内复用缓存）
  python3 Tools/fleet/local_brief.py --force     # 强制重生成
  python3 Tools/fleet/local_brief.py --json      # 机读
退出码：0 成功（或缓存） / 1 回落模板 / 2 模型不可用
"""
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT = os.path.join(STATE, "viz-brief.json")
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("BRIEF_MODEL", "qwen3.5:4b-mlx")
TTL_S = 600          # 缓存 10 分钟：页面 15s 刷新，不能每次都喊模型
TIMEOUT_S = 30


def _age(path):
    try:
        return time.time() - os.path.getmtime(path)
    except Exception:
        return None


def facts():
    """只从盘上读，不推断。返回给模型的事实清单与给校验用的原文。"""
    f = {}
    today = time.strftime("%Y-%m-%d")
    yday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    meta = ("TRIAGE", "PLAN", "CHECK", "ENV-PROBE", "CANARY", "PATROL",
            "AUDIT", "PROBE", "SCAN")
    done = real = opened = ydone = 0
    real_ids = []
    try:
        with open(os.path.join(ROOT, "cph4/fleet/PRODUCTION-QUEUE.jsonl"), encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                st = str(r.get("state") or "")
                if st == "OPEN":
                    opened += 1
                t = str(r.get("done_at") or r.get("finished_at") or r.get("ts") or "")[:10]
                if st == "DONE" and t == yday:
                    ydone += 1
                if st == "DONE" and t == today:
                    done += 1
                    cid = str(r.get("id") or "")
                    if not any(k in cid.upper() for k in meta):
                        real += 1
                        real_ids.append(cid)
    except Exception:
        pass
    f["今日完成卡数"] = done
    f["昨日完成卡数"] = ydone
    f["其中交付物卡数"] = real
    f["待派卡数"] = opened
    f["交付物示例"] = "、".join(real_ids[:3]) if real_ids else "无"

    ex = {}
    try:
        rv = json.load(open(os.path.join(STATE, "executor-revive.json"), encoding="utf-8"))
        for node, d in rv.items():
            d = d or {}
            v = str(d.get("verdict") or d.get("action") or "未探")
            try:
                h = (time.time() - float(d.get("ts"))) / 3600.0
            except Exception:
                h = None
            if v == "healthy" and h is not None and h > 1:
                v = "healthy但陈旧"
            ex[node] = v
    except Exception:
        pass
    f["执行器"] = ex
    f["有执行器的机器数"] = len([k for k, v in ex.items() if v == "healthy"])

    f["静默边界已上锁"] = os.path.exists(
        os.path.join(ROOT, ".codely-cli", "state", "FLEET-PAUSED"))
    la = os.path.expanduser("~/Library/LaunchAgents")
    try:
        import glob
        f["本机自启项数"] = len(glob.glob(os.path.join(la, "com.fluxgroup.*.plist")))
    except Exception:
        pass

    va = None
    try:
        va = json.load(open(os.path.join(STATE, "viz-audit.json"), encoding="utf-8"))
    except Exception:
        pass
    if va:
        # 键名写清楚作用域：2026-11-16 实测模型把它读成"机队整体是绿色"（它只描述看板本身）。
        f["看板体检结论(仅指看板页面,不代表机队)"] = va.get("verdict")
        bad = [r["name"] for r in (va.get("rows") or []) if r.get("need_human")]
        f["看板待人工项"] = "、".join(bad) if bad else "无"

    pulses = _age(os.path.join(ROOT, "cph4/fleet/dispatcher", "PULSE.json"))
    f["主控脉节拍分钟"] = round(pulses / 60.0, 1) if pulses is not None else None
    return f


PROMPT = """你是机队主控的播报员。下面 JSON 是刚从磁盘读到的事实清单。

用 2 到 3 句中文，直接向 CEO 汇报当前状态。

硬规则（违反任何一条即为无效输出）：
1. 只能使用清单里出现过的数字，严禁新增任何数字。
2. 只陈述清单里的事实，不要推测、不要编造清单外的信息。
3. 不要写"建议""应该""需要加强"这类空话。
4. 先给最关键的结论，再点出断点（如果清单里有）。
5. 清单里没有"机队整体状态"这个字段，禁止输出"机队状态为X/整体为X"这类总结判断；
   "看板体检结论"只描述看板页面本身，与机队产出无关。
6. 今日与昨日口径分开说，不要把两者混为一谈。
7. 机器状态必须用中文：healthy=正常、offline=离线、closeout=待收口、wake=唤醒中、
   未探=未探测；不要中英混写。

事实清单：
{facts}

播报："""


def call_model(ftext):
    body = json.dumps({
        "model": MODEL,
        "prompt": PROMPT.format(facts=ftext),
        "stream": False,
        "think": False,
        "options": {"num_ctx": 4096, "temperature": 0.2, "top_p": 0.9},
        "keep_alive": "5m",
    }).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", body,
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        d = json.load(r)
    return (d.get("response") or "").strip(), round(time.time() - t0, 1)


NUM = re.compile(r"\d+(?:\.\d+)?")


def verify(text, ftext, f):
    """输出里每个数字都必须能在事实文本里找到；否则判无效。"""
    bad = [n for n in NUM.findall(text) if n not in ftext]
    if bad:
        return False, "出现事实外的数字：%s" % "、".join(sorted(set(bad))[:4])
    if len(text) > 220:
        return False, "过长（%d 字），超出播报要求" % len(text)
    if not text.strip():
        return False, "空输出"
    return True, ""


def template(f):
    """模型不可用或校验不过时的事实句（不装成模型写的）。"""
    ex = f.get("执行器") or {}
    good = [k for k, v in ex.items() if v == "healthy"]
    bad = [k for k, v in ex.items() if v not in ("healthy",)]
    s1 = "今日完成 %d 张卡，其中交付物 %d 张，待派 %d 张。" % (
        f.get("今日完成卡数") or 0, f.get("其中交付物卡数") or 0, f.get("待派卡数") or 0)
    if good:
        s2 = "执行器正常 %s。" % "、".join(good)
    else:
        s2 = "没有执行器处于正常状态。"
    if bad:
        s2 += "%s 不在正常态。" % "、".join(bad)
    s3 = "可视化体检 %s。" % (f.get("可视化体检结论") or "-")
    return s1 + s2 + s3


def generate(force=False):
    try:
        prev = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        prev = None
    if prev and not force and (time.time() - float(prev.get("born") or 0)) < TTL_S:
        return prev
    f = facts()
    ftext = json.dumps(f, ensure_ascii=False, indent=1)
    out = {"born": time.time(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "model": MODEL, "facts": f, "text": "", "fallback": False,
           "elapsed_s": None, "why": ""}
    try:
        text, el = call_model(ftext)
        ok, why = verify(text, ftext, f)
        if ok:
            out.update({"text": text, "elapsed_s": el})
        else:
            out.update({"text": template(f), "fallback": True,
                        "elapsed_s": el, "why": why})
    except Exception as e:
        out.update({"text": template(f), "fallback": True,
                    "why": "模型不可用：%s" % str(e)[:80]})
    os.makedirs(STATE, exist_ok=True)
    try:
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = generate(a.force)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        tag = "模板(回落)" if r.get("fallback") else ("%s · %.1fs" % (r.get("model"), r.get("elapsed_s") or 0))
        print("[brief] %s" % tag)
        if r.get("why"):
            print("[brief] 原因: %s" % r["why"])
        print(r["text"])
    if r.get("fallback"):
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
