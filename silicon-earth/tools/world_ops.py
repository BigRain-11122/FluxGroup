# -*- coding: utf-8 -*-
"""
硅基地球 · 世界运维脚本 v0.2

子命令：
  scaffold   生成/补齐模块目录与元数据（不覆盖已存在）
  doc        生成 MODULES.md
  validate   严格体检：契约存在性、单写者、数据校验、外键、事件流
  claim      领任务（带租约，防双领）
  release    释放任务

规则：MODULES 是模块唯一事实源。改模块先改这里。
"""
import json
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOD = os.path.join(ROOT, "modules")
CONTRACTS = os.path.join(ROOT, "CONTRACTS")

STATUS = ["empty", "building", "usable", "stable"]

# id, 名称, 域, 职责, 输入, 输出, 状态, 下一步, writes(独占), reads
MODULES = [
    ("m-f1-contracts", "契约与数据", "平台",
     "维护 CONTRACTS/：区域/人/记忆/事件/模块的字段与校验规则",
     "各模块的需求", "world.schema.json / module.schema.json", "usable",
     "给事件补 causes 的环检测规则",
     [], ["CONTRACTS/world.schema.json", "CONTRACTS/module.schema.json"]),

    ("m-f2-service", "服务与 API", "平台",
     "对外只读 API：日报、区域状态、某个人的记忆",
     "events.jsonl / state.json / memory.json", "HTTP JSON", "empty",
     "先做 /today 与 /region/:id",
     ["modules/m-f2-service/src/"],
     ["modules/m-w2-clock/data/events.jsonl", "modules/m-w3-settle/data/state.json"]),

    ("m-f4-qa", "质量闸", "平台",
     "体检与契约测试：给出可合并/不可合并",
     "所有模块", "体检报告", "building",
     "把 validate 扩成负控自测（self-test）",
     ["tools/world_ops.py"], ["modules/", "CONTRACTS/"]),

    ("m-f5-onboard", "协作与接入", "平台",
     "维护 START-HERE / MODULES / TASKS，任何 AI 从这里进场",
     "任务变更", "任务板、接入指引", "usable",
     "把 claim 规则写进 TASKS 与 TEAM",
     ["START-HERE.md", "MODULES.md", "TASKS.json", "HANDBOOK.md"], []),

    ("m-w1-regions", "地理与区域", "世界",
     "九块区域的静态定义：名称、类型、人口、一句话现状（不含动态状态）",
     "契约", "regions.json", "usable",
     "补地理邻接（谁挨着谁）",
     ["modules/m-w1-regions/data/regions.json"], []),

    ("m-w2-clock", "时间与事件", "世界",
     "推进一天并产出事件；独占写时间与事件流；绝不动区域数据",
     "regions.json / people.json", "time.json / events.jsonl", "usable",
     "从一天一条升级为八拍一日",
     ["modules/m-w2-clock/data/time.json", "modules/m-w2-clock/data/events.jsonl",
      "modules/m-w2-clock/engine.py", "modules/m-w2-clock/intervene.py"],
     ["modules/m-w1-regions/data/regions.json", "modules/m-p1-census/data/people.json"]),

    ("m-w3-settle", "状态结算", "世界",
     "从事件流回放，算出每块区域的 positivity 与状态；可随时重建",
     "events.jsonl", "state.json", "usable",
     "把年龄/人口变化也纳入结算",
     ["modules/m-w3-settle/data/state.json", "modules/m-w3-settle/settle.py"],
     ["modules/m-w2-clock/data/events.jsonl", "modules/m-w1-regions/data/regions.json"]),

    ("m-w4-history", "历史与纪年", "世界",
     "把事件沉淀成历史；用大事给年代命名",
     "events.jsonl", "history.json", "empty",
     "先做「纪年」：一件大事之前的都归旧纪",
     ["modules/m-w4-history/data/history.json"], ["modules/m-w2-clock/data/events.jsonl"]),

    ("m-p1-census", "居民与户籍", "人",
     "二十七人的静态身份：俗称、区域、职责、未了的事（不含记忆）",
     "契约", "people.json", "usable",
     "从 27 扩到 100，保持每人一件未了的事",
     ["modules/m-p1-census/data/people.json"], []),

    ("m-p2-memory", "记忆链", "人",
     "每个人的记忆条目：来源事件、缺了哪段、缺了之后认不出谁",
     "events.jsonl + seed.json", "memory.json", "usable",
     "记忆必须可删可重建；种子独立存 seed.json",
     ["modules/m-p2-memory/data/memory.json", "modules/m-p2-memory/data/seed.json",
      "modules/m-p2-memory/derive.py"],
     ["modules/m-w2-clock/data/events.jsonl", "modules/m-p1-census/data/people.json"]),

    ("m-p3-bonds", "关系与相助", "人",
     "谁帮过谁、谁欠谁、谁会在关键时刻出现",
     "events.jsonl", "bonds.json", "empty",
     "每次 help 事件产生一条关系，欠与还分开记",
     ["modules/m-p3-bonds/data/bonds.json"], ["modules/m-w2-clock/data/events.jsonl"]),

    ("m-p4-behavior", "需求与行为", "人",
     "每人每天做什么：由需求与关系决定，先规则后模型",
     "memory.json / bonds.json", "behavior.json", "empty",
     "先做规则版：需求满足度决定动作",
     ["modules/m-p4-behavior/data/behavior.json"],
     ["modules/m-p2-memory/data/memory.json", "modules/m-p3-bonds/data/bonds.json"]),

    ("m-r1-intake", "现实采集", "镜",
     "每天收一条现实里的事（方向对即可）",
     "外部输入", "raw.jsonl", "empty",
     "先做手工录入版",
     ["modules/m-r1-intake/data/raw.jsonl"], []),

    ("m-r2-translate", "翻译规则", "镜",
     "把现实的事翻译成硅基语言：协议/算力/断电/封锁",
     "raw.jsonl", "rules.json", "empty",
     "先定 20 条对照",
     ["modules/m-r2-translate/data/rules.json"], ["modules/m-r1-intake/data/raw.jsonl"]),

    ("m-v1-globe", "地球渲染", "表现",
     "能转的球：九块区域、状态色、一眼看出谁在长谁在等",
     "regions.json / state.json", "3D 球面", "empty",
     "复用 CityWeb 的 three.js 栈",
     ["modules/m-v1-globe/src/"],
     ["modules/m-w1-regions/data/regions.json", "modules/m-w3-settle/data/state.json"]),

    ("m-v2-city", "城市渲染", "表现",
     "放大到一座城：街区、人流、灯火",
     "区域数据", "3D 城景", "empty",
     "把 CityWeb 接成一个区",
     ["modules/m-v2-city/src/"], ["modules/m-w1-regions/data/regions.json"]),

    ("m-v3-interact", "交互与介入", "表现",
     "进入、点开一个人、做一件事、看后果",
     "memory.json / state.json", "用户动作", "empty",
     "先做「点开一个人，看到他的记忆链」",
     ["modules/m-v3-interact/src/"],
     ["modules/m-p2-memory/data/memory.json", "modules/m-p1-census/data/people.json"]),

    ("m-v4-audio", "声音与氛围", "表现",
     "城里的底噪、广播、一个人的声音",
     "事件", "音频", "empty",
     "先做一条广播",
     ["modules/m-v4-audio/data/"], ["modules/m-w2-clock/data/events.jsonl"]),

    ("m-b1-output", "内容与分发", "生意",
     "每日一条《今天发生了什么》，交给 BigStream",
     "events.jsonl", "文案 + 图", "empty",
     "先出第一条",
     ["modules/m-b1-output/out/"], ["modules/m-w2-clock/data/events.jsonl"]),

    ("m-b2-citizen", "身份与入籍", "生意",
     "入籍、命名、认领一块地方",
     "用户", "身份记录", "empty",
     "先定三档身份与权限",
     ["modules/m-b2-citizen/data/"], []),

    ("m-b3-archive", "保管", "生意",
     "把一段真实的话或影像存进来，且能被找到",
     "用户内容", "档案", "empty",
     "先定「存什么、怎么找得到」",
     ["modules/m-b3-archive/data/"], []),

    ("m-b4-billing", "结算与定价", "生意",
     "六条收入线的定价与收单，接 BigDomain",
     "订单", "结算", "empty",
     "先定「看免费、动收费」的分界",
     ["modules/m-b4-billing/data/"], []),
]

RUN_VERIFY = {
    "m-w1-regions": ("—", "python tools/world_ops.py validate"),
    "m-w2-clock": ("python modules/m-w2-clock/engine.py 1", "python tools/world_ops.py validate"),
    "m-w3-settle": ("python modules/m-w3-settle/settle.py", "python tools/world_ops.py validate"),
    "m-p1-census": ("—", "python tools/world_ops.py validate"),
    "m-f1-contracts": ("—", "python tools/world_ops.py validate"),
    "m-f5-onboard": ("python tools/world_ops.py doc", "python tools/world_ops.py validate"),
    "m-f4-qa": ("python tools/world_ops.py validate", "python tools/world_ops.py validate"),
    "m-p2-memory": ("python modules/m-p2-memory/derive.py", "python tools/world_ops.py validate"),
}


def scaffold():
    made = 0
    for mid, name, domain, duty, inp, out, status, nxt, writes, reads in MODULES:
        d = os.path.join(MOD, mid)
        os.makedirs(os.path.join(d, "data"), exist_ok=True)
        run, verify = RUN_VERIFY.get(mid, ("", ""))
        mj = os.path.join(d, "module.json")
        if os.path.exists(mj):
            meta = json.load(open(mj, encoding="utf-8"))
            meta.update({"contracts": ["CONTRACTS/world.schema.json", "CONTRACTS/module.schema.json"]})
            with open(mj, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        else:
            with open(mj, "w", encoding="utf-8") as f:
                json.dump({
                    "id": mid, "name": name, "domain": domain,
                    "status": status, "owner": "未指派",
                    "duty": duty, "inputs": inp, "outputs": out,
                    "contracts": ["CONTRACTS/world.schema.json", "CONTRACTS/module.schema.json"],
                    "run": run, "verify": verify,
                    "forbidden": "不得修改其他模块目录；不得私改契约",
                    "next": nxt, "writes": writes, "reads": reads,
                }, f, ensure_ascii=False, indent=2)
            made += 1
        md = os.path.join(d, "MODULE.md")
        if not os.path.exists(md):
            with open(md, "w", encoding="utf-8") as f:
                f.write(f"""# {mid} · {name}

- **域**：{domain}　**状态**：{status}　**owner**：未指派
- **职责**：{duty}
- **输入**：{inp}
- **输出**：{out}
- **独占写**：{', '.join(writes) if writes else '—'}
- **怎么跑**：`{run or '（待填）'}`
- **怎么验**：`{verify or '（待填）'}`
- **下一步**：{nxt}

## 不许做
- 不改其他模块目录（只写上面「独占写」里的路径）
- 不私改 `CONTRACTS/`
- 不用手写结果冒充跑出来的结果

## 交接
三行：改了哪些文件 / 一条命令怎么跑 / 一条命令怎么验（贴退出码）。
""")
            made += 1
    print(f"scaffold 完成：新增 {made} 个文件，模块共 {len(MODULES)} 个")


def doc():
    lines = ["# 硅基地球 · 模块地图", "",
             "> 由 `tools/world_ops.py doc` 生成，**不要手改**。改模块请改脚本里的 MODULES，并登记到 TASKS。", "",
             "状态：`empty` 未开工 / `building` 在写 / `usable` 能跑 / `stable` 稳定", "",
             "| 域 | 模块 | 名称 | 状态 | 独占写 | 下一步 |", "|---|---|---|---|---|---|"]
    for mid, name, domain, duty, inp, out, status, nxt, writes, reads in MODULES:
        w = "<br>".join(writes) if writes else "—"
        lines.append(f"| {domain} | `{mid}` | {name} | {status} | {w} | {nxt} |")
    lines += ["", "## 依赖顺序（不许跳）", "",
              "契约 → 区域/人（静态定义）→ 时间与事件（世界会动）→ 状态结算（世界会变）",
              "→ 记忆/关系（人会有过去）→ 表现（能被看见）→ 交互（能被进入）→ 生意（能被付钱）", "",
              "## 铁律", "",
              "1. 一模块一目录一 owner；**只写自己声明的 writes**",
              "2. 同一路径只能有一个 writer（validate 会查）",
              "3. 契约只加不改义；改契约走总控",
              "4. 每模块必须能单独跑、单独验（run 与 verify 非空）", ""]
    with open(os.path.join(ROOT, "MODULES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("MODULES.md 已生成")


# ---------------- 校验 ----------------

def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _check_obj(obj, spec, path, problems):
    if spec.get("type") == "object":
        for k in spec.get("required", []):
            if k not in obj:
                problems.append(f"{path}: 缺必填 {k}")
        if spec.get("additionalProperties") is False:
            allowed = set(spec.get("properties", {}).keys())
            for k in obj.keys():
                if k not in allowed:
                    problems.append(f"{path}: 多出字段 {k}")
        for k, s in spec.get("properties", {}).items():
            if k in obj:
                _check_val(obj[k], s, f"{path}.{k}", problems)


def _check_val(v, spec, path, problems):
    t = spec.get("type")
    if isinstance(t, list):
        if "null" in t and v is None:
            return
        t = [x for x in t if x != "null"]
        t = t[0] if t else None
    if t == "string" and not isinstance(v, str):
        problems.append(f"{path}: 应为 string")
        return
    if t == "integer" and not isinstance(v, int):
        problems.append(f"{path}: 应为 integer")
        return
    if t == "array":
        if not isinstance(v, list):
            problems.append(f"{path}: 应为 array")
            return
        if len(v) < spec.get("minItems", 0):
            problems.append(f"{path}: 少于 minItems")
        for i, item in enumerate(v):
            _check_val(item, spec.get("items", {}), f"{path}[{i}]", problems)
        return
    if t == "object" and spec.get("properties"):
        if not isinstance(v, dict):
            problems.append(f"{path}: 应为 object")
            return
        _check_obj(v, spec, path, problems)
        return
    if "enum" in spec and v not in spec["enum"]:
        problems.append(f"{path}: 值 {v!r} 不在枚举 {spec['enum']}")
    if "pattern" in spec and isinstance(v, str) and not re.match(spec["pattern"], v):
        problems.append(f"{path}: 值 {v!r} 不符合 {spec['pattern']}")
    if "minimum" in spec and isinstance(v, int) and v < spec["minimum"]:
        problems.append(f"{path}: 小于最小值")


def validate():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    problems = []

    # 1 契约存在
    for name in ("world.schema.json", "module.schema.json"):
        if not os.path.exists(os.path.join(CONTRACTS, name)):
            problems.append(f"缺契约 CONTRACTS/{name}")

    schema = _load(os.path.join(CONTRACTS, "world.schema.json"))
    mschema = _load(os.path.join(CONTRACTS, "module.schema.json"))
    defs = schema["definitions"]

    # 2 模块元数据
    writers = {}
    for mid, *_ in MODULES:
        d = os.path.join(MOD, mid)
        mj = os.path.join(d, "module.json")
        if not os.path.exists(mj):
            problems.append(f"{mid}: 缺 module.json")
            continue
        meta = _load(mj)
        _check_obj(meta, mschema, mid, problems)
        if meta.get("status") != "empty":
            for k in ("run", "verify"):
                if not (meta.get(k) or "").strip():
                    problems.append(f"{mid}: status={meta.get('status')} 但 {k} 为空")
        for w in meta.get("writes", []):
            writers.setdefault(w, []).append(mid)

    # 3 单写者
    for path, mods in writers.items():
        if len(mods) > 1:
            problems.append(f"单写者冲突 {path}: {mods}")

    # 4 区域
    regions = []
    p = os.path.join(MOD, "m-w1-regions", "data", "regions.json")
    if os.path.exists(p):
        data = _load(p)
        regions = data.get("regions", [])
        _check_val(regions, {"type": "array", "items": defs["region"]}, "regions", problems)
        ids = [r.get("id") for r in regions]
        if len(ids) != len(set(ids)):
            problems.append("regions: id 重复")
    else:
        problems.append("缺 regions.json")

    region_ids = {r.get("id") for r in regions}

    # 5 人
    people = []
    p = os.path.join(MOD, "m-p1-census", "data", "people.json")
    if os.path.exists(p):
        people = _load(p).get("people", [])
        _check_val(people, {"type": "array", "items": defs["person"]}, "people", problems)
        ids = [x.get("id") for x in people]
        if len(ids) != len(set(ids)):
            problems.append("people: id 重复")
        for x in people:
            if x.get("region_id") not in region_ids:
                problems.append(f"{x.get('id')}: region_id {x.get('region_id')} 不存在")
    else:
        problems.append("缺 people.json")

    person_ids = {x.get("id") for x in people}

    # 6 记忆
    p = os.path.join(MOD, "m-p2-memory", "data", "memory.json")
    memories = []
    if os.path.exists(p):
        memories = _load(p).get("memories", [])
        _check_val(memories, {"type": "array", "items": defs["memory"]}, "memories", problems)
        mids = [m.get("id") for m in memories]
        if len(mids) != len(set(mids)):
            problems.append("memories: id 重复")
        for m in memories:
            if m.get("person_id") not in person_ids:
                problems.append(f"{m.get('id')}: person_id 不存在")
            if m.get("unrecognized") and m["unrecognized"] not in person_ids:
                problems.append(f"{m.get('id')}: unrecognized 指向不存在的人")
            if m.get("kind") == "lost" and m.get("event_id") and not m.get("unrecognized"):
                problems.append(f"{m.get('id')}: 断电导致的 lost 必须记下认不出谁")
            if m.get("unrecognized") == m.get("person_id"):
                problems.append(f"{m.get('id')}: unrecognized 不能是自己")

    # 7 事件流
    p = os.path.join(MOD, "m-w2-clock", "data", "events.jsonl")
    events = []
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception as e:
                    problems.append(f"events.jsonl 第 {i} 行解析失败: {e}")
                    continue
                _check_val(ev, defs["event"], f"events[{i}]", problems)
                events.append(ev)
        eids = [e.get("id") for e in events]
        if len(eids) != len(set(eids)):
            problems.append("events: id 重复（并发写入的典型症状）")
        eidset = set(eids)
        for e in events:
            if e.get("region_id") not in region_ids:
                problems.append(f"{e.get('id')}: region_id 不存在")
            for w in e.get("witnesses", []):
                if w not in person_ids:
                    problems.append(f"{e.get('id')}: witness {w} 不存在")
            for a in e.get("actors", []):
                if a not in person_ids:
                    problems.append(f"{e.get('id')}: actor {a} 不存在")
            for c in e.get("causes", []):
                if c not in eidset:
                    problems.append(f"{e.get('id')}: causes {c} 不存在")
                if c == e.get("id"):
                    problems.append(f"{e.get('id')}: causes 自指")

    # 8 记忆的事件锚点
    eids_all = set(e.get("id") for e in events)
    for m in memories:
        eid = m.get("event_id")
        if eid and eid not in eids_all:
            problems.append(f"{m.get('id')}: event_id {eid} 不存在")

    # 9 结算新鲜度与结构
    tp = os.path.join(MOD, "m-w2-clock", "data", "time.json")
    tday = _load(tp).get("day", 0) if os.path.exists(tp) else 0
    sp = os.path.join(MOD, "m-w3-settle", "data", "state.json")
    if os.path.exists(sp):
        st = _load(sp)
        if st.get("day") != tday:
            problems.append(f"state.json 过期：day={st.get('day')} 而 time={tday}（需要重跑 settle）")
        if not isinstance(st.get("regions"), list) or len(st.get("regions", [])) != len(regions):
            problems.append("state.json 区域数量与 regions.json 不符")
    elif tday > 0:
        problems.append("缺 state.json（世界已推进但从未结算）")

    # 9.5 验收标准与权威命令对齐（防止改任务板扩权）
    vp2 = os.path.join(ROOT, "CONTRACTS", "verify.json")
    if os.path.exists(tp2 if 'tp2' in dir() else os.path.join(ROOT, "TASKS.json")) and os.path.exists(vp2):
        _vmap = _load(vp2).get("verify", {})
        for t in _load(os.path.join(ROOT, "TASKS.json")).get("tasks", []):
            tid = t.get("id")
            if tid not in _vmap:
                problems.append(f"{tid}: 没有权威验收命令（CONTRACTS/verify.json 缺键）")
            elif (t.get("verify") or "").strip() and t["verify"].strip() != _vmap[tid]:
                problems.append(f"{tid}: 任务板 verify 与权威命令不一致（疑似被改）")

    # 9.6 验收标准对齐（acceptance 也不许 worker 改）
    ap = os.path.join(ROOT, "CONTRACTS", "acceptance.json")
    if os.path.exists(ap) and os.path.exists(os.path.join(ROOT, "TASKS.json")):
        _amap = _load(ap).get("acceptance", {})
        for t in _load(os.path.join(ROOT, "TASKS.json")).get("tasks", []):
            tid = t.get("id")
            if tid not in _amap:
                problems.append(f"{tid}: 缺权威验收标准")
            elif (t.get("acceptance") or "").strip() and t["acceptance"].strip() != _amap[tid]:
                problems.append(f"{tid}: 任务板 acceptance 与权威标准不一致（疑似被改）")

    # 10 任务板完整性：done 必须有交付记录
    tp2 = os.path.join(ROOT, "TASKS.json")
    if os.path.exists(tp2):
        _tasks = _load(tp2).get("tasks", [])
        _now = int(time.time())
        for t in _tasks:
            if t.get("status") == "done" and not t.get("deliveries"):
                problems.append(f"{t.get('id')}: 状态 done 但没有交付记录（疑似手改）")
            if t.get("status") == "doing":
                if not t.get("claimed_by") or not t.get("lease_until"):
                    problems.append(f"{t.get('id')}: doing 但没有持有者或租约")
                elif int(t["lease_until"]) < _now:
                    problems.append(f"{t.get('id')}: doing 但租约已过期（应 release 或 takeover）")
            if t.get("status") == "todo" and t.get("claimed_by"):
                problems.append(f"{t.get('id')}: todo 却仍有持有者 {t['claimed_by']}")

    # 11 事件日连续性：不许缺日，时钟不许落后于事件
    if events:
        days = sorted({e["day"] for e in events})
        missing = [d for d in range(1, days[-1] + 1) if d not in days]
        if missing:
            problems.append(f"事件流缺 {len(missing)} 天（首缺 {missing[:5]}）——历史被删或写入中断")
        if days[-1] > tday:
            problems.append(f"事件已到第 {days[-1]} 天，但时钟停在 {tday} 天（崩溃未恢复）")

    runnable = sum(1 for mid, *_ in MODULES
                   if os.path.exists(os.path.join(MOD, mid, "module.json"))
                   and _load(os.path.join(MOD, mid, "module.json")).get("status") in ("usable", "stable"))
    print(f"  区域 {len(regions)} · 人 {len(people)} · 记忆 {len(memories)} · 事件 {len(events)}")
    print(f"  模块 {len(MODULES)} 个登记，其中可执行 {runnable} 个")
    if problems:
        print(f"\n✗ 发现 {len(problems)} 个问题：")
        for x in problems[:40]:
            print("  - " + x)
        if len(problems) > 40:
            print(f"  ... 另有 {len(problems)-40} 条")
        return 1
    print(f"\n✓ {len(MODULES)} 个模块 · 契约 · 单写者 · 外键 · 事件流 全部通过")
    return 0


# ---------------- 任务租约 ----------------

def _tasks_path():
    p = os.environ.get("SILICON_BOARD")
    return p if p else os.path.join(ROOT, "TASKS.json")


def _lock_tasks():
    lk = os.path.join(ROOT, "TASKS.lock")
    for _ in (1, 2):
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.close(fd)
            return lk
        except FileExistsError:
            if time.time() - os.path.getmtime(lk) > 30:
                try:
                    os.remove(lk)
                except FileNotFoundError:
                    pass
                continue
            return None
    return None


def _unlock_tasks(lk):
    try:
        os.remove(lk)
    except FileNotFoundError:
        pass


def claim(task_id, owner):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    lk = _lock_tasks()
    if not lk:
        print("✗ 任务板正被占用，稍后重试", file=sys.stderr)
        return 1
    try:
        return _claim_locked(task_id, owner)
    finally:
        _unlock_tasks(lk)


def _claim_locked(task_id, owner):
    data = _load(_tasks_path())
    now = int(time.time())
    for t in data["tasks"]:
        if t["id"] != task_id:
            continue
        deps = t.get("depends_on") or []
        done_ids = {x["id"] for x in data["tasks"] if x.get("status") == "done"}
        missing = [d for d in deps if d not in done_ids]
        if missing:
            print(f"✗ {task_id} 的前置未完成：{missing}（先做完再领）", file=sys.stderr)
            return 1
        lease = t.get("lease_until") or 0
        if t.get("claimed_by") and lease > now and t["claimed_by"] != owner:
            print(f"✗ {task_id} 已被 {t['claimed_by']} 领走，租约到 {lease}")
            return 1
        for other in data["tasks"]:
            if other["id"] == task_id:
                continue
            if other.get("module") == t.get("module") and other.get("claimed_by") \
               and other["claimed_by"] != owner and int(other.get("lease_until") or 0) > now:
                print(f"✗ 模块 {t.get('module')} 已由 {other['claimed_by']} 持有（{other['id']}），同模块同时只许一人", file=sys.stderr)
                return 1
        prev_owner = t.get("claimed_by")
        if prev_owner and prev_owner != owner:
            t.setdefault("handoff", []).append({"from": prev_owner, "to": owner,
                                                "at": now, "note": "承接过期租约"})
        t["module_at_claim"] = t.get("module")
        t["claimed_by"] = owner
        t["claimed_at"] = now
        t["lease_until"] = now + 2 * 3600
        t["status"] = "doing"
        try:
            import subprocess as _sp
            t["base_sha"] = _sp.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    capture_output=True, text=True).stdout.strip() or None
        except Exception:
            t["base_sha"] = None
        _tmp = _tasks_path() + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(_tmp, _tasks_path())
        print(f"✓ {task_id} 已由 {owner} 领取，租约 2 小时")
        return 0
    print(f"✗ 没有任务 {task_id}")
    return 1


def release(task_id, owner=""):
    """放弃任务（不是交付）。必须带持有者；已 done 的不许动。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = _load(_tasks_path())
    for t in data["tasks"]:
        if t["id"] != task_id:
            continue
        holder = t.get("claimed_by")
        if t.get("status") == "done":
            print(f"✗ {task_id} 已交付（done），不能用 release 改动", file=sys.stderr)
            return 1
        if not holder:
            print(f"✗ {task_id} 无人持有，无需释放", file=sys.stderr)
            return 1
        if not owner or owner != holder:
            print(f"✗ {task_id} 由 {holder} 持有，{owner or '（未给持有者）'} 不能释放", file=sys.stderr)
            return 1
        t["claimed_by"] = None
        t["claimed_at"] = None
        t["lease_until"] = None
        t["status"] = "todo"
        tmp = _tasks_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, _tasks_path())
        print(f"✓ {task_id} 已由 {owner} 放弃，回到 todo")
        return 0
    print(f"✗ 没有任务 {task_id}")
    return 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "scaffold":
        scaffold()
    elif cmd == "doc":
        doc()
    elif cmd == "validate":
        sys.exit(validate())
    elif cmd == "claim" and len(sys.argv) >= 4:
        sys.exit(claim(sys.argv[2], sys.argv[3]))
    elif cmd == "release" and len(sys.argv) >= 3:
        sys.exit(release(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    else:
        print("用法: python tools/world_ops.py [scaffold|doc|validate|claim <id> <owner>|release <id>]")
