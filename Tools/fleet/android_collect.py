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

# 页面体检：这些词说明还停在登录页/弹窗上，抽到的都是界面文案不是内容
LOGIN_WORDS = ("账号密码登录", "手机号登录", "请输入手机号", "手机短信登录", "请输入密码")
RISK_WORDS = ("验证码", "安全验证", "请完成验证", "行为异常", "操作频繁", "captcha", "CAPTCHA",
              "人机验证", "滑动验证", "账号异常", "登录后查看")

# 界面骨架词：app 的导航/分区名，不是用户内容。
# 实锚 2026-11-23：首页 dump 抽到「直播/推荐/热门/动画/影视/新征程/首页/关注/会员购/我的」当语料。
CHROME_WORDS = frozenset((
    "推荐", "直播", "热门", "动画", "影视", "新征程", "番剧", "游戏中心", "会员购", "首页",
    "关注", "动态", "我的", "频道", "搜索", "发布", "追番", "纪录片", "电影", "电视剧",
    "综艺", "搞笑", "音乐", "舞蹈", "游戏", "知识", "科技", "运动", "汽车", "生活", "美食",
    "动物圈", "鬼畜", "时尚", "资讯", "娱乐", "赛事", "课程", "更多", "全部", "排行榜",
    "稍后再看", "历史", "收藏", "消息", "设置", "取消", "确定", "分享", "评论", "弹幕",
))
# 统计行噪声："295.1万" / "5163" / "29:44" / "-"
NUM_RE = re.compile(r"^[\d.]+\s*[万亿]?$")
DUR_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


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
    """按卡片结构抽内容；返回 (items, risk_hit)

    为什么不再"把所有 text 都收"（2026-11-23 实锚）：首页 82 条里混进「直播/推荐/热门」
    和「295.1万」「29:44」，这类界面骨架喂不进语料。

    真实布局（两列卡片）：统计行(播放/弹幕/时长) 在标题上方约 40-160px，作者在标题下方
    约 60-200px，同一列。所以判据是：**标题必须配得到统计行**才算一条内容，
    配不到的（顶栏横幅、导航词）自然被排除。
    """
    with open(xml_path, encoding="utf-8") as f:
        s = f.read()
    risk = next((w for w in RISK_WORDS if w in s), None)

    nodes = []
    for m in re.finditer(r'<node[^>]*text="([^"]*)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s):
        txt = m.group(1).strip()
        if not txt:
            continue
        x0, y0, x1, y1 = map(int, m.group(2, 3, 4, 5))
        nodes.append({"text": txt, "x0": x0, "y0": y0, "x1": x1, "cx": (x0 + x1) / 2.0})
    if not nodes:
        return [], risk

    w = max(n["x1"] for n in nodes) or 1080

    def is_num(n):
        t = n["text"]
        return bool(NUM_RE.match(t) or DUR_RE.match(t) or t == "-")

    def is_chrome(n):
        return re.sub(r"\s+", "", n["text"]) in CHROME_WORDS

    def col(n):
        return 0 if n["cx"] < w / 2.0 else 1

    candidates = [n for n in nodes if not is_num(n) and not is_chrome(n) and len(n["text"]) >= 4]

    items = []
    for t in candidates:
        if len(t["text"]) < 8:          # 短串多半是作者名/标签，标题会再长
            continue
        c = col(t)
        stats = [n for n in nodes
                 if is_num(n) and col(n) == c and -160 <= n["y0"] - t["y0"] <= -40]
        if not stats:                   # 配不到统计行 = 不是卡片（横幅/导航/标题外文本）
            continue
        views = next((n["text"] for n in stats if not DUR_RE.match(n["text"])), "")
        dur = next((n["text"] for n in stats if DUR_RE.match(n["text"])), "")
        author = next((n["text"] for n in candidates
                       if col(n) == c and 60 <= n["y0"] - t["y0"] <= 200 and len(n["text"]) <= 12), "")
        items.append({"text": t["text"], "author": author, "like": views or None,
                      "duration": dur, "y": t["y0"]})

    if not items:
        # 兜底：评论/详情页是竖排长文本，没有卡片统计行；只留足够长的，去掉骨架词
        items = [{"text": n["text"], "author": "", "like": None, "y": n["y0"]}
                 for n in candidates if len(n["text"]) >= 12]
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
    ap.add_argument("--ensure-login", action="store_true",
                    help="采集前先确保登录态：不是登录态就调 android_login.py（凭据取本地文件）")
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

    if a.ensure_login:
        rc, out, err = sh(["python3", os.path.join(HERE, "android_login.py"),
                           "--avd", a.avd], 300)
        tail = (out or err).strip().splitlines()[-1:] or [""]
        print("登录检查：%s" % tail[0][:100])
        if rc != 0:
            print("未就绪登录态（rc=%d），本轮不采集" % rc, file=sys.stderr)
            return rc

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
        if any(w in open(xml, encoding="utf-8").read() for w in LOGIN_WORDS):
            print("页面体检失败：当前在登录页（抽到的会是界面文案，不写库）。"
                  "先完成登录或退到内容页再采。", file=sys.stderr)
            return 3
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
