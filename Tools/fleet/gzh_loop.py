#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_loop.py — 汽车公众号线的自驱循环（SENSE → DECIDE → ACT → RECORD）。

科学判断（不是猜的，全部来自本周实测）：
  1. **供给是真瓶颈**：公众号没有公开文章列表接口；搜狗微信第 1 页就验证码；
     必应 site: 查询会把共享单线程浏览器拖死。所以循环**不许假装能自己找料**——
     池子见底就记 BLOCKED-SUPPLY 并停手，等人给种子，而不是空转刷日志。
  2. **能自动化的三段**：采集（3 秒/篇，已验证）→ 结构统计（纯规则，可复算）
     → 训练集构造（标题/开篇对齐，可复算）。
  3. **不能自动化的**：判断"这篇写得好不好"。所以本器只做到"把料备成能训的形态"，
     出了稿必须人看。禁止自己给自己打分发稿。

一拍只做一件事，优先级：缺料 > 采集 > 学结构 > 造训练集。
用法：
  python3 Tools/fleet/gzh_loop.py --status
  python3 Tools/fleet/gzh_loop.py --once
  python3 Tools/fleet/gzh_loop.py --self-test
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
GZH = os.path.join(SOCIAL, "gzh")
URLS = os.path.join(GZH, "URLS.jsonl")
ARTICLES = os.path.join(GZH, "ARTICLES.jsonl")
INDUSTRY = os.path.join(GZH, "ARTICLES-INDUSTRY.jsonl")   # 静态垂类产业语料（不进文笔训练）
STRUCT = os.path.join(GZH, "STRUCT.json")
TRAINSET = os.path.join(GZH, "TRAINSET.jsonl")
LEDGER = os.path.join(GZH, "LOOP-LEDGER.jsonl")
SCREEN = os.path.join(GZH, "LOOP.md")

POOL_MIN = 50          # 风格池少于这个数：静态源补不回来，只能要人给种子
HARVEST_PER_TICK = 8   # 一拍最多 8 篇（单篇 3 秒 + 间隔，控制在两分钟内）
HARVEST_BUDGET = 540   # 单拍墙钟预算：到点收工退 0，不许把调度器拖到超时
LEARN_AFTER = 20       # 采满 20 篇才值得学结构
TRAIN_AFTER = 100      # 100 篇才够造训练集（标题对/开篇对）
STALE_H = 12           # 学习产物超过 12 小时且新料变多 → 重学
INDUSTRY_TARGET = 200  # 产业语料目标：静态源可自动扩，不需要人给种子
SUPPLY_PER_TICK = 25   # 补料一拍最多入库几篇（两源各 25 ≈ 100 秒）


def _now():
    return datetime.now()


def _lease(platform):
    """向资源仲裁器申请本平台租约。返回 (rc, why)；仲裁器不可用时放行（不因工具缺失停工）。"""
    try:
        sys.path.insert(0, HERE)
        import res_alloc
        return res_alloc.may(platform)
    except Exception as e:
        return 0, "仲裁器不可用（%s）：放行" % type(e).__name__


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _append(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _atomic_json(path, obj):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _atomic_text(path, text):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


LOCKF = os.path.join(ROOT, ".codely-cli", "state", "gzh-loop.lock")


def _pid_alive(pid: int) -> bool:
    """True if a process with this pid exists (Windows via OpenProcess, POSIX via os.kill 0)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _lock():
    """单实例锁：POSIX 用 fcntl；Windows 无 fcntl，退回 pid 文件 + 存活校验（死锁自动回收）。"""
    os.makedirs(os.path.dirname(LOCKF), exist_ok=True)
    try:
        import fcntl
        f = open(LOCKF, "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(os.getpid()))
        f.flush()
        return f
    except ImportError:
        pass  # Windows: fall back to pid-file lock
    except Exception:
        return None  # POSIX: another instance holds the lock
    # Windows fallback
    try:
        if os.path.exists(LOCKF):
            try:
                holder = int((io.open(LOCKF, encoding="utf-8", errors="replace").read() or "0").strip() or 0)
            except Exception:
                holder = 0
            if holder and holder != os.getpid() and _pid_alive(holder):
                return None
        f = io.open(LOCKF, "w", encoding="utf-8")
        f.write(str(os.getpid()))
        f.flush()
        return f
    except Exception:
        return None


def _unlock(f):
    try:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        return
    except ImportError:
        pass
    except Exception:
        pass
    try:
        f.close()
        if os.name == "nt" and os.path.exists(LOCKF):
            os.remove(LOCKF)
    except Exception:
        pass


def _blocked_streak():
    """末尾连续 BLOCKED-SUPPLY 的拍数：用来把"缺料"从静默升级为告警。"""
    n = 0
    for r in reversed(_rows(LEDGER)):
        if r.get("status") in ("BLOCKED-SUPPLY", "ESCALATE-SUPPLY"):
            n += 1
        else:
            break
    return n


def _age_h(p):
    try:
        return (_now() - datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() / 3600
    except Exception:
        return None


# ---------------- SENSE ----------------

STATIC_HOSTS = ("auto.gasgoo.com", "www.d1ev.com", "d1ev.com")


def _is_static(url):
    from urllib.parse import urlsplit
    host = urlsplit(url or "").netloc.lower()
    return any(host == h or host.endswith("." + h) for h in STATIC_HOSTS)


def sense():
    """两本账分开数，因为它们是两件事：

      · **风格池**（mp.weixin / 车家号）→ ARTICLES.jsonl，能进文笔训练；
      · **产业语料**（盖世 / 第一电动）→ ARTICLES-INDUSTRY.jsonl，只做形态与事实，
        genre=industry，训练时排除。

    2026-11-25 实锚：把两本账混着数，池里 71 条**已经采完**的盖世链接被当成待抓，
    还被送进公众号提取器，每条卡满 25 秒 → 一次 900 秒预算跑爆判 CRASHED。
    教训：同一条事实写在两处、判据还各算一次，必出假待办。
    """
    pool = _rows(URLS)
    arts = _rows(ARTICLES)
    ind = _rows(INDUSTRY)
    pool_u = {r.get("_uid") for r in pool if r.get("_uid")}
    done_u = {r.get("_uid") for r in arts if r.get("_uid")}
    ind_u = {r.get("_uid") for r in ind if r.get("_uid")}
    # 风格池待抓：排除静态源链接（它们归产业语料，不归这里）
    style_rows = [r for r in pool if not _is_static(r.get("url"))]
    style_u = {r.get("_uid") for r in style_rows if r.get("_uid")}
    todo = [r for r in style_rows if r.get("_uid") not in done_u]
    struct = None
    try:
        struct = json.load(open(STRUCT, encoding="utf-8"))
    except Exception:
        pass
    return {
        "pool": len(pool_u), "style_pool": len(style_u),
        "pool_todo": len(todo), "style_todo": len(todo),
        "articles": len(done_u), "industry": len(ind_u),
        "struct_age_h": _age_h(STRUCT), "train_rows": len(_rows(TRAINSET)),
        "struct_n": (struct or {}).get("n"),
        "eligible": sum(1 for a in arts
                        if len((a.get("title") or "")) >= 6 and len((a.get("lead") or "")) >= 40),
        "ts": _now().isoformat(timespec="seconds"),
    }


# ---------------- DECIDE ----------------

def decide(s):
    """一拍只做一件事，顺序按「哪件现在真能推进」排：

      1. 风格池有货 → 先抓（这是唯一能进文笔训练的料）
      2. 产业语料不足 → 自动扩采（静态源免登录，不等任何人）
      3. 风格池见底 → 才升级要人给种子（公众号发现通道全封，这是真墙）

    为什么 2 排在 3 前面：CEO 最高规则是「禁以等人为由停工」。静态源能自己产，
    就没有理由让循环空转 68 拍写 ESCALATE-SUPPLY（2026-11-25 实锚）。
    """
    if s["style_todo"] > 0:
        return {"phase": "harvest",
                "why": "风格池还有 %d 条没抓" % s["style_todo"]}
    if s["industry"] < INDUSTRY_TARGET:
        return {"phase": "supply-industry",
                "why": "产业语料 %d/%d 篇，静态源可自动扩（不需要人给种子）"
                       % (s["industry"], INDUSTRY_TARGET)}
    if s["style_pool"] < POOL_MIN:
        return {"phase": "supply",
                "why": "风格池 %d 条 < %d：公众号发现通道全封，只能要人给种子"
                       % (s["style_pool"], POOL_MIN)}
    if s["struct_age_h"] is None or (s["struct_age_h"] or 0) > STALE_H:
        return {"phase": "learn", "why": "结构统计缺失或 %s 小时前"
                                          % (round(s["struct_age_h"], 1) if s["struct_age_h"] else "从未")}
    eligible = s.get("eligible", 0)
    if s["articles"] >= TRAIN_AFTER and eligible >= 20 and s["train_rows"] < 2 * eligible:
        return {"phase": "trainset", "why": "已采 %d 篇，训练集只有 %d 行"
                                            % (s["articles"], s["train_rows"])}
    return {"phase": "watch", "why": "料够、结构新、训练集齐；等出稿或等新种子"}


# ---------------- ACT ----------------

def act_harvest(limit=HARVEST_PER_TICK, rng=None):
    """调采集器抓一小批（子进程，别把循环拖死）。

    预算双保险：子进程自带 --budget-secs 会自己收工；外面再套一层硬超时，
    超时也只当「本拍没抓到」记下来，绝不让整个调度判 CRASHED。
    """
    rng = rng or random.Random()
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, "wechat_article.py"),
                            "--harvest", str(limit),
                            "--budget-secs", str(HARVEST_BUDGET)],
                           capture_output=True, text=True,
                           timeout=HARVEST_BUDGET + 180, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "secs": round(time.time() - t0, 1),
                "tail": "本拍超过 %d 秒硬超时，已放弃（不是崩溃，下一拍再来）"
                        % (HARVEST_BUDGET + 180)}
    tail = (p.stdout or p.stderr or "").strip().splitlines()[-4:]
    return {"ok": p.returncode == 0, "secs": round(time.time() - t0, 1),
            "tail": "\n".join(tail)[-400:]}


def act_supply_industry(limit=SUPPLY_PER_TICK):
    """静态垂类源自动补料（盖世 + 第一电动），不需要人给种子。

    这是把 supply 从「等 CEO」改成「自己找」的那一步：两家都是纯静态、免登录，
    实测单篇 1 秒左右、平均 2200-2500 字，一拍 25 篇约 100 秒。
    """
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, "gzh_corpus_expand.py"),
                            "--source", "all", "--limit", str(limit)],
                           capture_output=True, text=True, timeout=600, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "secs": round(time.time() - t0, 1),
                "tail": "补料超过 600 秒硬超时，已放弃（下一拍再来）"}
    tail = (p.stdout or p.stderr or "").strip().splitlines()[-6:]
    # 退出码 2 = 两个源一篇都没抓到 → 这才算补料失败
    return {"ok": p.returncode == 0, "secs": round(time.time() - t0, 1),
            "tail": "\n".join(tail)[-500:]}


_NUM = re.compile(r"\d")
_Q = re.compile(r"[？?]|吗|到底|是不是|能不能|该不该|为何|为什么|怎么")


def _style_arts(arts):
    """只用 genre=review 的篇目标定文风；通稿（press）与未知一律不进。

    2026-11-23 群审第一条就是"语料错配"：拿机构通稿标定，训出来必然是公文腔。
    genre 由 wechat_article.genre_of 判定（带 3 条负控）；没有 genre 列的老行按 unknown 处理。
    """
    use = [a for a in arts if a.get("genre") == "review"]
    drop = [a for a in arts if a.get("genre") != "review"]
    return use, drop


def learn_struct(arts=None):
    """纯规则统计：标题/开篇的形态分布。可复算，不猜。"""
    arts = arts if arts is not None else _rows(ARTICLES)
    if not arts:
        return None
    arts, _dropped = _style_arts(arts)
    if not arts:
        return None
    ts = [a.get("title") or "" for a in arts]
    leads = [(a.get("lead") or "").split("\n")[0][:80] for a in arts]
    n = len(arts)
    out = {
        "n": n,
        "ts": _now().isoformat(timespec="seconds"),
        "title_len_median": sorted(len(t) for t in ts)[n // 2],
        "title_has_num_pct": round(100.0 * sum(1 for t in ts if _NUM.search(t)) / n, 1),
        "title_question_pct": round(100.0 * sum(1 for t in ts if _Q.search(t)) / n, 1),
        "words_median": sorted((a.get("words") or 0) for a in arts)[n // 2],
        "heads_median": sorted(len(a.get("heads") or []) for a in arts)[n // 2],
        "imgs_median": sorted((a.get("imgs") or 0) for a in arts)[n // 2],
        "account_top": _top([a.get("account") for a in arts], 5),
        "lead_len_median": sorted(len(x) for x in leads)[n // 2],
    }
    os.makedirs(GZH, exist_ok=True)
    json.dump(out, open(STRUCT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def _top(xs, k):
    c = {}
    for x in xs:
        if x:
            c[x] = c.get(x, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])[:k]


def build_trainset(arts=None):
    """标题对 + 开篇对：给本地模型学的原料。只做对齐，不改写任何原文。"""
    arts = arts if arts is not None else _rows(ARTICLES)
    if not arts:
        return 0
    arts, _dropped = _style_arts(arts)
    if not arts:
        return 0
    os.makedirs(GZH, exist_ok=True)
    with open(TRAINSET, "w", encoding="utf-8") as f:
        for a in arts:
            t = (a.get("title") or "").strip()
            lead = (a.get("lead") or "").strip()
            if len(t) < 6 or len(lead) < 40:
                continue
            f.write(json.dumps({"kind": "title", "in": (a.get("account") or "") + "｜"
                                + (a.get("lead") or "")[:120], "out": t}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"kind": "lead", "in": t, "out": lead[:600]},
                               ensure_ascii=False) + "\n")
    return len(_rows(TRAINSET))


# 下一步的唯一事实：写死成"动作+判据+要谁动手"，任何会话读它就能接上，
# 不需要靠我记、也不需要问 CEO（CEO 2026-11-23：每次对话结尾都要知道下一步）。
NEXT_MAP = {
    "supply": {
        "id": "SUPPLY-1",
        "action": "要风格池种子（公众号/车家号链接或号名）",
        "judge": "风格池 ≥50 条且能翻页取到第 2 页",
        "needs": "人工（CEO/运营）：给 3-5 个号或链接。公众号发现通道全封（搜狗/百度/必应验证码、新榜/清博登录墙），这是唯一真墙",
        "eta": "本轮",
    },
    "supply-industry": {
        "id": "SUPPLY-IND",
        "action": "自动扩采产业语料（盖世汽车 + 第一电动，纯静态免登录）",
        "judge": "ARTICLES-INDUSTRY 净增 >0 且失败率 <30%",
        "needs": "无（自动推进，不等任何人）",
        "eta": "每 30 分钟一拍，单拍 ≤25 篇",
    },
    "harvest": {
        "id": "HARVEST",
        "action": "继续采集风格池，每拍最多 8 篇 / 540 秒预算",
        "judge": "ARTICLES 净增 >0 且失败率 <30%",
        "needs": "无",
        "eta": "每 30 分钟一拍",
    },
    "learn": {
        "id": "LEARN-STRUCT",
        "action": "出结构统计（标题长度/数字率/问句率/小标题密度/段落长度）",
        "judge": "STRUCT.json 的 n 等于已采篇数",
        "needs": "无",
        "eta": "本轮",
    },
    "trainset": {
        "id": "TRAINSET",
        "action": "生成标题对 + 开篇对训练集",
        "judge": "TRAINSET 行数 ≈ 2×篇数",
        "needs": "无",
        "eta": "本轮",
    },
    "watch": {
        "id": "TRAIN-GATE",
        "action": "堆语料至 200 篇（同作者 ≥10 篇、≥5 个作者）后才开训标题模型",
        "judge": "ARTICLES ≥200 且 作者数 ≥5",
        "needs": "无（自动推进）；不到门槛不训，避免浪费 GPU 并误判方向",
        "eta": "按采集速度自动",
    },
}


def write_next(s, task):
    """落 NEXT-STEP.json + NEXT-STEP.md，并返回该记录。"""
    base = NEXT_MAP.get(task["phase"], NEXT_MAP["watch"])
    rec = dict(base)
    rec.update({
        "phase": task["phase"], "why": task["why"],
        "facts": {"pool": s.get("pool"), "pool_todo": s.get("pool_todo"),
                  "style_pool": s.get("style_pool"), "industry": s.get("industry"),
                  "articles": s.get("articles"), "struct_n": s.get("struct_n"),
                  "train_rows": s.get("train_rows")},
        "progress": "风格 %d 篇 / 产业 %d/%d 篇"
                    % (s.get("articles") or 0, s.get("industry") or 0, INDUSTRY_TARGET),
        "ts": _now().isoformat(timespec="seconds"),
    })
    os.makedirs(GZH, exist_ok=True)
    _atomic_json(os.path.join(GZH, "NEXT-STEP.json"), rec)
    md = ["# 公众号线：下一步（唯一事实）", "",
          "> 任何会话/任何机器先读本文件再动手；它由 `gzh_loop.py` 每拍重算，不靠记忆。", "",
          "## %s · %s" % (rec["id"], rec["action"]), "",
          "- **为什么**：%s" % rec["why"],
          "- **判据**：%s" % rec["judge"],
          "- **要谁动手**：%s" % rec["needs"],
          "- **节奏**：%s" % rec["eta"],
          "- **进度**：%s" % rec["progress"],
          "- **事实**：%s" % json.dumps(rec["facts"], ensure_ascii=False),
          "- **更新时间**：%s" % rec["ts"], ""]
    _atomic_text(os.path.join(GZH, "NEXT-STEP.md"), "\n".join(md))
    return rec


def refresh_screen(s, task, rec=None):
    lines = ["# 公众号线（GZH-LOOP）", "",
             "| 项 | 值 |", "|---|---|",
             "| 风格池（能进文笔训练） | %d 条（待抓 %d） |" % (s["style_pool"], s["style_todo"]),
             "| 风格语料 | %d 篇 |" % s["articles"],
             "| 产业语料（只做形态/事实） | %d/%d 篇 |" % (s["industry"], INDUSTRY_TARGET),
             "| 结构统计 | %s（%s 小时前） |" % (s["struct_n"] or "无",
                                       round(s["struct_age_h"], 1) if s["struct_age_h"] else "从未"),
             "| 训练集 | %d 行 |" % s["train_rows"],
             "", "**本拍**：%s —— %s" % (task.get("phase"), task.get("why")), ""]
    if rec:
        lines += ["结果：`%s`｜%.1fs" % (rec.get("status"), rec.get("secs") or 0), "",
                  "```", (rec.get("tail") or "")[:600], "```", ""]
    lines += ["## 规则", "",
              "1. 两本账分开数：风格池归 ARTICLES.jsonl，产业语料归 ARTICLES-INDUSTRY.jsonl，"
              "混着数会造出假待办（实锚：71 条已采的盖世链接被当待抓，一次跑爆 900 秒）。",
              "2. 产业语料不足 %d 篇就自动补，**不等任何人**（静态源免登录）。" % INDUSTRY_TARGET,
              "3. 只有风格池见底才升级要种子——公众号发现通道全封，这是唯一的真墙。",
              "4. 采满 %d 篇才学结构；采满 %d 篇才造训练集。产业稿只学形态，不进文笔。" % (LEARN_AFTER, TRAIN_AFTER),
              "5. 本器不做「好不好」的判断——出稿必须人看，禁止自己打分发稿。", ""]
    os.makedirs(GZH, exist_ok=True)
    open(SCREEN, "w", encoding="utf-8").write("\n".join(lines))


# ---------------- 主流程 ----------------

def once(dry=False):
    """带锁与异常兜底的入口：任何一拍都要在台账留一行（含 CRASHED）。"""
    f = _lock()
    if f is None:
        print("[gzh] SKIP-LOCKED（另一个实例在跑）")
        return 0
    try:
        return _once_impl(dry=dry)
    except Exception as e:
        _append(LEDGER, {"ts": _now().isoformat(timespec="seconds"),
                         "phase": "unknown", "status": "CRASHED", "secs": 0,
                         "err": "%s: %s" % (type(e).__name__, str(e)[:300])})
        try:
            nx = {}
            p = os.path.join(GZH, "NEXT-STEP.json")
            if os.path.exists(p):
                nx = json.load(open(p, encoding="utf-8"))
            nx.update({"state": "CRASHED",
                       "err": "%s: %s" % (type(e).__name__, str(e)[:200]),
                       "ts": _now().isoformat(timespec="seconds")})
            _atomic_json(p, nx)
        except Exception:
            pass
        raise
    finally:
        _unlock(f)


def _once_impl(dry=False):
    s = sense()
    task = decide(s)
    write_next(s, task)
    rec = {"ts": s["ts"], "phase": task["phase"], "why": task["why"],
           "run_id": "%s-%d" % (s["ts"], os.getpid()),
           "facts": {k: s.get(k) for k in
                     ("pool", "pool_todo", "style_pool", "industry", "articles",
                      "struct_n", "train_rows", "eligible")}}
    if dry or task["phase"] == "watch":
        rec.update(status="WATCH", secs=0)
        _append(LEDGER, rec)
        refresh_screen(s, task, rec)
        print("[gzh] %s / %s" % (task["phase"], task["why"]))
        return 0
    if task["phase"] == "supply-industry":
        r = act_supply_industry()
        rec.update(status="OK" if r["ok"] else "FAIL", secs=r["secs"], tail=r["tail"])
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 产业补料 %s %.1fs" % ("完成" if r["ok"] else "失败", r["secs"]))
        print(r["tail"])
        return 0 if r["ok"] else 1
    if task["phase"] == "supply":
        # 缺料是真的阻塞，但"每拍成功什么都没做"会让 launchd 永远看到 exit 0。
        # 连续第 2 拍起升级为 ESCALATE-SUPPLY 并退非零，让异常在 launchctl 里一眼可见。
        streak = _blocked_streak() + 1
        esc = streak >= 2
        rec.update(status="ESCALATE-SUPPLY" if esc else "BLOCKED-SUPPLY", secs=0,
                   streak=streak,
                   need="URL 种子（给 3-5 个号或链接即可）" if not esc
                        else "已连续 %d 拍无料：镜像源采集器未实现，必须人工给种子" % streak)
        _append(LEDGER, rec)
        refresh_screen(s, task, rec)
        print("[gzh] %s（第 %d 拍）：%s" % (rec["status"], streak, task["why"]))
        if esc:
            print("[gzh] 升级：镜像源采集不在代码里，别再等它自己动")
            return 78          # EX_CONFIG：让 last exit code 非零
        return 0
    if task["phase"] == "harvest":
        # 平台租约：不是公众号时段就让位。记 DEFER 且退 0——
        # 记 FAIL 会触发退避，把语料永久压死（2026-11-23 踩过）。
        rc, why = _lease("gzh")
        if rc == 75:
            # 浏览器让位 ≠ 这一拍没事干。产业补料是纯 HTTP（urllib，不开浏览器），
            # 不占 browserd 单线程，照跑——否则等一个时段白等 30 分钟（2026-11-25 实锚：
            # 台账里 68 拍空转就是这么来的）。
            if s["industry"] < INDUSTRY_TARGET:
                r = act_supply_industry()
                rec.update(status="DEFER+SUPPLY" if r["ok"] else "DEFER+SUPPLY-FAIL",
                           secs=r["secs"], tail=r["tail"], why=why)
                _append(LEDGER, rec)
                refresh_screen(sense(), task, rec)
                print("[gzh] 采集让位（%s）→ 改跑产业补料 %s %.1fs"
                      % (why[:40], "完成" if r["ok"] else "失败", r["secs"]))
                print(r["tail"])
                return 0
            rec.update(status="DEFER", secs=0, tail=why)
            _append(LEDGER, rec)
            refresh_screen(sense(), task, rec)
            print("[gzh] 让位：%s" % why)
            return 0
        if rc != 0:
            rec.update(status="DENY", secs=0, tail=why)
            _append(LEDGER, rec)
            refresh_screen(s, task, rec)
            print("[gzh] 资源拒绝：%s" % why)
            return 0
        r = act_harvest()
        rec.update(status="OK" if r["ok"] else "FAIL", secs=r["secs"], tail=r["tail"])
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 采集 %s %.1fs" % ("完成" if r["ok"] else "失败", r["secs"]))
        print(r["tail"])
        return 0 if r["ok"] else 1
    if task["phase"] == "learn":
        st = learn_struct()
        rec.update(status="OK" if st else "FAIL", secs=0,
                   tail=json.dumps(st, ensure_ascii=False)[:300] if st else "无语料")
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 结构统计：%s" % rec["tail"])
        return 0 if st else 1
    if task["phase"] == "trainset":
        n = build_trainset()
        rec.update(status="OK" if n else "FAIL", secs=0, tail="训练集 %d 行" % n)
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 训练集 %d 行 → %s" % (n, os.path.relpath(TRAINSET, ROOT)))
        return 0
    return 0


def status():
    s = sense()
    task = decide(s)
    print("[gzh] 风格池 %d（待抓 %d）｜风格语料 %d 篇｜产业语料 %d/%d 篇｜结构 %s｜训练集 %d 行"
          % (s["style_pool"], s["style_todo"], s["articles"], s["industry"],
             INDUSTRY_TARGET,
             (str(s["struct_n"]) + " 篇/" + str(round(s["struct_age_h"], 1)) + "h")
             if s["struct_age_h"] else "无", s["train_rows"]))
    print("[gzh] 当前该做：%s —— %s" % (task["phase"], task["why"]))
    nx = NEXT_MAP.get(task["phase"], NEXT_MAP["watch"])   # 只读：不写文件、不刷新时间戳
    print("[gzh] 下一步 %s：%s" % (nx["id"], nx["action"]))
    print("[gzh] 判据：%s ｜ 动手：%s" % (nx["judge"], nx["needs"]))
    try:
        st = json.load(open(STRUCT, encoding="utf-8"))
        print("[gzh] 结构：标题中位 %s 字｜含数字 %s%%｜问句 %s%%｜正文中位 %s 字｜小标题 %s 个"
              % (st.get("title_len_median"), st.get("title_has_num_pct"),
                 st.get("title_question_pct"), st.get("words_median"), st.get("heads_median")))
    except Exception:
        pass
    return 0


def self_test():
    """负控：把判据弄坏必须变红，否则这个调度就是没接上的假绿。"""
    global URLS, ARTICLES, INDUSTRY, STRUCT, TRAINSET, INDUSTRY_TARGET
    import tempfile
    cases = []
    saved = (URLS, ARTICLES, INDUSTRY, STRUCT, TRAINSET, INDUSTRY_TARGET)
    d = tempfile.mkdtemp(prefix="gzhloop-")
    URLS, ARTICLES = os.path.join(d, "u.jsonl"), os.path.join(d, "a.jsonl")
    INDUSTRY = os.path.join(d, "ind.jsonl")
    STRUCT, TRAINSET = os.path.join(d, "s.json"), os.path.join(d, "t.jsonl")
    INDUSTRY_TARGET = 10          # 测试用小目标，判据逻辑与生产一致

    # N1 空池 → 不是等种子，而是先去自动补产业语料（守 CEO「禁以等人为由停工」）
    cases.append(("N1 全空→supply-industry（先自己找料）",
                  decide(sense())["phase"] == "supply-industry"))
    # N2 池够但没抓 → harvest 优先（风格料比产业料值钱）
    for i in range(POOL_MIN + 5):
        _append(URLS, {"_uid": "u%d" % i, "url": "https://chejiahao.autohome.com.cn/info/%d" % i})
    cases.append(("N2 池满未抓→harvest", decide(sense())["phase"] == "harvest"))
    # N2b 负控[本次真 bug] 静态源链接不得被算成风格待抓：
    # 实锚 2026-11-25，71 条已采完的盖世链接被当待抓，还送进公众号提取器跑爆 900 秒
    s_before = sense()["style_todo"]
    for i in range(5):
        _append(URLS, {"_uid": "g%d" % i,
                       "url": "https://auto.gasgoo.com/news/202611/x%d.shtml" % i})
    cases.append(("N2b 静态源不进风格待抓", sense()["style_todo"] == s_before))
    # N3 风格抓完但产业不足 → supply-industry（不是 learn，也不是空转等种子）
    for i in range(POOL_MIN + 5):
        _append(ARTICLES, {"_uid": "u%d" % i, "title": "标题%d 3 个理由" % i,
                           "lead": "开篇正文" * 30, "words": 600, "heads": ["a"], "imgs": 2,
                           "genre": "review"})
    cases.append(("N3 风格抓完但产业不足→supply-industry",
                  decide(sense())["phase"] == "supply-industry"))
    # N3b 产业语料补够 → 才进 learn
    for i in range(INDUSTRY_TARGET):
        _append(INDUSTRY, {"_uid": "i%d" % i, "title": "产业稿%d" % i,
                           "text": "行业正文" * 50, "genre": "industry", "source": "gasgoo"})
    cases.append(("N3b 产业补够→learn", decide(sense())["phase"] == "learn"))
    # N4 结构统计真的读语料：改语料必须改数字
    st = learn_struct()
    cases.append(("N4 结构统计 n 正确", st and st["n"] == POOL_MIN + 5))
    cases.append(("N5 数字标题率被算出来", st and st["title_has_num_pct"] == 100.0))
    # N6 训练集真的按篇数翻倍（title+lead 两条）
    n = build_trainset()
    cases.append(("N6 训练集成对生成", n == 2 * (POOL_MIN + 5)))
    # N7 结构新鲜时不该重复学
    cases.append(("N7 结构新鲜→不进 learn", decide(sense())["phase"] != "learn"))
    # N7b 产业稿绝不进风格语料/结构统计（两本账不许串）
    cases.append(("N7b 产业稿没被算进风格篇数", sense()["articles"] == POOL_MIN + 5))

    # N8 缺料必须能升级：连续两拍 BLOCKED-SUPPLY 之后 streak 必须到 2
    global LEDGER
    saved_led = LEDGER
    LEDGER = os.path.join(d, "led.jsonl")
    cases.append(("N8a 无阻塞行→streak=0", _blocked_streak() == 0))
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8b 一拍→streak=1（未升级）", _blocked_streak() == 1))
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8c 两拍→streak=2（应升级）", _blocked_streak() == 2))
    _append(LEDGER, {"status": "OK"})
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8d 中间有成功→重新计 1", _blocked_streak() == 1))
    LEDGER = saved_led

    # N9 过滤率过高不得进 trainset（否则每拍全文重写、永不推进）
    s9 = {"style_pool": 120, "style_todo": 0, "pool_todo": 0, "articles": 100,
          "industry": INDUSTRY_TARGET, "struct_age_h": 1.0,
          "train_rows": 20, "struct_n": 100, "eligible": 10}
    cases.append(("N9 可产行不足→不进 trainset", decide(s9)["phase"] != "trainset"))
    s9b = dict(s9, eligible=60, train_rows=20)
    cases.append(("N9b 可产行足够→进 trainset", decide(s9b)["phase"] == "trainset"))
    # N9c 风格池见底且产业也补满 → 才升级要种子（唯一的真墙）
    s9c = dict(s9, style_pool=3, style_todo=0, industry=INDUSTRY_TARGET,
               struct_age_h=0.5, eligible=60, train_rows=200)
    cases.append(("N9c 风格池见底+产业满→supply（要人给种子）",
                  decide(s9c)["phase"] == "supply"))

    # N10 负控：通稿（press）与未知（unknown）不得参与文风标定/训练集
    _append(ARTICLES, {"_uid": "p1", "title": "某指数结果发布丨N9 测评结果发布",
                       "lead": "测评背景 主办单位 联合发布" * 10, "words": 900,
                       "heads": ["背景", "方法"], "imgs": 1, "genre": "press"})
    _append(ARTICLES, {"_uid": "p2", "title": "没有文体的老行",
                       "lead": "开篇正文" * 30, "words": 600, "heads": [], "imgs": 0})
    st2 = learn_struct()
    cases.append(("N10a 通稿/未知不进文风标定（篇数不变）",
                  st2 and st2["n"] == POOL_MIN + 5))
    n2 = build_trainset()
    cases.append(("N10b 通稿/未知不进训练集（行数不变）",
                  n2 == 2 * (POOL_MIN + 5)))

    URLS, ARTICLES, INDUSTRY, STRUCT, TRAINSET, INDUSTRY_TARGET = saved
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.once:
        return once(dry=a.dry)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
