# -*- coding: utf-8 -*-
"""
第一屏原型构建：读真实数据，生成可双击打开的 entry.html

用法：python build_entry.py
输出：同目录 entry.html（自包含，无网络依赖）

只读：regions.json / people.json / state.json / time.json / events.jsonl
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # silicon-earth
MOD = os.path.join(ROOT, "modules")

REGIONS = os.path.join(MOD, "m-w1-regions", "data", "regions.json")
PEOPLE = os.path.join(MOD, "m-p1-census", "data", "people.json")
STATE = os.path.join(MOD, "m-w3-settle", "data", "state.json")
MEM = os.path.join(MOD, "m-p2-memory", "data", "memory.json")
TIME = os.path.join(MOD, "m-w2-clock", "data", "time.json")
EVENTS = os.path.join(MOD, "m-w2-clock", "data", "events.jsonl")
TPL = os.path.join(HERE, "entry.template.html")
OUT = os.path.join(HERE, "entry.html")

STATE_CN = {
    "growing": "在长", "repairing": "在修", "waiting": "在等",
    "dispersing": "在散", "stalled": "停摆",
}

# 球面布点：六个住人区在中纬环上，三块烂地在南边
SPHERE = {
    "R01": (26, 0), "R02": (26, 120), "R03": (26, 240),
    "R04": (-14, 60), "R05": (-14, 180), "R06": (-14, 300),
    "R07": (-58, 30), "R08": (-58, 150), "R09": (-58, 270),
}


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def recent_events(n=3):
    """每个区最近 n 条事件（按天升序），给「你到之前的三天」用"""
    out = {}
    if not os.path.exists(EVENTS):
        return out
    with open(EVENTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if not isinstance(ev, dict) or "region_id" not in ev:
                continue
            out.setdefault(ev["region_id"], []).append(
                {"day": int(ev.get("day", 0)), "text": ev.get("text", "")}
            )
    for rid in out:
        out[rid] = out[rid][-n:]
    return out


def last_events():
    """每个区最后一条事件（晚出现的覆盖早的）"""
    out = {}
    if not os.path.exists(EVENTS):
        return out
    with open(EVENTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if not isinstance(ev, dict) or "region_id" not in ev:
                continue
            rid = ev["region_id"]
            if rid not in out or int(ev.get("day", 0)) >= int(out[rid].get("day", 0)):
                out[rid] = ev
    return out


def memory_index():
    """每人第一条记忆，做「他记得什么」的展示位（只读派生文件）"""
    idx = {}
    mem = read_json(MEM, {"memories": []}).get("memories", [])
    for m in mem:
        pid = m.get("person_id")
        if pid and pid not in idx:
            idx[pid] = {"kind": m.get("kind"), "text": m.get("text"), "day": m.get("day")}
    return idx


EPI = {
    "breach": "后来的人说，第 {d} 天，{r}有人把答应过的事弄丢了。",
    "teach": "后来的人说，第 {d} 天，{r}有人把手艺交给了下一个人。",
    "help": "后来的人说，第 {d} 天，{r}有人悄悄替别人收了尾。",
    "repair": "后来的人说，第 {d} 天，{r}的灯又亮了一回。",
    "blackout": "后来的人说，第 {d} 天，{r}有一个人再没有醒来。",
}


def epigraph(ev, name, day):
    t = (ev or {}).get("type") or ""
    if t in EPI:
        return EPI[t].format(d=int(ev.get("day", day)), r=name)
    return "后来的人说，第 {d} 天，{r}下过一场雨，没人记得具体发生了什么。".format(
        d=int((ev or {}).get("day", day)), r=name)


def person_obj(p):
    called = p.get("called") or ""
    return {
        "id": p.get("id"),
        "called": called,
        "handle": "%s · %s" % (called, str(p.get("id"))[-3:]),
        "unfinished": p.get("unfinished") or "",
        "memory_span": p.get("memory_span") or "三年",
        "host": p.get("host") or "",
        "power": p.get("power") or "",
    }


def pick_people(people, region_id, n=3):
    """该区取 n 个有未了之事的人，名字尽量不重复"""
    got, seen = [], set()
    for p in people:
        if p.get("region_id") != region_id:
            continue
        if not (p.get("unfinished") or "").strip():
            continue
        called = p.get("called") or ""
        if called in seen:
            continue
        seen.add(called)
        got.append(person_obj(p))
        if len(got) >= n:
            break
    return got


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    regions = read_json(REGIONS)["regions"]
    people = read_json(PEOPLE)["people"]
    state = {r["id"]: r for r in read_json(STATE, {"regions": []})["regions"]}
    day = int(read_json(TIME, {"day": 0})["day"])
    last = last_events()
    recent = recent_events(3)
    memidx = memory_index()
    pmap = {p.get("id"): (p.get("called") or "") for p in people}
    byid = {p.get("id"): p for p in people}

    out = []
    for r in regions:
        rid = r["id"]
        lat, lon = SPHERE.get(rid, (0, 0))
        st = state.get(rid, {})
        ev = last.get(rid, {})
        cands = pick_people(people, rid)
        p0 = None
        for aid in (ev.get("actors") or []):
            if aid in byid:
                p0 = person_obj(byid[aid])
                break
        if p0 is None:
            p0 = cands[0] if cands else None
        if p0:
            p0["memory"] = memidx.get(p0["id"])
        out.append({
            "id": rid,
            "name": r["name"],
            "kind": r.get("kind", "home"),
            "population": int(r.get("population", 0)),
            "note": r.get("note", ""),
            "lat": lat,
            "lon": lon,
            "positivity": int(st.get("positivity", 50)),
            "state_cn": STATE_CN.get(st.get("state", ""), "在等"),
            "last_event_day": int(ev.get("day", day)),
            "last_event": ev.get("text", "这块地今天没有事发生。"),
            "epigraph": epigraph(ev, r["name"], day),
            "recent": recent.get(rid, []),
            "actors": [
                "%s · %s" % (pmap.get(aid, aid), str(aid)[-3:])
                for aid in (ev.get("actors") or [])[:3]
            ],
            "person": p0,
            "alts": cands[1:],
        })

    # 今天不太平：取全图最后一条 breach 所在区
    hot_rid = None
    if os.path.exists(EVENTS):
        with open(EVENTS, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if isinstance(ev, dict) and ev.get("type") == "breach":
                    hot_rid = ev.get("region_id")
    for r in out:
        r["hot"] = (r["id"] == hot_rid)

    data = {
        "day": day,
        "population": sum(r["population"] for r in out),
        "regions": out,
    }

    with open(TPL, encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False, indent=1))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK entry.html · 第 {day} 天 · {len(out)} 区 · 人口 {data['population']}")
    print(f"   热点区 = {hot_rid}")
    for r in out:
        p = r["person"]
        print(f"   {r['id']} {r['name']} {r['population']:>5} 人 · {r['state_cn']} · "
              f"{p['called'] if p else '（无人开口）'}")


if __name__ == "__main__":
    sys.exit(main() or 0)
