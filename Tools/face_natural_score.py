# -*- coding: utf-8 -*-
"""face_natural_score.py — 用大众检索联想词给每个人打「科技脸嫌疑分」。

CEO 2026-11-18：「是不是科技脸，去看粉丝和用户的评论不就知道了」。
本机拿不到需要登录的评论区，但搜索引擎的下拉联想词是同一件事的代理：
它是**大众真实搜索行为的聚合**——有人反复搜「XX 整容失败」，才会有这条联想。

关键区分（负控实测 2026-11-18）：
  韩安冉 → 「整容失败」「整容磨骨后续」       ← 手术实锤
  鞠婧祎 → 「整容后像鬼一样」                 ← 强烈负面
  汤唯   → 「整容前后的图片」「整容前后对比」 ← 只是八卦对比
  舒淇   → 「整容后变化」                     ← 同上
所以判据不能用「有没有整容这个词」（人人都有传闻），只能用**措辞是否构成实锤**。

输出：每人一个嫌疑分 + 命中的证据词，供人眼裁量。分数只作排序，不作最终裁定。

用法：
  py Tools/face_natural_score.py                       # 全部名册
  py Tools/face_natural_score.py --names 汤唯,韩安冉
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
POOLS = [
    os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-natural-v1.json"),
    os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-distinct-v1.json"),
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36"}

# 实锤词：出现即高度指向"动过刀/重度医美"，权重 5
# 注意「医美」单独不用——实测它把「医美简历范文」「医美项目有哪些」这类行业内容全拉进来，
# 必须与"失败/事故/痕迹/后遗症"组合才算实锤。
HARD = ("整容失败", "医美失败", "医美事故", "医美痕迹", "医美过度", "整容后遗症",
        "磨骨", "削骨", "后遗症", "像鬼", "僵硬", "崩坏", "毁容", "不自然",
        "脸塌", "填充过度", "假体", "膨体", "线雕", "三庭五眼不对",
        "变怪", "僵硬感", "硅胶", "塑料感", "发面", "蜡像", "网红脸")
# 争议词：只是八卦/对比，权重 1
SOFT = ("前后对比", "对比照", "变化", "怀疑", "传闻", "辟谣", "否认", "疑似")
# 自然向词：出现反而是正信号，权重 -0.5
NATURAL = ("素颜", "自然", "灵气", "清冷", "气质", "真实", "耐看", "扛得住", "原生")

# 疑问句不算实锤（"XX做过医美没有""XX整容了吗"只是围观，不是结论）
QUESTION = ("吗", "呢", "没有", "是不是", "如何", "怎么", "什么", "多少钱", "价格")
# 撞名/串词噪声：名字被当成别的词（本田翼→本田汽车、简嫚书→医美简历、朴素丹→朴素）
NOISE = ("简历", "范文", "SUV", "发动机", "汽车", "项目有哪些", "多少钱", "加盟", "培训",
         "招聘", "价格表", "医院", "诊所", "仪器", "吸气", "涡轮", "排量", "马力")
# 否定语境：含这些词的短语不能当"自然向"正信号（实测"白鹿气质不好/气质俗气"被算成了加分）
NEGATION = ("不好", "俗气", "差", "土", "崩", "不美", "难看", "没有一个", "比不上")

PROBES = ["整容", "医美", "颜值", "假脸", "脸型"]
GOOD = ["素颜", "气质", "自然"]


def baidu_sug(q, timeout=12):
    try:
        u = "https://suggestion.baidu.com/su?" + urllib.parse.urlencode({"wd": q})
        t = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout).read().decode("gbk", "replace")
        m = re.search(r"s:\[(.*?)\]", t, re.S)
        return re.findall(r'"(.*?)"', m.group(1)) if m else []
    except Exception:
        return []


def score(name):
    words_bad, words_good, hit_hard, hit_soft = [], [], [], []
    for p in PROBES:
        for w in baidu_sug(name + p):
            # 噪声与疑问句先剔掉，再判极性——否则"医美简历范文""本田自然吸气"都会计分
            if any(n in w for n in NOISE):
                continue
            if any(q in w for q in QUESTION):
                continue
            for h in HARD:
                if h in w:
                    hit_hard.append(w)
                    break
            for s in SOFT:
                if s in w:
                    hit_soft.append(w)
                    break
        time.sleep(0.25)
    for p in GOOD:
        for w in baidu_sug(name + p):
            if any(n in w for n in NOISE) or any(q in w for q in QUESTION):
                continue
            if any(x in w for x in NEGATION):
                continue
            for n in NATURAL:
                if n in w:
                    words_good.append(w)
                    break
        time.sleep(0.25)
    hard = len(set(hit_hard))
    soft = len(set(hit_soft))
    good = len(set(words_good))
    return {
        "name": name,
        "hard": hard, "soft": soft, "good": good,
        "score": hard * 5 + soft * 1 - good * 0.5,
        "evidence": sorted(set(hit_hard))[:4],
        "positive": sorted(set(words_good))[:3],
    }


def roster():
    names = []
    for p in POOLS:
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        for fam in d.get("families") or []:
            if fam.get("id") == "kr":
                continue
            names.extend(fam.get("internal_index_only") or [])
    out, seen = [], set()
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default="")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    names = [x.strip() for x in a.names.split(",") if x.strip()] if a.names else roster()
    if a.limit:
        names = names[:a.limit]

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("评分 %d 人（越低越自然）\n" % len(names))
    rows = []
    for i, nm in enumerate(names, 1):
        r = score(nm)
        rows.append(r)
        print("[%d/%d] %-12s 分=%2d (实锤%d 争议%d 自然%d) %s"
              % (i, len(names), nm, r["score"], r["hard"], r["soft"], r["good"],
                 ",".join(r["evidence"][:2])), flush=True)

    out = os.path.join(ROOT, "media", "faces", "_natural-score.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n=== 嫌疑最高（建议剔除或换人）===")
    for r in sorted(rows, key=lambda x: -x["score"])[:12]:
        print("  %-12s 分=%2d  %s" % (r["name"], r["score"], ",".join(r["evidence"][:3])))
    print("\n=== 最干净 ===")
    for r in sorted(rows, key=lambda x: x["score"])[:12]:
        print("  %-12s 分=%2d  %s" % (r["name"], r["score"], ",".join(r["positive"][:2])))
    print("\n明细 → %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
