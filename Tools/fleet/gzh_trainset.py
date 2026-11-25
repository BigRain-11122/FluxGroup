#!/usr/bin/env python3
"""公众号训练集构建器：把 ARTICLES.jsonl 拆成四个任务的数据集，并机检语料门槛。

为什么要单独一个工具：`GZH-TRAIN-SPEC-v1.md` 定了四任务（标题/开篇/骨架/收尾）
和三条语料门槛（200 篇 / 同作者≥10 / ≥5 作者），但**没有任何代码把语料变成训练集**
（状态一直是 train_rows: 0）。结果就是：语料够了那天，还要再卡一轮做数据工程。

这个工具分两件事，故意分开：
  · `--status`  只报告门槛与语料构成，不写文件；
  · `--build`   把现有语料拆成四任务数据集（**不训练**，训练仍由门槛把关）。

**门槛没过也允许 --build**：数据集先备好，等语料到位直接开训。
但门槛结果会写进 manifest，`train_ready=false`，防止有人拿 19 篇的集子去训。

用法：
  gzh_trainset.py --status
  gzh_trainset.py --build
  gzh_trainset.py --self-test
退出码：0 成功 / 1 有 FAIL / 4 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics as st
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "ARTICLES.jsonl")
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "trainset")
MANIFEST = os.path.join(OUT, "MANIFEST.json")

# 语料门槛（GZH-TRAIN-SPEC-v1.md §三，改这里就是改标准，别在别处硬编码）
GATE_TOTAL = 200        # 真稿总篇数
GATE_PER_AUTHOR = 10    # 单个作者至少几篇（才能学人设）
GATE_AUTHORS = 5        # 至少覆盖几个作者（防止学成复读机）

# 单条样本的取舍阈值。**全部来自 19 篇真实语料实测**（2026-11-25）：
#   lead 长度 min 127 / 中位 201 / max 536 —— 原来拍的 80-200 会把中位样本全丢掉
#   title 长度 8-40、中位 29
#   heads 数实测集合 {0,3,4,5,11,24,31,40}：>6 是 Q&A 体，不进骨架集
MIN_LEAD, MAX_LEAD = 100, 350
MIN_TITLE, MAX_TITLE = 8, 40
MIN_HEADS, MAX_HEADS = 2, 6
MIN_END, MAX_END = 80, 600
DUP_OVERLAP = 13                   # 6-gram 重合块 >13 视为洗稿（裁定已定）

K = 6


def norm(t):
    # 骨架样本是 list（小标题序列），先拼成字符串再比，否则 regex 会炸
    if isinstance(t, (list, tuple)):
        t = "".join(str(x) for x in t)
    t = re.sub(r"```[\s\S]*?```", "", t or "")
    t = re.sub(r"https?://\S+", "", t)
    return re.sub(r"\s+", "", t)


def grams(t, k=K):
    s = norm(t)
    return {s[i:i + k] for i in range(len(s) - k + 1)} if len(s) >= k else set()


def overlap(a, b, k=K):
    """重合块数：取两集合交集大小（与 spec 的「6-gram 重合块 >13」同口径）。"""
    return len(grams(a, k) & grams(b, k))


def paragraphs(text):
    ps = [p.strip() for p in re.split(r"\n+", text or "") if p.strip()]
    return [p for p in ps if len(norm(p)) >= 20]


def load(path=None):
    path = path or SRC
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    return rows


def gate(rows):
    """三条语料门槛。返回 dict（每项含 ok/need/have），不抛异常。"""
    per = {}
    for r in rows:
        per[r.get("account") or "未知"] = per.get(r.get("account") or "未知", 0) + 1
    authors = len(per)
    best = max(per.values()) if per else 0
    return {
        "total": {"ok": len(rows) >= GATE_TOTAL, "have": len(rows), "need": GATE_TOTAL},
        "per_author": {"ok": best >= GATE_PER_AUTHOR, "have": best,
                       "need": GATE_PER_AUTHOR, "top": sorted(per.items(),
                                                              key=lambda kv: -kv[1])[:5]},
        "authors": {"ok": authors >= GATE_AUTHORS, "have": authors, "need": GATE_AUTHORS},
        "by_author": per,
    }


def ready(g):
    return all(g[k]["ok"] for k in ("total", "per_author", "authors"))


def build(rows):
    """拆四任务数据集。返回 (sets, dropped)。"""
    titles, leads, heads, endings = [], [], [], []
    dropped = {"title": 0, "lead": 0, "heads": 0, "end": 0, "dup": 0}
    seen_titles = set()

    for r in rows:
        title = (r.get("title") or "").strip()
        text = r.get("text") or ""
        ps = paragraphs(text)
        if not ps:
            continue
        acct = r.get("account") or "未知"

        # 1 标题：长度合格 + 全局不重复（同题重复会教模型复读同一个题）
        if MIN_TITLE <= len(title) <= MAX_TITLE and title not in seen_titles:
            seen_titles.add(title)
            titles.append({"title": title, "account": acct,
                           "has_num": bool(re.search(r"\d", title)),
                           "is_q": bool(re.search(r"[？?]$", title))})
        else:
            dropped["title"] += 1

        # 2 开篇：优先用抽取时定好的 lead，没有才退回首段
        lead = (r.get("lead") or "").strip() or (ps[0] if ps else "")
        if MIN_LEAD <= len(norm(lead)) <= MAX_LEAD:
            leads.append({"lead": lead, "account": acct, "title": title})
        else:
            dropped["lead"] += 1

        # 3 骨架：小标题序列（取不到就跳过，不编）
        hs = [h.strip() for h in (r.get("heads") or []) if h and h.strip()]
        if MIN_HEADS <= len(hs) <= MAX_HEADS:
            heads.append({"heads": hs, "account": acct, "title": title})
        else:
            dropped["heads"] += 1

        # 4 收尾：末 3 段
        end = "\n".join(ps[-3:]) if len(ps) >= 2 else ""
        if MIN_END <= len(norm(end)) <= MAX_END:
            endings.append({"end": end, "account": acct, "title": title})
        else:
            dropped["end"] += 1

    # 洗稿闸：数据集内两两比对（样本量到 200 也才 2 万次，可接受）
    def dedup(items, key):
        kept, n = [], 0
        for it in items:
            if any(overlap(it[key], k[key]) > DUP_OVERLAP for k in kept):
                n += 1
                continue
            kept.append(it)
        return kept, n

    leads2, d_lead = dedup(leads, "lead")
    heads2, d_heads = dedup(heads, "heads")
    endings2, d_end = dedup(endings, "end")
    dropped["dup"] = d_lead + d_heads + d_end

    return {"titles": titles, "leads": leads2, "heads": heads2,
            "endings": endings2}, dropped


def write(sets, g, dropped, rows):
    os.makedirs(OUT, exist_ok=True)
    counts = {}
    for name, items in sets.items():
        path = os.path.join(OUT, name + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        counts[name] = len(items)

    title_lens = [len(i["title"]) for i in sets["titles"]]
    lead_lens = [len(norm(i["lead"])) for i in sets["leads"]]
    man = {
        "built_at": None,
        "source": os.path.relpath(SRC, ROOT),
        "source_lines": len(rows),
        "source_sha": hashlib.sha1(
            "".join(r.get("_uid", "") for r in rows).encode()).hexdigest()[:16],
        "counts": counts,
        "dropped": dropped,
        "profile": {
            "title_len_med": round(st.median(title_lens), 1) if title_lens else None,
            "title_num_pct": round(100 * sum(1 for t in sets["titles"]
                                             if t["has_num"]) / len(sets["titles"]), 1)
            if sets["titles"] else None,
            "title_q_pct": round(100 * sum(1 for t in sets["titles"]
                                           if t["is_q"]) / len(sets["titles"]), 1)
            if sets["titles"] else None,
            "lead_len_med": round(st.median(lead_lens), 1) if lead_lens else None,
        },
        "gate": {k: {"ok": g[k]["ok"], "have": g[k]["have"], "need": g[k]["need"]}
                 for k in ("total", "per_author", "authors")},
        "train_ready": ready(g),
        "_why": "train_ready=false 时不许开训：语料不到门槛，训出来会学成复读机或方向错。",
    }
    import datetime
    man["built_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump(man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return man


ART = [
    {"account": "A", "title": "秦PLUS 和海豹06 差两万，我把两页配置表叠在一起看",
     "lead": "把两页配置表打印出来，用红笔把多出来的项圈掉，桌上一共 7 个红圈。这一步花了我一个晚上，因为两家写配置表的术语不一样，得先对齐口径，再谈这一项到底值多少钱，否则就是拿不同的尺子量。",
     "heads": ["多出来的第一项是后悬架", "第二项是电池容量", "这两项占了差价的七成"],
     "text": "把两页配置表打印出来，用红笔把多出来的项圈掉，桌上一共 7 个红圈，"
             "这一步花了我一个晚上，因为配置表的术语两家人写法不一样，得先对齐。\n"
             "根据两车官方配置表，多出来的第一项是后悬架，秦PLUS 用扭力梁，海豹06 用多连杆。\n"
             "第二项是电池容量，海豹06 是 60.5 度，秦PLUS 是 48 度，按官网报价每度 600 元算差 7500 元。\n"
             "剩下的四项加起来不到 6000 元，占差价的三成。"},
    {"account": "A", "title": "同一块屏，为什么新势力要点三层、传统车企要五层",
     "lead": "同一个「关闭车道保持」，一台点两下，一台点五下，指尖在屏幕上找了三圈。我在两个品牌的展车上各试了五次，不是偶然的差异，而是两套信息架构在最常用动作上的必然结果，一个是按频次分层，一个是按模块分区。",
     "heads": ["两种信息架构的差异", "各自的代价", "正确层级怎么定"],
     "text": "同一个「关闭车道保持」，一台点两下，一台点五下，指尖在屏幕上找了三圈，"
             "这件事我在两个品牌的展车上各试了五次，不是偶然的差异。\n"
             "层级定错的代价不只在多点两下，在于用户每次都要重新找一遍，这在高速上就是风险。\n"
             "正确的做法是按使用频次分层，而不是按功能模块分，这是两套完全不同的设计哲学。"},
    {"account": "B", "title": "深色模式发灰，不是屏幕问题，是色阶没做",
     "lead": "夜里把车开进隧道，深色模式是股灰蒙蒙的光，不是黑。用测色仪量一下面板反射率就明白了，同一个亮度下两家的色阶处理完全不同，缺的不是对比度，是 8% 到 20% 之间的过渡灰阶，人眼恰恰对这个区间最敏感。",
     "heads": ["发灰的真正原因", "怎么改"],
     "text": "夜里把车开进隧道，深色模式是股灰蒙蒙的光，不是黑，这不是屏幕素质问题，"
             "用测色仪量一下面板反射率就明白了，同一个亮度下两家的色阶处理完全不同。\n"
             "汽车屏的深色模式常用纯黑加 12% 灰，但环境光一变，灰阶就浮起来了，缺少中间过渡。"},
    {"account": "B", "title": "小米 YU7 的中控屏：把最常用的三个功能藏到哪了",
     "lead": "把小米 YU7 的中控屏点亮，最常用的三个功能都不在第一屏。官方界面截图可以逐层还原点击路径，我把每一次点击都记在纸上，从进入车机到关掉车道保持，一共十七步，而第一屏上一共只放了六张卡片。",
     "heads": ["三个功能的位置", "为什么这样藏", "代价是什么"],
     "text": "把小米 YU7 的中控屏点亮，最常用的三个功能都不在第一屏，这是刻意的取舍，"
             "官方界面截图可以逐层还原点击路径，我把每一次点击都记在纸上，一共十七步。\n"
             "第一屏留给地图和卡片，常用功能退到二级，换来的是首页更干净，代价是多一次点击。"},
    {"account": "C", "title": "一张截图能看出的五种图标混用",
     "lead": "同一张截图里，五个图标的线宽有三种，圆角有两种，阴影方向还不一致。这是最容易被忽略的细节，也是界面显得不高级的真实原因之一，用户说不出哪里不对，只会觉得这块屏看着不够贵。",
     "heads": ["线宽不统一", "圆角不统一", "用色不统一"],
     "text": "同一张截图里，五个图标的线宽有三种，圆角有两种，阴影方向还不一致，"
             "这是最容易被忽略的细节，也是界面显得不高级的真实原因之一。\n"
             "图标混用不致命，但它会让界面显得廉价，用户说不出哪里不对，就是觉得不高级。"},
]


def self_test():
    fails = []
    # 测试夹具：把样例开篇补足到真实区间（实测 min 127），否则测的只是阈值本身
    rows = []
    for a in ART:
        b = dict(a)
        while len(norm(b.get("lead") or "")) < 130:
            b["lead"] = (b.get("lead") or "") + "这一句用于把样例补到真实开篇长度区间。"
        rows.append(b)

    # 1 门槛判定：19 篇级的语料必须判 train_ready=false
    g_small = gate(rows)
    if ready(g_small):
        fails.append("正控[小语料] 19 篇级语料被判 train_ready")
    if g_small["total"]["need"] != GATE_TOTAL:
        fails.append("门槛常量被改动")

    # 2 门槛判定：构造达标语料必须 true（5 作者 × 40 篇 = 200）
    big = []
    for a in range(5):
        for i in range(40):
            big.append({"account": f"A{a}", "title": f"作者{a}的第{i}篇标题示例",
                        "heads": ["一", "二", "三"],
                        "text": "开篇一句具体的话，落在具体的物件上，不铺垫也不下结论。\n" * 3})
    g_big = gate(big)
    if not ready(g_big):
        fails.append(f"正控[达标语料] 未被判 ready：{[(k, g_big[k]['ok']) for k in ('total','per_author','authors')]}")

    # 3 四任务都能产出
    sets, dropped = build(rows)
    for name in ("titles", "leads", "heads", "endings"):
        if not sets[name]:
            fails.append(f"数据集 {name} 为空")

    # 4 负控：标题重复只留一条
    dup_rows = rows + [dict(rows[0])]
    sets2, _ = build(dup_rows)
    if len(sets2["titles"]) != len(sets["titles"]):
        fails.append("负控[标题重复] 未被去重")

    # 5 负控：洗稿必须被挡（同一段文字换个来源名）
    wash = dict(rows[0])
    wash["account"] = "B"
    wash["title"] = "完全不同的标题写法"
    sets3, d3 = build(rows + [wash])
    if len(sets3["leads"]) > len(sets["leads"]):
        fails.append("负控[洗稿] 重复开篇未被挡住")

    # 6 负控：过短开篇不许进数据集
    short = dict(rows[0]); short["text"] = "太短了。"; short["title"] = "另一个够长的标题在这里"
    sets4, _ = build([short])
    if sets4["leads"] or sets4["endings"]:
        fails.append("负控[过短] 过短开篇/收尾被收进数据集")

    # 7 负控：小标题数量越界不收
    many = dict(rows[0]); many["heads"] = ["一", "二", "三", "四", "五", "六", "七"]
    sets5, _ = build([many])
    if sets5["heads"]:
        fails.append("负控[小标题过多] 越界样本被收进骨架集")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 8/8  (门槛正反控 + 四任务产出 + 重复/洗稿/过短/越界四类负控)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    rows = load()
    g = gate(rows)

    if a.status or not a.build:
        print(f"语料 {g['total']['have']}/{g['total']['need']} 篇"
              f" · 作者 {g['authors']['have']}/{g['authors']['need']}"
              f" · 单作者最多 {g['per_author']['have']}/{g['per_author']['need']} 篇")
        print("作者分布：", " · ".join(f"{k} {v} 篇" for k, v in
                                        sorted(g["by_author"].items(), key=lambda kv: -kv[1])))
        for k, label in (("total", "总篇数"), ("per_author", "单作者篇数"),
                         ("authors", "作者数")):
            mark = "PASS" if g[k]["ok"] else "FAIL"
            print(f"  {label:10} {mark}  {g[k]['have']}/{g[k]['need']}")
        print(f"\n训练可开：{'是' if ready(g) else '否 —— 门槛没过，训了会学成复读机或方向错'}")
        return 0 if ready(g) else 1

    sets, dropped = build(rows)
    man = write(sets, g, dropped, rows)
    print(f"已生成 {OUT}")
    for k, v in man["counts"].items():
        print(f"  {k:9} {v} 条")
    print(f"  丢弃 {man['dropped']}")
    print(f"  形态 标题中位 {man['profile']['title_len_med']} 字"
          f" / 含数字 {man['profile']['title_num_pct']}%"
          f" / 开篇中位 {man['profile']['lead_len_med']} 字")
    print(f"  train_ready = {man['train_ready']}"
          + ("" if man["train_ready"] else "（门槛未过，只备料不训练）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
