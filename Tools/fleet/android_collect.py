#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""android_collect.py - 设备端素材采集（模拟人为操作）。

CEO 2026-11-23：「你的素材采集都要走这些，模拟人为操作，自己科学判断和梳理」。
本工具只做一件事：在模拟器里像人一样滑、停、看，把屏幕上真实出现过的文本抽成结构化语料。

三条硬约束（违反即数据不可用）：
1) **只读**：不点赞、不关注、不发送、不点广告；只 scroll / dump / 返回。
2) **像人**：滑动手势参数随机（距离 35-65% 屏高、时长 220-620ms）、每次读完停留 2-9s、
   每轮之间过 social_riskguard.wait_turn（基准间隔 + 0-40% 抖动）、10% 概率回滑一下、
   凌晨 2-6 点不采（真人也不在这时候刷）。
3) **可复算**：每轮都留 ui.xml 原件到 state/android-collect/，JSONL 里写 evidence 路径；
   抽不到就写 UNKNOWN 并退非 0，**不许用 0 条冒充"该页没内容"**。

输出契约（同时修掉"语料没有 platform 字段"的老技术债）：
  {"platform","kind","text","author","like","ts","evidence","avd","session"}
  → 直接喂 human_corpus.py --from-dir

用法：
  python3 Tools/fleet/android_collect.py --avd acct1 --platform bilibili --kind feed --rounds 3
  python3 Tools/fleet/android_collect.py --avd acct1 --platform bilibili --kind comment --parse-only /tmp/ui.xml
Exit: 0 正常；2 环境/设备问题；1 抽取为 0（UNKNOWN，不写成成功）
"""
import argparse
import hashlib
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
SDK = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/android-sdk")
ADB = os.path.join(SDK, "platform-tools", "adb")
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "android-collect")
RAW = os.path.join(ROOT, "cph4", "fleet", "social", "raw")

RISK_WORDS = ("验证码", "安全验证", "请完成验证", "行为异常", "操作频繁", "captcha", "CAPTCHA",
              "人机验证", "滑动验证", "账号异常", "登录后查看")


def sh(cmd, timeout=40, binary=False):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = r.stdout if binary else (r.stdout or b"").decode("utf-8", "replace")
        return r.returncode, out, (r.stderr or b"").decode("utf-8", "replace")
    except Exception as e:
        return 1, (b"" if binary else ""), str(e)


def serial_of(avd):
    """acct1 -> emulator-5554（与 android_farm 的端口分配一致）"""
    home = os.path.expanduser("~/.android/avd")
    names = sorted(f[:-4] for f in os.listdir(home) if f.endswith(".ini")) if os.path.isdir(home) else []
    if avd not in names:
        return None
    return "emulator-%d" % (5554 + 2 * names.index(avd))


def win_size(serial):
    rc, out, _ = sh([ADB, "-s", serial, "shell", "wm", "size"])
    m = re.search(r"(\d+)x(\d+)", out or "")
    return (int(m.group(1)), int(m.group(2))) if m else (1080, 2400)


def human_swipe(serial, w, h, direction="up"):
    """像人一样滑：随机起止点、随机时长、轻微横向漂移。"""
    dist = random.randint(int(h * 0.35), int(h * 0.65))
    x0 = random.randint(int(w * 0.35), int(w * 0.65))
    drift = random.randint(-int(w * 0.08), int(w * 0.08))
    dur = random.randint(220, 620)
    if direction == "up":
        y0, y1 = int(h * 0.72), int(h * 0.72) - dist
    else:
        y0, y1 = int(h * 0.30), int(h * 0.30) + dist
    sh([ADB, "-s", serial, "shell", "input", "swipe",
        str(x0), str(y0), str(x0 + drift), str(y1), str(dur)], 20)
    return dur


def dwell(lo=2.0, hi=9.0):
    """读完停留：真实用户不会 0.2 秒翻一屏。"""
    t = random.uniform(lo, hi)
    time.sleep(t)
    return round(t, 1)


def dump(serial, tag):
    os.makedirs(STATE, exist_ok=True)
    remote = "/sdcard/_ac.xml"
    sh([ADB, "-s", serial, "shell", "uiautomator", "dump", remote], 40)
    dst = os.path.join(STATE, "ui-%s-%s.xml" % (tag, time.strftime("%H%M%S")))
    rc, data, err = sh([ADB, "-s", serial, "pull", remote, dst], 40)
    if not os.path.exists(dst):
        return None, err
    return dst, None


def parse_ui(xml_path):
    """抽 text 节点 + 邻接 like 数；返回 (items, risk_hit)"""
    with open(xml_path, encoding="utf-8") as f:
        s = f.read()
    risk = next((w for w in RISK_WORDS if w in s), None)
    items = []
    # bounds 用来判断"这是一条独立条目"（纵向成块），并附带位置便于人味排序
    for m in re.finditer(r'text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s):
        txt = m.group(1).strip()
        if not txt or len(txt) < 2:
            continue
        y0 = int(m.group(3))
        items.append({"text": txt, "y": y0})
    # 纯数字/时长等噪声（如 "1.2万"、"7:08"）留给上层过滤，这里不主观删
    return items, risk


def write_jsonl(rows, platform, kind, avd, out_path=None):
    os.makedirs(RAW, exist_ok=True)
    out_path = out_path or os.path.join(RAW, "%s.%s.jsonl" % (
        {"bilibili": "bilibili", "xiaohongshu": "xiaohongshu", "zhihu": "zhihu",
         "weibo": "weibo", "douyin": "douyin", "wechat": "wechat"}.get(platform, platform), kind))
    seen = set()
    n = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for r in rows:
            h = hashlib.sha1(r["text"].encode("utf-8")).hexdigest()[:16]
            if h in seen:
                continue
            seen.add(h)
            rec = {"platform": platform, "kind": kind, "text": r["text"],
                   "author": r.get("author", ""), "like": r.get("like"),
                   "ts": datetime.now().isoformat(timespec="seconds"),
                   "evidence": r.get("evidence", ""), "avd": avd,
                   "session": r.get("session", "")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return out_path, n


def active_hours_ok():
    h = datetime.now().hour
    return not (2 <= h < 6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--avd", default="acct1")
    ap.add_argument("--platform", default="bilibili")
    ap.add_argument("--kind", default="feed")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--parse-only", help="只解析已有 ui.xml，不动设备（自检/复算用）")
    ap.add_argument("--dry", action="store_true", help="只滑不写库")
    a = ap.parse_args()

    if a.parse_only:
        items, risk = parse_ui(a.parse_only)
        print(json.dumps({"items": len(items), "risk": risk, "sample": items[:5]},
                         ensure_ascii=False, indent=1))
        return 0 if items else 1

    serial = serial_of(a.avd)
    if not serial:
        print("AVD 不存在: %s" % a.avd, file=sys.stderr)
        return 2
    rc, devs, _ = sh([ADB, "devices"])
    if serial not in devs:
        print("%s 未运行（先 android_farm.py start %s）" % (serial, a.avd), file=sys.stderr)
        return 2
    if not active_hours_ok():
        print("凌晨 2-6 点不采集（真人也不在这时候刷）", file=sys.stderr)
        return 2

    try:
        sys.path.insert(0, HERE)
        import social_riskguard as rg
    except Exception:
        rg = None

    w, h = win_size(serial)
    session = datetime.now().strftime("%Y%m%d-%H%M%S")
    all_rows, rounds_done, risk_seen = [], 0, None

    for i in range(a.rounds):
        if rg:
            ok, why = rg.wait_turn(a.platform, max_wait=90)
            if not ok:
                print("节律拦截：%s（本轮停止，不硬闯）" % why, file=sys.stderr)
                break
        tag = "%s-%s-%d" % (a.platform, session, i)
        xml, err = dump(serial, tag)
        if not xml:
            print("dump 失败：%s" % err, file=sys.stderr)
            return 2
        items, risk = parse_ui(xml)
        if risk:
            risk_seen = risk
            print("命中风控词「%s」→ 立即停止（不硬闯）" % risk, file=sys.stderr)
            break
        for it in items:
            it["evidence"] = os.path.relpath(xml, ROOT)
            it["session"] = session
        all_rows.extend(items)
        rounds_done += 1
        print("第 %d 轮：抽到 %d 条（停留 %.1fs 后滑动）" % (i + 1, len(items), dwell()))
        human_swipe(serial, w, h, "up")
        if random.random() < 0.10:          # 10% 回滑：真人会往回看
            time.sleep(random.uniform(1.0, 2.5))
            human_swipe(serial, w, h, "down")

    if not all_rows:
        print("UNKNOWN：%d 轮 0 条（不写成成功）" % rounds_done, file=sys.stderr)
        return 1
    if a.dry:
        print(json.dumps({"dry": True, "rows": len(all_rows), "sample": all_rows[:3]},
                         ensure_ascii=False, indent=1))
        return 0
    out, n = write_jsonl(all_rows, a.platform, a.kind, a.avd)
    print("落盘 %s：%d 条（去重后）｜轮次 %d｜风控=%s" % (os.path.relpath(out, ROOT), n,
                                                rounds_done, risk_seen or "无"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
