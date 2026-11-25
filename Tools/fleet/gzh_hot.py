#!/usr/bin/env python3
"""热点监测：从百度热搜里捞出与「汽车 / 座舱 / HMI / 智能体」相关的条目。

CEO 令 2026-11-25：「碰到热点事件马上去出文章」。抢热点的前提是**先看见**，
而且不能一看见就写——要判断它跟三支柱对不对得上，否则写了也是凑热闹。

为什么只用百度热搜：微博热搜接口 403、知乎热榜 401、懂车帝热榜返回 0 字节（JS），
第三方聚合站已死。百度热搜是唯一本机可读、服务端渲染、带热度分的榜单（2026-11-25 实测）。
汽车垂类热点靠 night_harvest 的 T1/T2 源补（工信部/中汽协/汽车媒体）。

输出三段：
  · 强相关：命中汽车/座舱/HMI 词表 → 值得看
  · 弱相关：科技/AI/芯片 → 只在能挂到「从智能体看未来」时才用
  · 建议角度：按命中的词给一个可写的角度（不是标题，是方向）

用法：
  gzh_hot.py                 # 看当前热点与建议
  gzh_hot.py --json
  gzh_hot.py --min-hot 1000000   # 只要热度高于某值
  gzh_hot.py --self-test
退出码：0 有强相关热点 / 1 没有（也是有效结论）/ 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

BD_HOT = "https://top.baidu.com/board?tab=realtime"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# 强相关：出现即认为这是我们能写的题材
STRONG = ("汽车", "车企", "车主", "座舱", "车机", "中控", "仪表", "HUD", "智驾",
          "自动驾驶", "辅助驾驶", "新能源车", "电动车", "充电", "换电", "电池",
          "小米汽车", "比亚迪", "特斯拉", "华为", "问界", "蔚来", "理想", "小鹏",
          "极氪", "长城", "长安", "吉利", "奇瑞", "智己", "阿维塔", "岚图",
          "召回", "碰撞", "续航", "车规", "车企", "车主")
# 弱相关：科技面，需要能挂到「从智能体看未来」才值得写
WEAK = ("AI", "人工智能", "大模型", "芯片", "机器人", "算力", "算法", "自动驾驶",
        "端到端", "智能体", "Agent", "操作系统", "OTA", "软件")

# 三支柱 → 用于给建议角度
PILLARS = {
    "界面": ("座舱", "车机", "中控", "仪表", "HUD", "屏", "界面", "交互", "按钮", "菜单"),
    "成本": ("利润", "价格", "降价", "涨价", "毛利", "营收", "亏损", "成本", "财报", "销量"),
    "智能体": ("AI", "大模型", "智驾", "自动驾驶", "端到端", "芯片", "算法", "机器人", "Agent"),
}

ANGLE = {
    "界面": "从界面看能力：热点里出现的车/功能，截图逐层还原它点几步、藏多深",
    "成本": "从成本看设计：这钱的变动对应到配置上的哪一项，用配置表/公告核",
    "智能体": "从智能体看未来：这个能力边界在哪，落到用户身上是多做了哪件事",
}


def fetch_hot(timeout=12, html=None):
    """取热搜列表。html 可注入（自检用），否则联网。返回 [{rank,word,hot}]。"""
    if html is None:
        req = urllib.request.Request(BD_HOT, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", "ignore")
    return parse_hot(html)


def parse_hot(html):
    """从百度热搜页面抽 (排名, 词, 热度分)。

    结构：JSON 片段里成对出现 "word":"...", "hotScore":"..."（2026-11-25 实测 52 条）。
    解析不到就返回空——由调用方决定是报错还是当"今天没热点"。
    """
    words = re.findall(r'"word":"([^"]{2,80})"', html)
    hots = re.findall(r'"hotScore":"?(\d+)"?', html)
    out, seen = [], set()
    for i, w in enumerate(words):
        w = re.sub(r"\s+", " ", w).strip()
        if not w or w in seen:
            continue
        seen.add(w)
        hot = int(hots[i]) if i < len(hots) else 0
        out.append({"rank": 0, "word": w, "hot": hot})
    out.sort(key=lambda x: -x["hot"])
    for i, it in enumerate(out, 1):
        it["rank"] = i
    return out


def classify(word):
    """返回 (相关度, 命中词)。strong > weak > none。"""
    for w in STRONG:
        if w in word:
            return "strong", w
    for w in WEAK:
        if w in word:
            return "weak", w
    return "none", ""


def suggest(word):
    """按三支柱给一个可写角度（只给方向，不给标题）。"""
    hits = [p for p, kws in PILLARS.items() if any(k in word for k in kws)]
    if not hits:
        return ""
    return " / ".join(f"{p}：{ANGLE[p]}" for p in hits[:2])


def scan(items, min_hot=0):
    strong, weak = [], []
    for it in items:
        if it["hot"] < min_hot:
            continue
        rel, kw = classify(it["word"])
        it = dict(it, rel=rel, kw=kw, angle=suggest(it["word"]))
        if rel == "strong":
            strong.append(it)
        elif rel == "weak":
            weak.append(it)
    return strong, weak


def self_test():
    fails = []
    html = ('{"word":"小米汽车利润突然掉头","hotScore":"7904136"},'
            '{"word":"演员好像忘记自己中箭了","hotScore":"7619275"},'
            '{"word":"某车企召回 12 万辆","hotScore":"5200000"},'
            '{"word":"大模型价格战再起","hotScore":"4100000"}')
    items = parse_hot(html)
    if len(items) != 4:
        fails.append(f"解析条数错：{len(items)}，应 4")
    if items[0]["word"] != "小米汽车利润突然掉头":
        fails.append("排序错：应按热度降序")

    strong, weak = scan(items)
    words = [x["word"] for x in strong]
    if "小米汽车利润突然掉头" not in words:
        fails.append("负控[汽车热点] 未识别")
    if "某车企召回 12 万辆" not in words:
        fails.append("负控[车企召回] 未识别")
    if any("演员" in w for w in words + [x["word"] for x in weak]):
        fails.append("负控[娱乐热点] 被误收")
    if not any("大模型" in x["word"] for x in weak):
        fails.append("负控[弱相关] 科技热点未归到 weak")

    # 建议角度必须挂得上支柱
    ang = [x for x in strong if "利润" in x["word"]][0]["angle"]
    if "成本" not in ang:
        fails.append(f"建议角度未命中「成本」支柱：{ang}")

    # 空页面不许崩
    if parse_hot("<html></html>") != []:
        fails.append("空页面未返回空列表")
    if scan([]) != ([], []):
        fails.append("空输入未返回空")

    # 阈值过滤
    s2, _ = scan(items, min_hot=6000000)
    if len(s2) != 1:
        fails.append(f"热度阈值过滤错：{len(s2)}，应 1")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 9/9  (解析/排序/强相关/弱相关/娱乐排除/角度/空输入/阈值)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-hot", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    try:
        items = fetch_hot()
    except Exception as e:  # noqa: BLE001
        print(f"热搜取不到：{type(e).__name__}（不影响出稿，只是没有热点输入）", file=sys.stderr)
        return 1
    if not items:
        print("热搜解析为空——页面结构可能变了，先查解析器", file=sys.stderr)
        return 1

    strong, weak = scan(items, a.min_hot)
    if a.json:
        print(json.dumps({"strong": strong, "weak": weak, "total": len(items)},
                         ensure_ascii=False, indent=1))
        return 0 if strong else 1

    print(f"百度热搜 {len(items)} 条（热度阈值 {a.min_hot or '不限'}）")
    print(f"\n强相关 {len(strong)} 条：")
    for x in strong:
        print(f"  #{x['rank']:<3} {x['word'][:36]}  热度 {x['hot']:,}  命中「{x['kw']}」")
        if x["angle"]:
            print(f"        建议角度 → {x['angle']}")
    print(f"\n弱相关 {len(weak)} 条（只在能挂到「从智能体看未来」时用）：")
    for x in weak[:6]:
        print(f"  #{x['rank']:<3} {x['word'][:36]}  热度 {x['hot']:,}")
    if not strong:
        print("\n今天没有强相关热点——不用硬蹭，按选题库正常出稿。")
    return 0 if strong else 1


if __name__ == "__main__":
    sys.exit(main())
