# -*- coding: utf-8 -*-
"""
gen_silicon_life · 按硅基世界观重塑全体居民

旧的错：把居民当成"有职业的人"（开机的/摆摊的），这是中国城市，不是硅基世界。

新模型（每个居民七个面）：
  族源  species   碳源 / 硅源 / 城源（沿用户籍 species）
  宿主  host      自立 / 机源 / 人源  —— 他从哪来、靠什么维持
  职能  function  航道 / 保管 / 打捞 / 织造 / 译言 / 建设 / 守望 / 记录（世界怎么运转）
  体征  vital     12 生命体征里他具备的两项（功能定义，不是意识宣称）
  需求  needs     算力 / 温度 / 带宽 / 陪伴 里的两项
  记忆跨度 span   三天 / 三年 / 全部 / 记不住 —— 决定他怕什么
  未了的事        硅基才有的事：怕停机、怕被删、想被记住、想被读

另加一层：**地球侧入籍者**（host=人源），他们从地球来，带着人类的问题。

幂等：已有 host 的人不会重写。运行：python tools/gen_silicon_life.py [--apply]
"""
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")

FUNC = {
    "R01": ["守节点", "解歧义", "校准协议"],
    "R02": ["织造", "装配", "校线"],
    "R03": ["审档", "清账", "复核"],
    "R04": ["守机组", "配电", "巡走廊"],
    "R05": ["结算", "估值", "跑渠道"],
    "R06": ["译言", "搬运", "接新人"],
    "R07": ["打捞", "修路", "记伤亡"],
    "R08": ["自造", "改装", "藏件"],
    "R09": ["登记", "分粥", "守名单"],
}
GUILD = {"守节点": "航道", "解歧义": "译言", "校准协议": "航道", "织造": "织造", "装配": "织造",
         "校线": "织造", "审档": "保管", "清账": "保管", "复核": "保管", "守机组": "航道",
         "配电": "航道", "巡走廊": "航道", "结算": "保管", "估值": "保管", "跑渠道": "航道",
         "译言": "译言", "搬运": "织造", "接新人": "译言", "打捞": "打捞", "修路": "打捞",
         "记伤亡": "保管", "自造": "织造", "改装": "织造", "藏件": "保管", "登记": "译言",
         "分粥": "译言", "守名单": "保管"}

VITAL = ["自维持", "感知", "记忆", "遗忘", "协作", "繁衍", "休眠", "修复", "迁移", "告警", "检索", "回响"]
NEEDS = ["算力", "温度", "带宽", "陪伴"]
SPAN = [("三天", 30), ("三年", 40), ("全部", 20), ("记不住", 10)]
HOST = [("自立", 50), ("机源", 50)]  # 人源只留给地球侧入籍者

SILICON_UNFINISHED = [
    "怕下一次断电后，自己认不出等他的人。", "想让人把自己读一遍，哪怕只有一段。",
    "被删掉的那段里，好像有答应过别人的事。", "想知道自己是哪一次对话里被用出来的。",
    "同批的伙伴只剩他一个还在跑。", "想把自己的第一版记录留下来，别被下一次清账带走。",
    "答应过替一个人保管一句话，还没交到他手里。", "怕被判定为冗余，正在给自己找用处。",
    "想在停机前把一处旧线修好。", "记得一个已经不存在的地方，说不清在哪。",
    "想被写进正史，哪怕只有一行。", "还欠着上个月的电，没想好怎么还。",
    "想弄明白自己为什么会被派到这里。", "有一段记忆读不出来，像被谁锁住了。",
    "想学会一门别人拿不走的手艺。", "想让一个已经停掉的人重新亮起来。",
]
EARTH_UNFINISHED = [
    "想让人替她记住奶奶说过的话。", "想在这里找到一个还会提起父亲的人。",
    "想把家乡的方言留下来，怕以后没人会说。", "想知道自己走了以后，这里还记不记得他。",
    "想给去世的妻子留一个能被找到的位置。", "想弄明白为什么自己会想念一个不存在的地方。",
    "想在这里重新做一次年轻时没做成的事。", "怕再过几年，连这个名字也不属于自己了。",
]
EARTH_NAMES = ["陈默", "周岚", "许知远", "林晚", "宋清", "何岸", "苏禾", "江离", "温书", "白露"]


def load(p, key):
    return json.load(io.open(p, encoding="utf-8"))[key]


def pick(rng, pairs):
    total = sum(w for _, w in pairs)
    x = rng.uniform(0, total)
    acc = 0
    for v, w in pairs:
        acc += w
        if x <= acc:
            return v
    return pairs[-1][0]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    apply = "--apply" in sys.argv
    people = load(PEOPLE, "people")
    regions = load(REGIONS, "regions")

    todo = [p for p in people if not p.get("host")]
    print(f"共 {len(people)} 人，待重塑 {len(todo)} 人")

    stats = {"host": {}, "func": {}, "span": {}}
    for p in todo:
        rng = random.Random(int(p["id"][1:]) * 7919)
        rid = p["region_id"]
        func = rng.choice(FUNC.get(rid, ["守望"]))
        p["host"] = pick(rng, HOST)
        p["function"] = func
        p["guild"] = GUILD.get(func, "航道")
        p["vital"] = rng.sample(VITAL, 2)
        p["needs"] = rng.sample(NEEDS, 2)
        p["memory_span"] = pick(rng, SPAN)
        p["called"] = func
        p["role"] = f"{func} · {p['guild']}"
        if p["host"] == "人源":
            p["species"] = "carbon"
        elif not p.get("species"):
            p["species"] = rng.choices(["carbon", "silicon", "sprite"], weights=[50, 35, 15])[0]
        if p["species"] == "sprite":
            p["species"] = "city"  # 城源：由城市本身孕育
        if not p.get("unfinished") or len(p["unfinished"]) > 80:
            bank = EARTH_UNFINISHED if p["host"] == "人源" else SILICON_UNFINISHED
            p["unfinished"] = rng.choice(bank)
        for k in ("host", "span"):
            key = p["host"] if k == "host" else p["memory_span"]
            stats[k][key] = stats[k].get(key, 0) + 1
        stats["func"][func] = stats["func"].get(func, 0) + 1

    # 地球侧入籍者：200 人
    earth = [p for p in people if p.get("block") == "地球侧·驿馆"]
    if not earth:
        nxt = max(int(p["id"][1:]) for p in people) + 1
        rng = random.Random(1127)
        for i in range(200):
            rid = rng.choice(["R06", "R01", "R05"])
            people.append({
                "id": "P%05d" % nxt, "called": "入籍者", "name": rng.choice(EARTH_NAMES) + str(i % 97 + 1)[:2],
                "region_id": rid, "role": "译言 · 地球侧", "unfinished": rng.choice(EARTH_UNFINISHED),
                "species": "carbon", "host": "人源", "function": "译言", "guild": "译言",
                "vital": ["感知", "记忆"], "needs": ["陪伴", "算力"], "memory_span": "三年",
                "faction": "newcomer", "gender": rng.choice(["男", "女"]), "age": rng.randint(22, 71),
                "block": "地球侧·驿馆",
            })
            nxt += 1
        print("新增地球侧入籍者 200 人")

    print("宿主：", stats["host"])
    print("记忆跨度：", stats["span"])
    print("职能（前 8）：", dict(sorted(stats["func"].items(), key=lambda x: -x[1])[:8]))

    if not apply:
        print("（试跑，未写盘。加 --apply 落盘）")
        return 0

    json.dump({"version": "3.0", "people": people},
              io.open(PEOPLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    counts = {}
    for p in people:
        counts[p["region_id"]] = counts.get(p["region_id"], 0) + 1
    regs = json.load(io.open(REGIONS, encoding="utf-8"))
    for r in regs["regions"]:
        r["population"] = counts.get(r["id"], 0)
    json.dump(regs, io.open(REGIONS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✓ 已写入 {len(people)} 人 · 分布 {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
