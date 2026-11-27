# -*- coding: utf-8 -*-
"""
m-w2-clock · 时间与事件 v0.3

v0.3 修的是运维席实测出的两个真问题：
  1) events.jsonl 末尾半行：旧版会把下一条事件粘在残行后面，永久吞掉；
     现在每次加锁后先修尾（不回换行则截到最后一个完整行；末行不可解析则丢弃）。
  2) 锁没有属主：旧版 release 无条件删路径，别人可能替你把锁删了；
     现在锁里写 token，释放时先比对，长跑中每 50 天刷心跳。

铁律不变：只写本模块 data/ 下的 time.json / events.jsonl / engine.lock。
"""
import json
import os
import random
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")
RULES = os.path.join(ROOT, "modules", "m-r2-translate", "data", "rules.json")
TIME = os.path.join(DATA, "time.json")
EVENTS = os.path.join(DATA, "events.jsonl")
LOCK = os.path.join(DATA, "engine.lock")
STALE = 300

TEMPLATES = {
    "build": [
        "{r} 多了一条街，{a} 在里头盯了三天。",
        "{r} 的老墙挪了半米，{a} 说这样过路的人能少绕一圈。",
        "{r} 有人把空地清了出来，{a} 天天去，什么都没说。",
    ],
    "help": [
        "{a} 帮 {b} 把一段断掉的记忆接了回去。",
        "{a} 把 {b} 落下的东西送回去，没等一句谢就走了。",
        "{b} 那几天过不去，是 {a} 天天来。",
    ],
    "teach": [
        "{a} 教 {b} 一件旧手艺，说这玩意儿以后没人会了就可惜。",
        "{a} 让 {b} 上手做了一次，自己在旁边看着。",
        "{a} 把自己记了很多年的一段东西，讲给 {b} 听。",
    ],
    "repair": [
        "{r} 的一处旧线被接上，{a} 说自己只是顺手。",
        "{r} 停了三天的灯重新亮起来，{a} 没跟任何人讲。",
        "{r} 有个人回来了，{a} 去门口接的。",
    ],
    "weather": [
        "远处传来消息说那边又不太平，{r} 照旧过日子。",
        "{r} 落了两天雨，{a} 把门口的水扫到路沟里。",
        "{r} 断了一夜的电，天亮就好了，{a} 没让人知道。",
    ],
    "slip": [
        "{a} 手一抖，把一段还没备份的记录弄没了。",
        "{a} 走神了一瞬，{r} 的一处接头就断了。",
        "{a} 赶工赶得太急，返工比重做还慢。",
    ],
    "breach": [
        "{a} 答应过 {b} 的事没做到，{b} 没说什么，只是不再找他。",
        "{a} 把 {b} 托付的东西弄丢了，两个人都装作没事。",
    ],
}

WEIGHTS = {
    "home": ["build", "help", "teach", "help"],
    "badland": ["repair", "help", "weather"],
}


def token():
    return "%d@%s" % (os.getpid(), socket.gethostname())


def acquire_lock():
    me = token()
    for _ in (1, 2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, me.encode("utf-8"))
            os.close(fd)
            return me
        except FileExistsError:
            age = time.time() - os.path.getmtime(LOCK)
            if age < STALE:
                print(f"✗ 另一个推进进程正在运行（锁 {age:.0f}s），退出。", file=sys.stderr)
                return None
            try:
                os.remove(LOCK)
            except FileNotFoundError:
                pass
    print("✗ 无法取得推进锁", file=sys.stderr)
    return None


def release_lock(me):
    try:
        with open(LOCK, encoding="utf-8") as f:
            holder = f.read().strip()
    except FileNotFoundError:
        return
    if holder == me:
        try:
            os.remove(LOCK)
        except FileNotFoundError:
            pass


def heartbeat():
    try:
        os.utime(LOCK, None)
    except FileNotFoundError:
        pass


def read_json(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def repair_tail():
    """修 events.jsonl 尾部：无换行则截到最后一个完整行；末行不可解析则丢弃。返回丢弃行数。"""
    if not os.path.exists(EVENTS):
        return 0
    with open(EVENTS, "rb") as f:
        data = f.read()
    if not data:
        return 0
    dropped = 0
    if not data.endswith(b"\n"):
        idx = data.rfind(b"\n")
        data = data[: idx + 1] if idx >= 0 else b""
        dropped += 1
    lines = data.split(b"\n")
    while lines and not lines[-1]:
        lines.pop()
    if lines:
        try:
            json.loads(lines[-1].decode("utf-8"))
        except Exception:
            lines.pop()
            dropped += 1
    if dropped:
        with open(EVENTS, "wb") as f:
            f.write(b"\n".join(lines) + b"\n")
    return dropped


def last_seq():
    if not os.path.exists(EVENTS):
        return 0
    seq = 0
    with open(EVENTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                seq = max(seq, int(json.loads(line)["id"][1:]))
            except Exception:
                continue
    return seq


def advance(days):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    me = acquire_lock()
    if not me:
        return 1
    try:
        os.makedirs(DATA, exist_ok=True)
        fixed = repair_tail()
        if fixed:
            print(f"· 修尾：丢弃 {fixed} 条不完整记录", file=sys.stderr)

        regions = read_json(REGIONS)["regions"]
        people = read_json(PEOPLE)["people"]
        if os.path.exists(TIME):
            t = read_json(TIME)
        else:
            dmax, smax = 0, 0
            if os.path.exists(EVENTS):
                with open(EVENTS, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ev0 = json.loads(line)
                            dmax = max(dmax, int(ev0["day"]))
                            smax = max(smax, int(ev0["id"][1:]))
                        except Exception:
                            continue
            t = {"version": "1.1", "day": dmax, "seq": smax}
            print(f"· 时钟缺失，已从事件流重建：第 {dmax} 天 / seq {smax}", file=sys.stderr)
        _max_day, _max_seq = 0, 0
        if os.path.exists(EVENTS):
            with open(EVENTS, encoding="utf-8-sig", errors="replace") as _f:
                for _line in _f:
                    _line = _line.strip()
                    if not _line:
                        continue
                    try:
                        _ev = json.loads(_line)
                        _max_day = max(_max_day, int(_ev["day"]))
                        _max_seq = max(_max_seq, int(_ev["id"][1:]))
                    except Exception:
                        continue
        if _max_day > int(t.get("day", 0)):
            print(f"· 时钟落后（{t.get('day')} < {_max_day}），已按事件流对齐", file=sys.stderr)
            t["day"] = _max_day
        t["seq"] = max(int(t.get("seq", 0)), _max_seq, last_seq())

        last_by_region = {}
        if os.path.exists(EVENTS):
            with open(EVENTS, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        ev0 = json.loads(line)
                        last_by_region[ev0["region_id"]] = ev0["id"]
                    except Exception:
                        continue

        existing_days = set()
        if os.path.exists(EVENTS):
            with open(EVENTS, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing_days.add(int(json.loads(line)["day"]))
                    except Exception:
                        continue

        streaks = {r["id"]: 0 for r in regions}
        try:
            rules = read_json(RULES).get("rules", [])
        except Exception:
            rules = []

        for i in range(days):
            next_day = int(t["day"]) + 1
            if next_day in existing_days:
                print(f"✗ 第 {next_day} 天已有事件：拒绝重放（崩溃重启的典型症状）", file=sys.stderr)
                return 2
            t["day"] = next_day
            day = next_day
            rng = random.Random(day * 7919)
            region = rng.choice(regions)
            members = [p for p in people if p["region_id"] == region["id"]]
            a = rng.choice(members)
            others = [m for m in members if m["id"] != a["id"]]
            b = rng.choice(others) if others else a

            streak = streaks.get(region["id"], 0)
            if streak >= 3 and rng.random() < min(0.5, 0.10 * (streak - 2)):
                # 越顺越容易松懈：连续好事之后，失手与背约的概率上升
                etype = "slip" if rng.random() < 0.6 else "breach"
                text = rng.choice(TEMPLATES[etype]).format(r=region["name"], a=a["called"], b=b["called"])
            elif rules and rng.random() < 0.30:
                rule = rng.choice(rules)
                etype = rule["event_type"]
                base = rng.choice(TEMPLATES.get(etype, ["{r} 照旧过日子。"])).format(
                    r=region["name"], a=a["called"], b=b["called"])
                text = rule["translate"] + "。" + base.split("，")[0] + "。"
            else:
                etype = "weather" if rng.random() < 0.10 else rng.choice(WEIGHTS.get(region["kind"], ["help"]))
                text = rng.choice(TEMPLATES[etype]).format(r=region["name"], a=a["called"], b=b["called"])

            t["seq"] += 1
            prev = last_by_region.get(region["id"])
            event = {
                "id": "E%04d" % t["seq"],
                "day": day,
                "region_id": region["id"],
                "type": etype,
                "text": text,
                "actors": [a["id"], b["id"]],
                "witnesses": rng.sample([m["id"] for m in members if m["id"] not in (a["id"], b["id"])],
                                        min(20, max(0, len(members) - 2))),
                "causes": [prev] if prev else [],
                "weights": dict(zip(("positive", "cost"),
                                    {"weather": (0, 1), "slip": (0, 1), "breach": (0, 2), "blackout": (0, 2)}.get(etype, (1, 0)))),
            }
            with open(EVENTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            last_by_region[region["id"]] = event["id"]
            streaks[region["id"]] = 0 if event["weights"]["cost"] else streaks.get(region["id"], 0) + 1
            print("第 {d:>3} 天 · {r} · {t}".format(d=day, r=region["name"], t=text))
            if i % 50 == 49:
                heartbeat()

        write_atomic(TIME, t)
        return 0
    finally:
        release_lock(me)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    sys.exit(advance(n))
