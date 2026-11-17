#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_sweep.py — 训练语料批量补货（只读公开接口，走登录态 profile 取 cookie）。

为什么单独一个工具：24h 学习循环每 20 分钟只抽 1 条视频、3 页评论，一天撑死几百句；
而训练门槛是自有 ≥2000 条 use=train。补货要用"一次性成批、但节奏仍是真人"的方式，
且必须与学习循环互斥（同一 profile 两开必 ProcessSingleton）。

口径（硬约束，违反即数据不可用）：
  - 只读：view / x/v2/reply / 弹幕 list.so 三个公开接口，不点赞不关注不评论不发送。
  - 节奏：每个视频之间过 social_riskguard.wait_turn（20-60s 抖动 + 会话休息），不连射。
  - 落盘：raw/<platform>.<kind>.jsonl 追加，字段 text 供 human_corpus.py --from-dir 清洗。
  - 口径：弹幕只留"像人话"的（≥4 字符、含中文或字母、非纯重复刷屏），并且单视频设上限。

用法：
  # 1) 先停学习循环（同一 profile 不能两开）
  launchctl bootout gui/$(id -u)/com.fluxgroup.sociallearn
  # 2) 补货
  python3 Tools/fleet/social_sweep.py --videos 8 --comment-pages 8
  # 3) 重新装载
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.fluxgroup.sociallearn.plist
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SOURCES = os.path.join(SOCIAL, "SOURCES-v1.json")
STATE = os.path.join(ROOT, ".codely-cli", "state")
CJK = re.compile(r"[\u4e00-\u9fff]")
WORDY = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]")

UA_REFERER = {"Referer": "https://www.bilibili.com/", "User-Agent": "Mozilla/5.0"}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def norm(text):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return t[:300]


def danmaku_ok(t, min_len=4):
    if len(t) < min_len:
        return False
    if not WORDY.search(t):
        return False
    if not CJK.search(t) and len(t) < 8:      # 纯字母短串多半是打卡/编号，不是人话
        return False
    if len(set(t)) <= 2:                      # "666666" "哈哈哈哈哈" 这类刷屏
        return False
    return True


def get_json(ctx, url, tries=2):
    for i in range(tries):
        try:
            r = ctx.request.get(url, headers=UA_REFERER, timeout=25000)
            if r.status == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(2 + i * 3)
    return None


def get_text(ctx, url, tries=2):
    for i in range(tries):
        try:
            r = ctx.request.get(url, headers=UA_REFERER, timeout=30000)
            if r.status == 200:
                return r.text()
        except Exception:
            pass
        time.sleep(2 + i * 3)
    return None


def bv_id(url):
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    return m.group(1) if m else None


def video_meta(ctx, bvid):
    js = get_json(ctx, "https://api.bilibili.com/x/web-interface/view?bvid=%s" % bvid)
    if not js or js.get("code") != 0:
        return None, "view code=%s" % (js or {}).get("code")
    d = js.get("data") or {}
    return {"aid": d.get("aid"), "cid": d.get("cid"), "title": d.get("title") or "",
            "duration": d.get("duration") or 0,
            "reply": (d.get("stat") or {}).get("reply")}, ""


def walk_replies(replies, out):
    """v2/reply 的每条可能自带几条子回复，一起收（都是真人写的）。"""
    for it in replies or []:
        t = norm((it.get("content") or {}).get("message"))
        if t:
            out.append({"text": t, "author": (it.get("member") or {}).get("uname") or "",
                        "rpid": str(it.get("rpid") or ""), "like": it.get("like")})
        for sub in (it.get("replies") or []):
            st = norm((sub.get("content") or {}).get("message"))
            if st:
                out.append({"text": st,
                            "author": (sub.get("member") or {}).get("uname") or "",
                            "rpid": str(sub.get("rpid") or ""), "like": sub.get("like")})


def fetch_comments(ctx, aid, pages=8):
    rows = []
    for pn in range(1, pages + 1):
        js = get_json(ctx, "https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=%d&ps=20&sort=2"
                      % (aid, pn))
        if not js or js.get("code") != 0:
            break
        data = js.get("data") or {}
        walk_replies(data.get("replies"), rows)
        if pn == 1:
            walk_replies(data.get("top_replies"), rows)
        if not (data.get("replies") or []):
            break
        time.sleep(random.uniform(1.5, 4.0))       # 页间留间隔
    return rows


def _varint(b, i):
    r = s = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7F) << s
        s += 7
        if not x & 0x80:
            return r, i


def _pb_fields(b):
    """最小 protobuf 走字段器（只解我们需要的两层，不引依赖）。"""
    i, n = 0, len(b)
    while i < n:
        k, i = _varint(b, i)
        f, wt = k >> 3, k & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 2:
            ln, i = _varint(b, i)
            v = b[i:i + ln]
            i += ln
        elif wt == 5:
            v = b[i:i + 4]
            i += 4
        elif wt == 1:
            v = b[i:i + 8]
            i += 8
        else:
            return
        yield f, v


def fetch_danmaku(ctx, aid, cid, duration=0, cap=4000):
    """弹幕走 /x/v2/dm/web/seg.so（protobuf，字段 1=DanmakuElem、其中字段 7=正文）。

    为什么不走 XML：list.so 与 comment.bilibili.com/*.xml 都返回 raw deflate，
    Playwright 的 APIRequestContext 解不开（实锚 "failed to decompress 'deflate'"），
    加 Accept-Encoding: identity 也照旧——不是我们的 header 能修的。
    """
    import math
    segs = max(1, int(math.ceil((duration or 360) / 360.0))) + 1
    out, seen, raw_n = [], set(), 0
    for idx in range(1, segs + 1):
        u = ("https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid=%s&pid=%s&segment_index=%d"
             % (cid, aid, idx))
        try:
            r = ctx.request.get(u, headers=UA_REFERER, timeout=25000)
        except Exception:
            break
        if r.status != 200:
            break
        body = r.body()
        if not body:
            break
        got = []
        for f, v in _pb_fields(body):
            if f != 1:
                continue
            for f2, v2 in _pb_fields(v):
                if f2 == 7:
                    got.append(v2.decode("utf-8", "replace"))
        if not got:
            break
        raw_n += len(got)
        for t in got:
            t = norm(t)
            if not danmaku_ok(t):
                continue
            h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            if h in seen:
                continue
            seen.add(h)
            out.append({"text": t})
            if len(out) >= cap:
                break
        time.sleep(random.uniform(1.0, 2.5))
        if len(out) >= cap:
            break
    return out, "原始 %d 条 → 像人话 %d 条" % (raw_n, len(out))


def append_rows(path, rows, extra):
    if not rows:
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    seen = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                try:
                    seen.add(json.loads(line).get("h") or "")
                except Exception:
                    pass
    n = 0
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            t = norm(r.get("text"))
            if not t:
                continue
            h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            if h in seen:
                continue
            seen.add(h)
            rec = dict(r, text=t, h=h, ts=_now())
            rec.update(extra)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def urls_from_sources():
    try:
        src = json.load(open(SOURCES, encoding="utf-8"))
        return [u for u in (src.get("platforms", {}).get("bilibili", {}).get("urls") or []) if u]
    except Exception:
        return []


def self_test():
    """离线判据：弹幕筛选 + protobuf 解析。不联网，任何一条不过就是工具坏了。"""
    cases = []
    cases.append(("短弹幕丢弃", not danmaku_ok("配啊")))
    cases.append(("纯数字丢弃", not danmaku_ok("2333333")))
    cases.append(("纯刷屏丢弃", not danmaku_ok("哈哈哈哈")))
    cases.append(("弹幕正文保留", danmaku_ok("这段转场真的顶")))
    cases.append(("空白归一", norm("  你好\n 世界 ") == "你好 世界"))

    # 造一条合法 DanmakuElem：field7(正文) = "测试弹幕啊"
    body = "测试弹幕啊".encode("utf-8")
    elem = bytes([0x3A, len(body)]) + body
    msg = bytes([0x0A, len(elem)]) + elem
    got = []
    for f, v in _pb_fields(msg):
        if f != 1:
            continue
        for f2, v2 in _pb_fields(v):
            if f2 == 7:
                got.append(v2.decode("utf-8"))
    cases.append(("protobuf 取正文", got == ["测试弹幕啊"]))

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--videos", type=int, default=8, help="本次最多扫几个视频")
    ap.add_argument("--comment-pages", type=int, default=8, help="每个视频最多拉几页评论（20/页）")
    ap.add_argument("--no-danmaku", action="store_true")
    ap.add_argument("--out", default=os.path.join(SOCIAL, "raw"))
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--url", action="append", default=None, help="指定视频（可多次）")
    ap.add_argument("--sort-by-reply", action="store_true",
                    help="先按评论数倒序再采（爆火视频优先，时间花在油水最大的地方）")
    ap.add_argument("--min-reply", type=int, default=0, help="评论数低于此值的视频跳过")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    # 互斥：学习循环还在跑就拒绝（同 profile 两开必失败，且节奏叠加会被判机械）
    if os.path.exists(os.path.join(STATE, "SOCIAL-LEARN-PAUSED")):
        pass
    elif os.environ.get("SOCIAL_SWEEP_FORCE") != "1":
        import subprocess
        try:
            out = subprocess.run(["pgrep", "-f", "social_learn.py"], capture_output=True,
                                 text=True).stdout.strip()
        except Exception:
            out = ""
        if out:
            print("[sweep] 学习循环还在跑（pid %s）。先停：launchctl bootout gui/$(id -u)/com.fluxgroup.sociallearn"
                  % out.replace("\n", ","))
            return 2

    sys.path.insert(0, HERE)
    import social_riskguard as guard
    import social_collect as sc

    urls = a.url or urls_from_sources()
    urls = [u for u in urls if bv_id(u)]
    random.shuffle(urls)
    if not urls:
        print("[sweep] 没有可用视频源（SOURCES-v1.json 的 bilibili.urls）")
        return 2

    from playwright.sync_api import sync_playwright
    stat = {"videos": 0, "comments": 0, "comments_new": 0, "danmaku": 0, "danmaku_new": 0,
            "skipped": 0}
    done = {}
    cpath = os.path.join(a.out, "bilibili.comment.jsonl")
    dpath = os.path.join(a.out, "bilibili.danmaku.jsonl")
    if os.path.exists(cpath):
        for line in open(cpath, encoding="utf-8"):
            try:
                th = json.loads(line).get("thread") or ""
            except Exception:
                continue
            if th:
                done[th] = done.get(th, 0) + 1
    # 只跳过"已经挖到本次深度"的视频；浅抽过的（比如早期 3 页）要再挖一遍，
    # 否则 raw 里那批 60 条的视频永远停在 60 条。
    depth = max(40, int(20 * a.comment_pages * 0.6))

    with sync_playwright() as p:
        ctx = sc._launch(p, headed=a.headed, platform="bilibili")
        try:
            # 评论数倒序：爆火视频一条能出几百上千条评论，同样的时间先吃油水大的。
            if a.sort_by_reply or a.min_reply:
                scored = []
                for u in urls:
                    meta, _ = video_meta(ctx, bv_id(u))
                    if not meta:
                        continue
                    n = meta.get("reply") or 0
                    if n >= a.min_reply:
                        scored.append((n, u))
                    time.sleep(random.uniform(0.3, 0.8))
                scored.sort(reverse=True)
                urls = [u for _n, u in scored]
                print("[sweep] 按评论数排序取前 %d：%s"
                      % (len(urls[:a.videos]), ", ".join("%d" % n for n, _ in scored[:6])))
            for url in urls:
                if stat["videos"] >= a.videos:
                    break
                if done.get(url, 0) >= depth:
                    stat["skipped"] += 1
                    continue
                ok, why = guard.wait_turn("bilibili", max_wait=180)
                if not ok:
                    print("[sweep] 风控闸要求停下：%s" % why)
                    break
                bvid = bv_id(url)
                meta, why2 = video_meta(ctx, bvid)
                if not meta:
                    print("[sweep] %s 元信息取不到（%s），跳过" % (bvid, why2))
                    stat["skipped"] += 1
                    continue
                rows = fetch_comments(ctx, meta["aid"], pages=a.comment_pages)
                newc = append_rows(cpath, rows, {"platform": "bilibili", "kind": "comment",
                                                 "thread": url, "source": "api_v2_reply"})
                stat["comments"] += len(rows)
                stat["comments_new"] += newc
                dm, dmnote = ([], "跳过") if a.no_danmaku else fetch_danmaku(
                    ctx, meta["aid"], meta["cid"], duration=meta.get("duration") or 0)
                newd = append_rows(dpath, dm, {"platform": "bilibili", "kind": "danmaku",
                                               "thread": url, "source": "dm_list_so"})
                stat["danmaku"] += len(dm)
                stat["danmaku_new"] += newd
                stat["videos"] += 1
                guard.note("bilibili", "ok", "sweep %s c=%d d=%d" % (bvid, newc, newd))
                print("[sweep] %s %s | 评论 %d(新%d) 弹幕 %d(新%d) %s | 累计 评论%d 弹幕%d"
                      % (bvid, (meta["title"] or "")[:18], len(rows), newc, len(dm), newd,
                         dmnote, stat["comments_new"], stat["danmaku_new"]), flush=True)
        finally:
            try:
                ctx.close()
            except Exception:
                pass

    print("[sweep] 完成：视频 %d（跳过 %d）评论新 %d / 弹幕新 %d → %s"
          % (stat["videos"], stat["skipped"], stat["comments_new"], stat["danmaku_new"], a.out))
    print("[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
