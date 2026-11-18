# -*- coding: utf-8 -*-
"""face_source_collect.py — 自动采集单人面孔训练素材（私有实验用）。

为什么有它：CEO 令「训练素材是你去解决，你自己去专业网站或者别的地方去找」。
手工存图不现实，本脚本把「搜 → 下 → 过闸 → 分拣」串成一条命令。

流程：
  1) 多组关键词（本名 / 本名+年代 / 本名+年轻 / 本名+写真…）翻页取候选直链
  2) 下载（限速、限大小、解码校验，坏图直接丢）
  3) 过 face_lora_prep 的素材闸（分辨率/清晰度/人脸占比/去重）
  4) 可用件进 keep/，废件进 reject/ 并留原因

用法：
  python Tools/face_source_collect.py collect --person 徐若瑄 --want 160 --out D:\\faces\\vivian
  python Tools/face_source_collect.py collect --person 徐若瑄 --terms "1990s,年轻,写真,早期" \
      --pages 8 --min-side 600 --out D:\\faces\\vivian
退出码：0 有可用件 / 1 无可用件 / 2 参数错
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_lora_prep as GATE  # noqa: E402

BING = "https://cn.bing.com/images/async"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
      "Referer": "https://cn.bing.com/"}
MURL = re.compile(r"murl&quot;:&quot;(.*?)&quot;")
OK_EXT = (".jpg", ".jpeg", ".png", ".webp")


SO360 = "https://image.so.com/j"

# 年代过滤复用 face_lora_prep.era_tag：判据单点定义，采集端与挑选端不许各写一套
ERA_KEEP = ("young",)
ERA_DROP = ("recent", "drop_other")


def fetch(url, timeout=25, referer=None):
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search_360(query, pages, rn=60, gap=1.2):
    """360 图片：JSON 接口、不限流、总量大（实测单人 800+ 条），主力源。

    返回 [(url, title)]：title 用于年代过滤，是判断「年轻时候」的硬证据。
    """
    out = []
    for p in range(1, pages + 1):
        q = {"q": query, "pn": p * rn, "rn": rn, "src": "srp"}
        try:
            data = json.loads(fetch(f"{SO360}?{urllib.parse.urlencode(q)}",
                                     referer="https://image.so.com/"))
        except Exception as e:
            print(f"  [warn] 360 第 {p} 页失败: {e}")
            continue
        for it in data.get("list") or []:
            u = it.get("img") or it.get("thumb")
            if u:
                out.append((u, it.get("title") or it.get("name") or ""))
        time.sleep(gap)
    seen, uniq = set(), []
    for u, t in out:
        if u not in seen:
            seen.add(u)
            uniq.append((u, t))
    return uniq


def search_links(query, pages, step=35, portrait=True, gap=2.5):
    """翻页取原图直链。portrait=必应人像过滤；gap=反限流间隔，空页重试一次。"""
    out = []
    for p in range(pages):
        q = {"q": query, "first": p * step, "count": step}
        if portrait:
            q["qft"] = "+filterui:face-portrait"
        url = f"{BING}?{urllib.parse.urlencode(q)}"
        links = []
        for attempt in range(2):
            try:
                html = fetch(url).decode("utf-8", "replace")
                links = [u.replace("\\/", "/") for u in MURL.findall(html)]
            except Exception as e:
                if attempt == 0:
                    time.sleep(5)
                    continue
                print(f"  [warn] {query} 第 {p + 1} 页失败: {e}")
            if links:
                break
            time.sleep(5)          # 空页多半是限流，等一会儿再来一次
        out.extend(l for l in links if l.lower().split("?")[0].endswith(OK_EXT))
        time.sleep(gap)
    seen, uniq = set(), []
    for l in out:
        if l not in seen:
            seen.add(l)
            uniq.append(l)
    return uniq


def download_all(links, raw_dir, target_usable, min_side, person="", max_mb=12, max_try=600):
    """下到「过闸可用」张数达标为止——缺口在采集端补，别指望训练端救。

    links 为 [(url, title)]；title 命中近年词直接跳过，命中年代锚优先处理。
    """
    os.makedirs(raw_dir, exist_ok=True)
    # 年代锚命中的排前面：池子有限时先下"确定年轻"的
    links = sorted(links, key=lambda ut: {v: i for i, v in enumerate(
        ("young", "unknown", "recent", "drop_other"))}[GATE.era_tag(ut[1], person)])
    got, usable, hashes, tries = 0, 0, set(), 0
    dropped_era = 0
    titles: dict[str, str] = {}
    for url, title in links:
        if usable >= target_usable or tries >= max_try:
            break
        if GATE.era_tag(title, person) in ERA_DROP:
            dropped_era += 1
            continue
        tries += 1
        try:
            data = fetch(url, timeout=20)
        except Exception:
            continue
        if len(data) < 20 * 1024 or len(data) > max_mb * 1024 * 1024:
            continue
        h = hashlib.sha1(data).hexdigest()
        if h in hashes:
            continue
        ext = ".jpg"
        for e in OK_EXT:
            if url.lower().split("?")[0].endswith(e):
                ext = e
        # 用内容哈希命名：重跑同一人不会覆盖已有文件，跨轮次天然去重
        path = os.path.join(raw_dir, f"{h[:12]}{ext}")
        with open(path, "wb") as f:
            f.write(data)
        img = GATE.cv2.imread(path)
        if img is None or min(img.shape[:2]) < min_side:
            os.remove(path)
            continue
        titles[os.path.basename(path)] = title
        hashes.add(h)
        got += 1
        if GATE.evaluate(path)["verdict"] != "REJECT":
            usable += 1
            print(f"  可用 {usable}/{target_usable}（已下 {got}）")
        time.sleep(0.3)
    if dropped_era:
        print(f"  跳过近年图 {dropped_era} 条（标题含 2020+/近照/现状等）")
    # 标题随图落盘：挑人阶段要按年代排序（CEO 要求「都要年轻时候的」），
    # 标题年份是硬证据，脸龄模型没有可靠阈值可用。
    if titles:
        side = os.path.join(raw_dir, "_titles.json")
        old = {}
        if os.path.isfile(side):
            try:
                with open(side, encoding="utf-8") as f:
                    old = json.load(f)
            except json.JSONDecodeError:
                old = {}
        old.update(titles)
        with open(side, "w", encoding="utf-8") as f:
            json.dump(old, f, ensure_ascii=False, indent=1)
    return got, usable


def split(raw_dir, out_dir):
    """按素材闸分拣：可用进 keep/，废件进 reject/。"""
    rep = GATE.scan_dir(raw_dir)
    keep = os.path.join(out_dir, "keep")
    rej = os.path.join(out_dir, "reject")
    os.makedirs(keep, exist_ok=True)
    os.makedirs(rej, exist_ok=True)
    used = 0
    for r in rep["rows"]:
        dst_dir = rej if r["verdict"] == "REJECT" else keep
        dst = os.path.join(dst_dir, os.path.basename(r["path"]))
        if os.path.abspath(dst_dir) != os.path.abspath(raw_dir):
            shutil.copy2(r["path"], dst)
        if r["verdict"] != "REJECT":
            used += 1
    return rep["counts"], used


def main(argv=None):
    ap = argparse.ArgumentParser(description="单人面孔训练素材自动采集")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("collect")
    s.add_argument("--person", required=True)
    s.add_argument("--alias", default="", help="别名/英文名/拼音，逗号分隔——扩池主力")
    s.add_argument("--terms", default="年轻,年轻时,早期,出道,出道作品,成名作,处女作,"
                                      "少女时期,学生时期,校服,素颜,清纯,初恋脸,少女感,"
                                      "18岁,20岁,22岁,写真,写真集,旧照,老照片,"
                                      "2000年代,90年代,剧照,电影剧照,高清,脸部,"
                                      # 2026-11-17 加：写真/刊物类定向词。实测百度/必应/搜狗/豆瓣图册全被挡，
                                      # 360 是唯一活着的源，只能靠"多角度词"扩大覆盖面而不是加页数。
                                      "杂志封面,杂志写真,画报,宣传照,广告照,海报,写真拍摄,"
                                      "写真花絮,电视剧剧照,采访照,记者会,发布会,红毯,"
                                      "清纯写真,气质,侧脸,正脸,近照old,九零年代")
    s.add_argument("--pages", type=int, default=4)
    s.add_argument("--want-links", type=int, default=400, dest="want_links")
    s.add_argument("--target", type=int, default=45)
    s.add_argument("--min-side", type=int, default=600)
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    out = os.path.abspath(a.out)
    raw = os.path.join(out, "raw")
    terms = [t.strip() for t in a.terms.split(",") if t.strip()]
    names = [a.person] + [x.strip() for x in a.alias.split(",") if x.strip()]
    queries, seen_q = [], set()
    for n in names:
        for q in [n, f"{n} 年轻", n + " young"] + [f"{n} {t}" for t in terms]:
            if q not in seen_q:
                seen_q.add(q)
                queries.append(q)

    links = []
    for q in queries:
        got = search_360(q, a.pages)
        print(f"[360] 「{q}」→ {len(got)} 条")
        links.extend(got)
        if len(links) >= a.want_links:
            break
    if len(links) < 60:
        print("360 量不足，回落必应…")
        for q in queries[:4]:
            got = search_links(q, 2)
            print(f"[bing] 「{q}」→ {len(got)} 条")
            links.extend([(u, "") for u in got])   # 必应不带标题，年代判为 unknown
    seen, uniq = set(), []
    for u, t in links:
        if u not in seen:
            seen.add(u)
            uniq.append((u, t))
    known = sum(1 for _, t in uniq if GATE.era_tag(t, a.person) in ERA_KEEP)
    drops = sum(1 for _, t in uniq if GATE.era_tag(t, a.person) in ERA_DROP)
    print(f"去重后候选 {len(uniq)} 条（确定年轻 {known} · 近年/他人已排除 {drops}），"
          f"开始下载（目标可用 {a.target} 张）…")

    got, usable = download_all(uniq, raw, a.target, a.min_side, a.person)
    print(f"下载完成：落盘 {got} 张 · 过闸可用 {usable}")

    counts, usable = split(raw, out)
    print(f"过闸：总 {counts['total']} · PASS {counts['pass']} · WARN {counts['warn']} "
          f"· REJECT {counts['reject']} · 可用 {usable}")
    if usable < 20:
        print(f"[FAIL] 可用 {usable} 张 < 20——加 --pages / 换关键词 / 准入门槛放宽前先补量")
        return 1
    print(f"[OK] 可用 {usable} 张 → {os.path.join(out, 'keep')}")
    if usable < 40:
        print(f"[WARN] 少于建议值 40，训出来容易漂，建议再采一轮")
    return 0


if __name__ == "__main__":
    sys.exit(main())
