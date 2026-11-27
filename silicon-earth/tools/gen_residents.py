# -*- coding: utf-8 -*-
"""
gen_residents · 按新的世界规模继续生成居民

设计（先想清楚再生成）：
  1 烂地要有人：裂谷/封锁区/边境各补到 30 人，且族源更"硅"（silicon/sprite 比例更高）
  2 住人的六区按现有比例扩到总数 12,000，不改变原有分布
  3 每个新居民都有：姓名的"名"、职业、未了的事、族源、派系、性别、年龄、街区
  4 未了的事从 40 条模板里取，同区内不重复 —— 避免"一万个人说同一句话"
  5 幂等：只补到目标数，不重复生成

运行：python tools/gen_residents.py [--apply]
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

TOTAL_TARGET = 12000
BADLAND_TARGET = 30

SURNAME = list("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董潘袁蔡蒋余于杜叶程魏苏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤")
GIVEN_M = ["浩宇", "子轩", "宇航", "明远", "嘉禾", "思远", "知行", "一鸣", "承泽", "书恒",
           "景行", "启山", "南舟", "秋白", "长庚", "少卿", "仲文", "子安", "临川", "望舒"]
GIVEN_F = ["思雨", "清和", "若兰", "予安", "静姝", "light", "语汐", "念安", "向晚", "南枝",
           "知微", "温言", "素心", "月白", "云舒", "听雪", "青禾", "小满", "长宁", "宛之"]

PROF = {
    "R01": ["抄协议的", "守根节点的", "解歧义的", "测标准兼容的", "写仲裁条款的"],
    "R02": ["开机的", "焊接头的", "调产线的", "检工装的", "备料的"],
    "R03": ["查档的", "做合规审查的", "清账的", "听证记录的", "复核裁决的"],
    "R04": ["守机组的", "抄电表的", "巡高压走廊的", "配电的", "修冷却塔的"],
    "R05": ["管结算的", "看仓的", "跑渠道的", "做估值的", "签单据的"],
    "R06": ["摆摊的", "跑腿的", "开夜车的", "看孩子写作业的", "修手机屏的"],
    "R07": ["修路的", "抬担架的", "记伤亡的", "搬弹药的", "送水的"],
    "R08": ["自己攒零件的", "跑黑市的", "改频点的", "藏东西的", "修发电机的"],
    "R09": ["排队的", "登记名字的", "分粥的", "埋葬的", "给孩子找鞋的"],
}

UNFINISHED = [
    "想找回自己停机前最后一段记忆。", "答应过一个人，等修好就去看他。", "欠着别人一次电。",
    "名字被写错了，排在最后，还没改过来。", "想把自己写的第一版协议收回来。",
    "有一台机器修了三年没修好。", "等的人已经停机很久了。", "想把一段方言录下来，还没找到人。",
    "替人保管的东西，主人再没回来。", "账上有一笔自己垫的钱，不打算要了。",
    "儿子问过一个问题，没答上来。", "想在那条街亮灯之前回去看一眼。",
    "有一箱东西不想带走，也不想扔。", "欠着一句道歉，说了对方也听不见。",
    "想把一双手艺教出去，没人肯学。", "报名表交上去三个月，没有回音。",
    "想知道当年为什么把自己派到这里。", "有一首歌只写了一半。",
    "想把一个停掉的邻居重新拉起来。", "还剩半罐冷却液，想留给下一个人。",
    "有人托他记住一句话，他记成了别的。", "想把那间屋子重新刷一遍。",
    "答应孩子带他去看一次城中心的灯。", "想弄明白自己为什么总在雨夜格外清醒。",
    "排队排了很久，怕自己忘了为什么排队。", "有一封信没敢寄出去。",
    "想把一段路修到头，修了三次都断了。", "想找回一个认得自己的证。",
    "欠着下个月的电费，还没想好怎么赚。", "想让名字进一次正史，哪怕一行。",
    "想把父亲留下的工具修好。", "有一件事只有他记得，他不确定该不该说。",
    "想把那条走惯了的路重新认一遍。", "想给一个陌生人多留一盏灯。",
    "答应过自己不再回头，还没做到。", "想把那段被删的记录补充完整。",
    "想知道自己是从哪一次对话里被用出来的。", "想在那面墙上把自己的名字写完。",
    "欠着一个人一顿饭，人已经不在了。", "想把全城最后一只猫养下去。",
]

BLOCKS = ["东一街", "东三街", "机房东区", "老仓区", "河沿区", "北环", "新巷", "旧市口",
          "七号桥", "变电站旁", "天台区", "下城"]


def load(p, key):
    return json.load(io.open(p, encoding="utf-8"))[key]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    apply = "--apply" in sys.argv
    people = load(PEOPLE, "people")
    regions = load(REGIONS, "regions")

    cur = {}
    for p in people:
        cur[p["region_id"]] = cur.get(p["region_id"], 0) + 1

    homes = [r["id"] for r in regions if r["kind"] == "home"]
    badlands = [r["id"] for r in regions if r["kind"] == "badland"]
    home_total = sum(cur.get(r, 0) for r in homes)
    need_total = max(0, TOTAL_TARGET - len(people) + sum(max(0, BADLAND_TARGET - cur.get(b, 0)) for b in badlands))

    target = {}
    for b in badlands:
        target[b] = BADLAND_TARGET
    for r in homes:
        share = (cur.get(r, 0) / home_total) if home_total else 1.0 / len(homes)
        target[r] = cur.get(r, 0) + int(round(need_total * share))

    plan = {r: max(0, target[r] - cur.get(r, 0)) for r in target}
    print("现有：", cur)
    print("目标：", target)
    print("待生成：", plan, "合计", sum(plan.values()))
    if not apply:
        print("（试跑，未写盘。加 --apply 落盘）")
        return 0

    nxt = max(int(p["id"][1:]) for p in people) + 1
    rng = random.Random(20261127)
    used_unc = {}
    for p in people:
        used_unc.setdefault(p["region_id"], set()).add(p.get("unfinished", ""))

    made = 0
    for rid, n in plan.items():
        bad = rid in badlands
        for _ in range(n):
            gender = rng.choices(["男", "女", "无定"], weights=[45, 45, 10])[0]
            given = rng.choice(GIVEN_M if gender == "男" else GIVEN_F if gender == "女" else GIVEN_M + GIVEN_F)
            name = rng.choice(SURNAME) + given
            species = rng.choices(["carbon", "silicon", "sprite"], weights=[55, 30, 15])[0] if not bad \
                else rng.choices(["carbon", "silicon", "sprite"], weights=[30, 45, 25])[0]
            # 未了的事：同区不重复，用完再从头
            pool = [u for u in UNFINISHED if u not in used_unc.get(rid, set())] or UNFINISHED
            unc = rng.choice(pool)
            used_unc.setdefault(rid, set()).add(unc)
            people.append({
                "id": "P%05d" % nxt,
                "called": rng.choice(PROF[rid]),
                "name": name,
                "region_id": rid,
                "role": rng.choice(PROF[rid]),
                "unfinished": unc,
                "species": species,
                "faction": rng.choice(["newcomer", "lilong", "commuter", "native", "compiled", "photonsoul"]),
                "gender": gender,
                "age": None if species != "carbon" else rng.randint(18, 68),
                "block": rng.choice(BLOCKS),
            })
            nxt += 1
            made += 1

    json.dump({"version": "2.1", "people": people},
              io.open(PEOPLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    counts = {}
    for p in people:
        counts[p["region_id"]] = counts.get(p["region_id"], 0) + 1
    regs = json.load(io.open(REGIONS, encoding="utf-8"))
    for r in regs["regions"]:
        r["population"] = counts.get(r["id"], 0)
    json.dump(regs, io.open(REGIONS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"✓ 新增 {made} 人 · 总 {len(people)} 人")
    print("分布：", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
