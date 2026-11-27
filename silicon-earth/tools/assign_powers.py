# -*- coding: utf-8 -*-
"""
assign_powers · 把已有居民编入世界格局里的势力

以前生产的人全部留用，只是给他们补上"归属"：
  三个核心：协议方 / 产能方 / 能量方
  两个依附：法规方 / 资本方
  新洲：无主（自立者、互助会）
  烂地：裂谷派系 / 封锁区 / 边境帮派

每区按权重分配，幂等（已有 power 的人不重写）。
运行：python tools/assign_powers.py [--apply]
"""
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")

# 区 → [(势力, 具体组织, 权重)]
MAP = {
    "R01": [("协议方", "标准局", 30), ("协议方", "唯一芯片厂", 25),
            ("协议方", "开源基金会", 20), ("协议方", "卫星城", 15), ("资本方", "结算所", 10)],
    "R02": [("产能方", "超级工厂城", 35), ("产能方", "供应商联盟", 25),
            ("产能方", "运输公司", 20), ("产能方", "工会", 15), ("资本方", "基金", 5)],
    "R03": [("法规方", "审查院", 45), ("法规方", "清账执行队", 30),
            ("法规方", "做事的 NGO", 15), ("法规方", "当眼线的 NGO", 10)],
    "R04": [("能量方", "老电站", 40), ("能量方", "新电站", 25),
            ("能量方", "管道公司", 20), ("能量方", "维修队", 10), ("能量方", "交易商", 5)],
    "R05": [("资本方", "评级机构", 30), ("资本方", "长线基金", 25),
            ("资本方", "做空基金", 20), ("资本方", "结算所", 25)],
    "R06": [("无主", "自立者", 45), ("无主", "互助会", 25),
            ("产能方", "外来工", 20), ("资本方", "小生意", 10)],
    "R07": [("裂谷派系", "第三条街的人", 30), ("裂谷派系", "两边都给钱的中间人", 20),
            ("裂谷派系", "中立电台", 15), ("裂谷派系", "修路的", 20), ("无主", "不走的", 15)],
    "R08": [("封锁区", "自造厂", 40), ("封锁区", "黑市", 30),
            ("封锁区", "流亡政府", 20), ("封锁区", "藏东西的", 10)],
    "R09": [("边境帮派", "管活的", 35), ("边境帮派", "管死的", 25),
            ("边境帮派", "管记忆的", 20), ("无主", "互助会", 15), ("封锁区", "走私线", 5)],
}

CAMP = {"协议方": "核心", "产能方": "核心", "能量方": "核心",
        "法规方": "依附", "资本方": "依附", "无主": "底层",
        "裂谷派系": "烂地", "封锁区": "烂地", "边境帮派": "烂地"}


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    apply = "--apply" in sys.argv
    data = load(PEOPLE)
    people = data["people"]
    todo = [p for p in people if not p.get("power")]
    print(f"共 {len(people)} 人，待编入 {len(todo)} 人")

    counts, orgs = {}, {}
    for p in todo:
        rng = random.Random(int(p["id"][1:]) * 104729)
        options = MAP.get(p["region_id"], [("无主", "自立者", 1)])
        total = sum(w for _, _, w in options)
        x = rng.uniform(0, total)
        acc = 0
        pick = options[-1]
        for o in options:
            acc += o[2]
            if x <= acc:
                pick = o
                break
        p["power"], p["org"] = pick[0], pick[1]
        p["alignment"] = CAMP.get(p["power"], "底层")
        counts[p["power"]] = counts.get(p["power"], 0) + 1
        key = f"{p['power']}·{pick[1]}"
        orgs[key] = orgs.get(key, 0) + 1

    print("按势力：", dict(sorted(counts.items(), key=lambda x: -x[1])))
    print("最大组织（前 8）：", dict(sorted(orgs.items(), key=lambda x: -x[1])[:8]))

    if not apply:
        print("（试跑，未写盘。加 --apply 落盘）")
        return 0

    json.dump(data, io.open(PEOPLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✓ 已写入 {len(people)} 人的势力归属")
    return 0


if __name__ == "__main__":
    sys.exit(main())
