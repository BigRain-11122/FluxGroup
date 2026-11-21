#!/usr/bin/env python3
"""agent_daemon.py — 一个号一个智能体，24 小时自己刷。

CEO 2026-11-20：「技术上能并行就并行，建立 2 个不同的智能体去管理，我的机器专门做养号，
24 小时不停」。

职责划分（一个进程只管一个号，互不干扰）：
- 按**该号人设的活跃时段**决定何时开窗（不是固定间隔，人不会准点刷）
- 一场结束 → 随机歇 20–90 分钟 → 再判断要不要开下一场
- 动作层与另一个号**错峰**（同一 IP 两个号同时动手是最容易被串起来的特征）；
  浏览可以并行（不同 profile、不同视频），动手不行
- 任何异常都不退出：记一笔、歇一会儿、继续（24 小时不停）

用法：
  python3 Tools/fleet/agent_daemon.py --account acct1
  python3 Tools/fleet/agent_daemon.py --account acct3 --dry
"""
from __future__ import annotations

import argparse
import json
import os
import random
import signal
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOG = os.path.join(STATE, "agent-daemon.jsonl")
sys.path.insert(0, HERE)

STOP = False


def _stop(signum, frame):
    global STOP
    STOP = True


def log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    os.makedirs(STATE, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def persona(alias):
    try:
        d = json.load(open(os.path.join(ROOT, "cph4", "fleet", "social",
                                        "ACCOUNT-PERSONAS.json"), encoding="utf-8"))
        return d.get(alias) or {}
    except Exception:
        return {}


def in_hours(per, now=None):
    hrs = per.get("hours") or []
    if not hrs:
        return True
    h = (now or datetime.now()).hour
    return any(abs(h - x) <= 1 or abs(h - x) >= 23 for x in hrs)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--min-gap", type=int, default=5, help="两场之间最少歇几分钟（CEO：加快频率）")
    ap.add_argument("--max-gap", type=int, default=20)
    a = ap.parse_args(argv)
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    os.environ["FLUX_ACCOUNT"] = a.account
    per = persona(a.account)
    rng = random.Random()
    print("[daemon] %s（%s）启动：时段=%s 配额=%s%s"
          % (a.account, per.get("name"), per.get("hours"), per.get("caps"),
             " [dry]" if a.dry else ""), flush=True)
    log({"event": "start", "account": a.account, "persona": per.get("name"), "dry": a.dry})

    while not STOP:
        try:
            # 用平台真实作息时钟决定"现在该不该动"（activity_clock.py 从评论时间戳算出）。
            # 2026-11-21 CEO「频率太低，要符合 UP 主操作习惯」：原来按人设的 4 个整点 ±1 小时开，
            # 均匀得像机器；实测真实活跃是 22 点 2.6 倍、12 点 2.2 倍、凌晨 1–6 点接近 0。
            try:
                import activity_clock as _ac
                _plan = _ac.session_plan(persona=per)
            except Exception:
                _plan = {"open": in_hours(per), "minutes": 15}
            if not _plan.get("open"):
                time.sleep(600)
                continue
            import user_agent as ua
            # 强制本 daemon 只养这一个号
            os.environ["FLUX_ACCOUNT"] = a.account
            acct = ua.pick_account(a.account)
            if not acct:
                log({"event": "no_account", "account": a.account})
                time.sleep(1800)
                continue
            # 2026-11-21 CEO「你随机就好」：计划值只当基准，实际时长/动作量都加抖动，
            # 免得每天同一分钟、同一长度——那本身就是"不是人"的证据。
            _base_min = int(_plan.get("minutes") or rng.randint(8, 35))
            minutes = max(5, int(round(_base_min * rng.uniform(0.7, 1.4))))
            if _plan.get("comment"):
                _plan["comment"] = max(1, int(round(_plan["comment"] * rng.uniform(0.6, 1.5))))
            if _plan.get("danmaku"):
                _plan["danmaku"] = max(1, int(round(_plan["danmaku"] * rng.uniform(0.6, 1.6))))
            if _plan.get("like"):
                _plan["like"] = max(2, int(round(_plan["like"] * rng.uniform(0.6, 1.6))))
            t0 = time.time()
            sent = os.path.join(STATE, "AGENT-SESSION-%s" % a.account)
            try:
                open(sent, "w", encoding="utf-8").write(str(os.getpid()))
            except Exception:
                pass
            # 会话期间要出稿（要 GPU）。2026-11-21 实锚：训练 19 轮把 GPU 占满，
            # 养号"开一场"却生成不出字，一整天 0 条产出。所以会话先拿"publish"租约、
            # 持有到会话结束；拿不到就跳过这一场（训练正在关键处，不硬抢）。
            _lease = None
            if not a.dry:
                try:
                    import gpu_lease as _gl
                    _got, _why = _gl.acquire("publish", ttl_s=minutes * 60 + 600, wait_s=60)
                except Exception:
                    _got, _why = True, ""
                if not _got:
                    log({"event": "skip_gpu", "account": a.account, "why": _why})
                    print("[daemon] %s 让路：%s" % (a.account, _why), flush=True)
                    time.sleep(300)
                    continue
                _lease = _gl
            print("[daemon] %s 开一场 %d 分钟" % (a.account, minutes), flush=True)
            try:
                r = ua.run_session(minutes, dry=a.dry, force=True)
            finally:
                if _lease is not None:
                    try:
                        _lease.release("publish")
                    except Exception:
                        pass
                try:
                    os.remove(sent)
                except Exception:
                    pass
            log({"event": "session", "account": a.account, "minutes": minutes,
                 "ok": bool(r.get("ok")), "why": r.get("why"),
                 "steps": len(r.get("steps") or []), "cost_s": int(time.time() - t0)})
            # 效能：今天场次没达标就缩短间隔补场；达标后拉长，别把"多"做成"密"。
            try:
                import user_agent as _ua
                name = acct.get("uname") or acct.get("mid")
                done_today = _ua.today_count("session", name)
            except Exception:
                done_today = 99
            target = 4
            if done_today < target:
                lo = max(5, a.min_gap // 2)
                gap = rng.randint(lo, max(lo, a.min_gap)) * 60
                print("[daemon] %s 今日 %d/%d 场 → 缩短歇息补场"
                      % (a.account, done_today, target), flush=True)
            else:
                gap = rng.randint(a.min_gap, a.max_gap) * 60
            # 深夜更长的歇（2-6 点基本不动）
            if datetime.now().hour in (2, 3, 4, 5):
                gap = max(gap, 3 * 3600)
            print("[daemon] %s 歇 %d 分钟" % (a.account, gap // 60), flush=True)
            t_end = time.time() + gap
            while time.time() < t_end and not STOP:
                time.sleep(30)
        except Exception as e:
            log({"event": "error", "account": a.account,
                 "why": "%s: %s" % (type(e).__name__, str(e)[:120])})
            print("[daemon] 异常 %s，30 分钟后继续" % type(e).__name__, flush=True)
            time.sleep(1800)
    log({"event": "stop", "account": a.account})
    print("[daemon] %s 收到停止信号，退出" % a.account, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
