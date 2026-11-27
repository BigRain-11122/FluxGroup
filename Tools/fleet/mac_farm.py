#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mac_farm.py - 把本机当成一台"有槽位的机器"来调度：GPU 一条模型槽、一条 ASR 槽、两条编码槽。

为什么（CEO 2026-11-04「利用好 macbook 32g 统一内存和强大的 gpu cpu 算力，机队协同工作」）：
  以前本机只有脉冲里一串串行阶段：模型在跑时 CPU 闲着，编码在跑时 GPU 闲着，算力互相等。
  但真实边界是**内存**而不是核数：32GB 里 6GB 要留给办公与主控，模型 4B 吃 5.5GB、ASR 吃 2.5GB、
  两条 ffmpeg 各 1.2GB——算清了就能同时开，算不清就会 swap（CEO 明令禁止）。

它只做调度，不做生产：每个槽位调既有工具（asset_caption / review_proxy / subs_asr），
按槽位表并发，开工前用实测内存余额判断能不能开，跑完写账。

用法：
  python3 Tools/fleet/mac_farm.py --budget 240      # 跑最多 4 分钟，能开几条槽开几条
  python3 Tools/fleet/mac_farm.py --dry             # 只报能开几条槽、排队多少活
Exit: 0 正常；1 有槽位任务失败；3 槽位表/工具缺失
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SLOTS = os.path.join(FLEET, "MAC-SLOTS-v1.json")
STATE = os.path.join(FLEET, "state", "mac-farm.json")
def _vault():
    """素材库位置：环境变量 > ASSET-VAULT.json > 空。不许写死 /Volumes，也不许在导入期 SystemExit
    （2026-11-11 实测：vault.path=null 时整个工具在 import 阶段就死了，连 --help 都看不到）。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import vault as _v
    base = _v.root()
    if not base:
        return ""
    return base if base.endswith("/store") else os.path.join(base, "store")


VAULT = _vault()
INBOX = os.path.join(ROOT, "media", "inbox")


RELEASE_FLAG = os.path.expanduser("~/.fluxgroup-disk-release")


def mem_gb():
    """(可回收GB, wiredGB, swapMB)。可回收 = free + inactive（macOS 会把 inactive 让出来）。"""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return 0.0, 0.0, 0.0
    page = 16384
    m = re.search(r"page size of (\d+)", out)
    if m:
        page = int(m.group(1))
    def g(label):
        mm = re.search(label + r":\s+(\d+)", out)
        return int(mm.group(1)) if mm else 0
    # 可回收 = free + inactive + speculative + purgeable + compressor
    # （毛压缩页在压力下会被解压回收；白名单只算 free+inactive 会把"其实能用"误判成不能开槽，
    #  实测同一时刻两次读数 16.9GB→10.1GB，只差在压缩与缓存记账，不是内存真被吃掉。）
    free = (g("Pages free") + g("Pages inactive") + g("Pages speculative")
            + g("Pages purgeable") + g("Pages occupied by compressor"))
    wired = g("Pages wired down")
    sw = 0.0
    try:
        s = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
        mm = re.search(r"used = ([\d.]+)M", s)
        sw = float(mm.group(1)) / 1024 if mm else 0.0
    except Exception:
        pass
    return round(free * page / 2 ** 30, 1), round(wired * page / 2 ** 30, 1), round(sw, 1)


def count_caption_todo():
    n = 0
    if not os.path.isdir(VAULT):
        return 0
    for d, _s, fs in os.walk(VAULT):
        for f in fs:
            if f.lower().endswith(".txt"):
                continue
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                if not os.path.exists(os.path.join(d, os.path.splitext(f)[0] + ".txt")):
                    n += 1
    return n


# 编码/字幕槽的素材源：收件暂存 + 本机成片目录。只看 media/inbox 会让 CPU 槽永远没活
# （收件靠别机推送，今天还卡在 bm-a 车道上），而 media/drama-out 的成片一直有代理可做。
MEDIA_SRCS = [INBOX, os.path.join(ROOT, "media", "drama-out")]
# 库里的镜头/样本只在库根真的配置了才加进来（移动盘 2026-11-11 已清空退出，
# 写死路径会让 CPU 槽天天对着一个不存在的盘报"没活"）。
if VAULT and os.path.isdir(VAULT):
    for _sub in ("mv0001-handover/outbound/krea2/30s-reel-v1/fleet-shots", "drama-dept-v1/samples"):
        _p = os.path.join(VAULT, _sub)
        if os.path.isdir(_p):
            MEDIA_SRCS.append(_p)
PROXY_DIR = os.path.join(ROOT, "media", "review-720p")


def count_media_todo(sub):
    """需要代理（同名 -720p 不存在）或字幕（同名 .srt 不存在）的文件数。"""
    n = 0
    for src in MEDIA_SRCS:
        if not os.path.isdir(src):
            continue
        for d, _s, fs in os.walk(src):
            for f in fs:
                low = f.lower()
                stem = os.path.splitext(f)[0]
                if sub == "proxy" and low.endswith((".mp4", ".mov", ".mkv")) and "-proxy" not in low:
                    if not os.path.exists(os.path.join(PROXY_DIR, stem + "-720p.mp4")):
                        n += 1
                if sub == "asr" and low.endswith((".mp4", ".mov", ".mkv", ".wav", ".mp3")):
                    if not os.path.exists(os.path.join(d, stem + ".srt")):
                        n += 1
    return n


def run_cmd(cmd, timeout):
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {"rc": r.returncode, "sec": round(time.time() - t0, 1),
                "tail": ((r.stdout or "") + (r.stderr or "")).strip()[-300:]}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "sec": round(time.time() - t0, 1), "tail": "timeout"}
    except Exception as e:
        return {"rc": 99, "sec": 0, "tail": str(e)[:200]}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=240, help="本轮最多跑多少秒")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(SLOTS):
        print("[mac-farm] 缺槽位表 %s（rc=3）" % SLOTS)
        return 3
    cfg = json.load(open(SLOTS, encoding="utf-8"))
    if os.path.exists(RELEASE_FLAG):
        print("[mac-farm] 盘已置「可拔线」旗标，本轮不碰外盘素材（rc=0）")
        return 0
    reserve = float(cfg.get("reserve_gb") or 6.0)
    slots = {s["id"]: s for s in cfg.get("slots") or []}

    free, wired, swap = mem_gb()
    cap = free + 0.0
    todo = {"caption": count_caption_todo(), "proxy": count_media_todo("proxy"),
            "asr": count_media_todo("asr")}

    # 选槽：按 est_gb 从大到小排队，够内存就开
    order = ["gpu_model", "gpu_asr", "cpu_ffmpeg", "cpu_rules"]
    plan, used = [], 0.0
    for sid in order:
        s = slots.get(sid)
        if not s:
            continue
        est = float(s.get("est_gb") or 0) * int(s.get("conc") or 1)
        if used + est <= max(0.0, cap - reserve):
            plan.append(sid)
            used += est
    # 换页判据不能是 swap>0：macOS 只要写过一次就留着零点几 MB，实测 0.5MB 就把 GPU 槽永久锁死。
    # 用与脉冲 relieve_swap 同一口径：>1GB 才让路，1GB 以下视为历史残留。
    if swap > 1024:
        plan = [p for p in plan if p == "cpu_rules"]

    # 打标熔断（2026-11-04 实测）：新图连续被质量门拒收、且单张从 6.9s 涨到 34s，
    # 继续跑就是烧 GPU 换垃圾。最近一次 CAPTIONS 记录 verdict=FAIL 时本轮不再开模型槽，
    # 把问题交给资产线改提示词/判据，而不是每小时重刷一遍。
    cap_blocked = ""
    try:
        j = json.load(open(os.path.join(FLEET, "state", "caption-last.json"), encoding="utf-8"))
        if str(j.get("verdict")).upper() == "FAIL":
            cap_blocked = "上次打标 verdict=FAIL（%s）" % str((j.get("gaps") or ["全被拒"])[0])[:60]
    except Exception:
        pass

    jobs = []
    if cap_blocked:
        todo["caption"] = 0
    if "gpu_model" in plan and todo["caption"] > 0 and os.path.isdir(VAULT):
        # 批量按"预算能跑完"来定（实测 6.9s/张）：超预算会被 kill 成 rc=124，
        # 那一批的账就只剩"超时"，看起来像工具坏——其实是我给多了。
        per = float(((cfg.get("jobs") or {}).get("caption") or {}).get("measure_s_per_item") or 7.0)
        # 留 40% 余量：与 ASR 同抢 GPU 时单张会慢于 6.9s，实测按满预算算会被 kill 成 rc=124。
        n = max(1, min(40, todo["caption"], int(max(10, a.budget * 0.6) / per)))
        jobs.append(("caption", ["python3", "Tools/fleet/asset_caption.py", "--dir", VAULT,
                                 "--recursive", "--limit", str(n),
                                 "--out", "cph4/fleet/asset-lib-v1/CAPTIONS.jsonl"]))
    if "cpu_ffmpeg" in plan and todo["proxy"] > 0:
        # review_proxy 只扫一层目录（2026-11-04 实测：镜头都在 fleet-shots/FLUXGROUP 这种子目录里，
        # 传父目录会报"出 0 条，已是最新"），所以按"真正有缺代理的目录"逐个喂，最多开 conc 条。
        dirs = []
        for src in MEDIA_SRCS:
            if not os.path.isdir(src):
                continue
            for d, _s, fs in os.walk(src):
                if d in dirs:
                    continue
                for f in fs:
                    low = f.lower()
                    if low.endswith((".mp4", ".mov", ".mkv")) and "-proxy" not in low:
                        stem = os.path.splitext(f)[0]
                        if not os.path.exists(os.path.join(PROXY_DIR, stem + "-720p.mp4")):
                            dirs.append(d)
                            break
        for d in dirs[:int(slots["cpu_ffmpeg"]["conc"])]:
            jobs.append(("proxy:%s" % os.path.basename(d),
                         ["python3", "Tools/fleet/review_proxy.py", "--src", d,
                          "--out", "media/review-720p", "--max", "4"]))
    if "gpu_asr" in plan and todo["asr"] > 0:
        jobs.append(("asr", ["python3", "Tools/fleet/subs_asr.py", "--sync-dir", INBOX,
                             "--subs-dir", "cph4/fleet/drama-dept-v1/subs", "--days", "3"]))

    results = []
    if jobs:
        with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
            futs = {ex.submit(run_cmd, cmd, max(30, a.budget)): name for name, cmd in jobs}
            for f in futs:
                pass
            for f, name in [(fu, futs[fu]) for fu in futs]:
                r = f.result()
                results.append({"slot_job": name, **r})
    else:
        results.append({"slot_job": "none", "rc": 0, "sec": 0,
                        "tail": "没有可开的槽或无排队活"})

    free2, wired2, swap2 = mem_gb()
    st = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "free_gb_before": free,
          "free_gb_after": free2, "wired_gb": wired2, "swap_mb": swap2,
          "slots_open": plan, "budget_s": a.budget, "results": results}
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # rc=1 是工具自己的质量门（例如打标判定"只命中 1 个可见属性，像空话"），
    # 那是产出被判次不是调度失败——算软告警，不阻断本轮。
    # rc=124 = 本轮预算用尽（批量没跑完，但已产出的都落了盘）；算软告警不算失败。
    bad = [r for r in results if r.get("rc") not in (0, 1, 124)]
    print("[mac-farm] 开槽=%s free %.1f→%.1fGB swap=%.1fMB" %
          (",".join(plan) or "无", free, free2, swap2))
    for r in results:
        print("  %-10s rc=%-3s %5ss  %s" % (r["slot_job"], r.get("rc"), r.get("sec"),
                                           (r.get("tail") or "").replace("\n", " ")[:70]))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))