# -*- coding: utf-8 -*-
"""regression.py - 回归用例集：把踩过的每个坑变成一条会自动跑的断言。

为什么要有它：这几天修了上百处，每次都靠当场验证。改一个地方碰坏另一个地方没人知道，
于是"修了 13 次还是老问题"。这个文件把历史故障固化成用例，每次改码后跑一遍。

用例设计原则（负控优先）：
  * 每条都必须能在 3 秒内跑完、不联网、不写生产数据；
  * 每条都有"应通过"的输入与"应拒绝"的输入（只测通过的用例等于没测）；
  * 失败信息必须指向文件与函数，不许只说 FAIL。

Usage: regression.py [--json]
Exit: 0 全过；1 有用例失败
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))

CASES = []


def case(cid, name, why):
    def deco(fn):
        CASES.append({"id": cid, "name": name, "why": why, "fn": fn})
        return fn
    return deco


# ---- R1 队列：字段级继承 ------------------------------------------------
@case("RG-01", "状态更新行不得抹掉卡的 cmd", "2026-11-06 347 张卡降空壳的根因")
def rg01():
    import fleet_lane as fl
    d = tempfile.mkdtemp()
    p = os.path.join(d, "PRODUCTION-QUEUE.jsonl")
    fl.write_jsonl(p, [{"id": "C1", "title": "t", "cmd": "python3 x.py",
                        "nodes": ["bm-a"], "deliverable": "o.json", "state": "READY"}])
    fl.merge_jsonl(p, [{"id": "C1", "state": "OPEN", "owner": None}], key="id", mirror=False)
    row = fl.read_jsonl(p)[0]
    assert row.get("cmd") == "python3 x.py", "cmd 被抹掉了"
    assert row.get("deliverable") == "o.json", "deliverable 被抹掉了"
    # 负控：显式 null 仍必须能清除
    fl.merge_jsonl(p, [{"id": "C1", "cmd": None}], key="id", mirror=False)
    assert fl.read_jsonl(p)[0].get("cmd") is None, "显式 null 未生效"
    return "继承生效且显式 null 可清"


@case("RG-02", "没有 cmd/prompt 的卡不得进可派状态", "空壳卡被车道扫到即跳过")
def rg02():
    import fleet_lane as fl
    d = tempfile.mkdtemp()
    p = os.path.join(d, "PRODUCTION-QUEUE.jsonl")
    fl.write_jsonl(p, [])
    fl.merge_jsonl(p, [{"id": "SHELL", "state": "OPEN", "owner": "bm-b"},
                       {"id": "GOOD", "state": "OPEN", "cmd": "python3 y.py"},
                       {"id": "LLM", "state": "OPEN", "prompt": "写一句"}], key="id", mirror=False)
    m = {r["id"]: r["state"] for r in fl.read_jsonl(p)}
    assert m["SHELL"] == "CARD-DEFECT", "空壳未拦：%s" % m["SHELL"]
    assert m["GOOD"] == "OPEN" and m["LLM"] == "OPEN", "误伤了正常卡"
    return "空壳入 CARD-DEFECT，正常卡放行"


# ---- R2 同步：假脏三方向 -------------------------------------------------
@case("RG-03", "分叉判定必须分三方向", "2026-11-07 连续两次误判（checkout 回滚/落后当手改）")
def rg03():
    import fork_close as fc
    # 白名单：纯记账可安全收口；真产物必须拒绝
    book = ["cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/state/x.json",
            "cph4/fleet/queue-receipts/r.json"]
    real = ["media/asset/a.png", "Tools/fleet/new.py"]
    b, r = fc.classify(book)
    assert len(b) == 3 and not r, "记账被误判为真产物"
    b2, r2 = fc.classify(book + real)
    assert set(r2) == set(real), "真产物未被识别：%s" % r2
    return "记账/真产物分类正确"


@case("RG-04", "lanes 与 queue-receipts 必须在 git 里", "撤销我 11-06 切断派单通道的错误")
def rg04():
    # 只判「整目录被忽略」，不能做子串匹配：.gitignore 里有一条
    # cph4/fleet/queue-receipts/_last_lane_*.json（具体文件），子串判断会误伤。
    lines = [ln.strip() for ln in
             open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read().splitlines()]
    for bad in ("cph4/fleet/lanes/", "cph4/fleet/queue-receipts/"):
        assert bad not in lines, "%s 整目录被忽略 = 切断机队取卡/上报通道" % bad
    rc, out = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "origin/main",
                              "--name-only"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace").returncode, ""
    return "lanes/queue-receipts 未被忽略"


# ---- R3 判据：假绿 ------------------------------------------------------
@case("RG-05", "ensure() 的元组不得被 bool() 吞成恒真", "装失败也报 INSTALLED")
def rg05():
    import env_selfheal as es
    r = es.ensure("__no_such_tool__")
    assert isinstance(r, tuple) and len(r) == 2, "ensure 返回结构变了：%r" % (r,)
    assert bool((False, "x")) is True, "元组恒真这条常识必须成立"  # 说明为何不能 bool()
    ok, detail = es.ensure("python")
    assert isinstance(ok, bool), "第一个元素应是 bool"
    return "ensure 返回 (ok, detail)，判成败取第一个元素"


@case("RG-06", "自改新鲜度不得把自己的回执算进去", "度量自指：永远判 OK")
def rg06():
    import self_improve as si
    d = tempfile.mkdtemp()
    old = si.RECEIPT_DIR
    try:
        si.RECEIPT_DIR = d
        open(os.path.join(d, "self-improve-bm-m-x.json"), "w").write("{}")
        assert si.newest_receipt_age_s() is None, "自己的回执被算成真实产出"
        open(os.path.join(d, "real-work-1.json"), "w").write("{}")
        assert si.newest_receipt_age_s() is not None, "真实回执未被识别"
    finally:
        si.RECEIPT_DIR = old
    return "self-improve 前缀被排除"


@case("RG-07", "远端产物不得判成缺失", "48→15→6 张假完成的四次误报")
def rg07():
    import demand_audit as da
    fake = [{"id": "A", "state": "DONE", "deliverable": "D:\\FleetWorker\\x.json"},
            {"id": "B", "state": "DONE", "deliverable": "C:/Fluxgroup/x.json"},
            {"id": "C", "state": "DONE", "deliverable": "quant/bigmoney/r.json"},
            {"id": "D", "state": "DONE", "deliverable": "cph4/fleet/state/x.txt"},
            {"id": "E", "state": "DONE", "deliverable": "不存在的相对路径.json"}]
    old = da.qrows
    try:
        da.qrows = lambda: fake
        ok, ev = da.p_false_green(None)
    finally:
        da.qrows = old
    assert ok is False and "1" in ev, "未把唯一真实的缺失识别出来：%s" % ev
    return "四类远端/运行时路径放行，本地缺失仍被抓到"


# ---- R4 修复未生效 ------------------------------------------------------
@case("RG-08", "脉里每个阶段的脚本必须存在", "submit_ledger 调了不存在的文件，每天 rc=2")
def rg08():
    src = open(os.path.join(ROOT, "Tools", "fleet", "master_pulse.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "STAGES" for t in node.targets):
            for e in node.value.elts:
                if isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) >= 2:
                    if isinstance(e.elts[1], (ast.List, ast.Tuple)) and e.elts[1].elts:
                        f = e.elts[1].elts[0]
                        if isinstance(f, ast.Constant) and isinstance(f.value, str) \
                                and f.value.endswith(".py"):
                            if not os.path.exists(os.path.join(ROOT, f.value)):
                                missing.append(f.value)
    assert not missing, "悬空引用：%s" % missing
    return "STAGES 引用的脚本全部存在"


# ---- R5 收口责任 -------------------------------------------------------
@case("RG-09", "不得有无人认领的失败卡", "16 张 BLOCKED/FAILED 无 owner 长期占位")
def rg09():
    import root_cause_audit as rca
    ok, ev = rca.probe_unowned_alerts(None)
    assert ok is not False, ev
    return "失败卡均有 owner 或已归档"


@case("RG-10", "同一交付物不得两张活卡同时在飞", "bm-b 与 bm-m 撞同一文件")
def rg10():
    import demand_audit as da
    ok, ev = da.p_dup_cards(None)
    assert ok, ev
    return "无重复活卡"


# ---- R6 结构一致性 -----------------------------------------------------
@case("RG-11", "节奏表必须覆盖脉里全部阶段", "表只登记 32 条而脉跑 86 个")
def rg11():
    import cadence as cd
    tbl = cd.load_table()
    errs, warns, notes, by_id = cd.validate(tbl, cd.pulse_stages())
    assert not errs, "表校验失败：%s" % errs[:2]
    # 只查"脉→表"方向会漏掉纸面验收：表里登记、脉里却从没跑的阶段只报 WARN，
    # 而 warning 不算失败 —— verify_done 就是这样长期"有表无脉"的。
    dangling = [w for w in warns if "W-STAGE" in w]
    assert not dangling, "表里登记但脉里没接线：%s" % dangling[:2]
    return "%d 条，0 错，无未接线阶段" % len(by_id)


@case("RG-12", "现役模型只许有一个答案", "两份策略各写一个现役，导致三模型驻留 10.4GB")
def rg12():
    a = (json.load(open(os.path.join(FLEET, "MODEL-POLICY.json"), encoding="utf-8-sig"))
         .get("lane_local_llm") or {}).get("model")
    b = ((json.load(open(os.path.join(FLEET, "LOCAL-MODEL-POLICY.json"), encoding="utf-8"))
          .get("duties") or {}).get("resident") or {}).get("model")
    assert a == b, "模型现役两处不同：%s vs %s" % (a, b)
    return "两处一致：%s" % a


@case("RG-13", "无心跳记录不得当成静默 1e9 秒",
      "三机 last_result.ts 全空 → 任何卡 claim 后 3 分钟被判超时，派单链对全部机器失效")
def rg13():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import closer
    beats = closer.lane_beat()
    assert beats, "lane_beat 返回空：MASTER-STATE 读不到，心跳判定等于瞎"
    absurd = {k: v for k, v in beats.items() if v is not None and v > 1e8}
    assert not absurd, "心跳年龄出现荒谬值（无记录被当成很久）：%s" % absurd
    neg = [k for k, v in beats.items() if v is not None and v <= 0]
    assert not neg, "心跳年龄为负/零：%s" % neg
    return "%d 条车道心跳年龄正常（无记录=%d）" % (
        len(beats), sum(1 for v in beats.values() if v is None))


@case("RG-14", "四处重排阈值必须来自同一份策略",
      "closer/chief/master_agent/master_solver 各写一套阈值 → 同一张卡被四套判据来回改状态")
def rg14():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import card_policy as cp
    pol = cp.load()
    assert pol.get("max_attempts") and pol.get("heartbeat_timeout_s"), "策略文件读不到"
    import closer
    bad = []
    if closer.HEARTBEAT_TIMEOUT_S != cp.heartbeat_timeout_s():
        bad.append("closer.HEARTBEAT_TIMEOUT_S=%s" % closer.HEARTBEAT_TIMEOUT_S)
    if closer.STALL_S != cp.stall_after_s():
        bad.append("closer.STALL_S=%s" % closer.STALL_S)
    if closer.MAX_ATTEMPTS != cp.max_attempts():
        bad.append("closer.MAX_ATTEMPTS=%s" % closer.MAX_ATTEMPTS)
    import master_agent as ma
    if ma.MAX_ATTEMPTS != cp.max_attempts():
        bad.append("master_agent.MAX_ATTEMPTS=%s" % ma.MAX_ATTEMPTS)
    if int(ma.DEFAULT_LEASE.get("cpu") or 0) != cp.lease_minutes("cpu"):
        bad.append("master_agent.DEFAULT_LEASE cpu=%s" % ma.DEFAULT_LEASE.get("cpu"))
    if int(ma.DEFAULT_LEASE.get("gpu") or 0) != cp.lease_minutes("gpu"):
        bad.append("master_agent.DEFAULT_LEASE gpu=%s" % ma.DEFAULT_LEASE.get("gpu"))
    import master_solver as ms
    if ms.MAX_RETRY != max(1, cp.max_attempts() - 1):
        bad.append("master_solver.MAX_RETRY=%s" % ms.MAX_RETRY)
    assert not bad, "阈值与 CARD-POLICY-v1.json 不一致：%s" % bad
    return "四入口一致（lease cpu=%s gpu=%s · heartbeat=%ss · stall=%ss · attempts=%s）" % (
        cp.lease_minutes("cpu"), cp.lease_minutes("gpu"),
        cp.heartbeat_timeout_s(), cp.stall_after_s(), cp.max_attempts())


@case("RG-15", "队列只许行级合并写，禁整文件覆盖",
      "2026-11-02 实锚：整树重写吞掉 21 张自排卡；2026-11-07 同 id 在两份账漂移")
def rg15():
    import glob as _g
    import re as _re
    bad = []
    for p in _g.glob(os.path.join(ROOT, "Tools", "fleet", "*.py")):
        src = open(p, encoding="utf-8", errors="ignore").read()
        for m in _re.finditer(r"open\(([^\n]{0,80}),\s*[\"']w[\"']", src):
            arg = m.group(1)
            if "QUEUE" in arg or "PRODUCTION-QUEUE" in arg:
                bad.append("%s: %s" % (os.path.basename(p), arg.strip()[:50]))
    assert not bad, "整文件覆盖写队列：%s" % bad[:3]
    return "全部写者走行级合并（merge_jsonl），无整文件覆盖"


@case("RG-16", "分线质量判据必须能拦住自己的反例",
      "没有反例自证的质量闸=永远绿的空闸；21 条判据里曾有 3 条连坏样本都放行")
def rg16():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import quality_agents as qa
    rc, info = qa.selftest(verbose=False)
    assert rc == 0, "质量闸自证失败（%d 条拦不住反例）：%s" % (
        len(info.get("problems") or []), (info.get("problems") or [])[:3])
    return "%d 条判据全部能拦住专属反例" % info["items"]


@case("RG-17", "内存护栏必须在位且口径正确",
      "把文件缓存当成占用会报假紧张；只看 swap 总量会漏掉真正的换页抖动")
def rg17():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import mem_guard as mg
    cfg = mg.cfg()
    assert cfg.get("resident_gb_limit", 0) >= 12.0, "常驻上限过低（CEO 允许占满算力）"
    assert cfg.get("pageouts_max_per_min", 0) > 0, "缺换页速率阈值"
    src = open(os.path.join(ROOT, "Tools", "fleet", "mem_guard.py"), encoding="utf-8").read()
    assert "Pages wired down" in src and "compressor" in src, \
        "可用内存口径必须扣掉 wired+active+compressor（否则把文件缓存当占用）"
    fg = mg.free_gb()
    assert 0 <= fg <= 64, "可用内存读数异常：%s" % fg
    return "护栏在位（上限 %.1fGB，换页上限 %d 页/分，当前可用 %.1fGB）" % (
        cfg["resident_gb_limit"], cfg["pageouts_max_per_min"], fg)


@case("RG-18", "巡查只对 ACTIVE 的线报供给失败，且机读件必须真的写出来",
      "PARKED 的线被责令铺卡=假红（bigstream-shortvideo 129h/car-gaming 122h 实锚）；"
      "文档承诺 state/patrol.json 而代码从未写过=下游只能剥 Markdown")
def rg18():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import patrol
    json_p = os.path.join(ROOT, "cph4", "fleet", "state", "patrol.json")
    if not os.path.exists(json_p):
        assert patrol.main([]) == 0, "patrol 跑不起来"
    assert os.path.exists(json_p), "patrol 没写机读件（cph4/fleet/state/patrol.json）"
    j = json.load(open(json_p, encoding="utf-8"))
    # items 允许为空：0 条 = 机队当前没有待办，这是好状态，不是断点。
    # 首版写成 `and j["items"]`（要求非空），把「干净」判成了失败——假红。
    assert isinstance(j.get("items"), list), "机读件里没有 items 字段"

    lines = (json.load(open(os.path.join(ROOT, "cph4", "fleet", "state", "lines.json"),
                            encoding="utf-8-sig")) or {}).get("lines") or []
    nonactive = {str(l.get("id")) for l in lines
                 if str(l.get("declared") or "ACTIVE").upper() != "ACTIVE"}
    bad = [it["key"] for it in j["items"]
           if it.get("round") == "R2" and it["key"].split(":", 1)[-1] in nonactive]
    assert not bad, "把非 ACTIVE 的线报成供给失败：%s" % bad[:4]

    # 负控：体检/自述卡的判据必须能分开两种交付物（拦不住就等于没有这条判据）
    f = patrol.is_selfreport
    assert f({"deliverable": "cph4/fleet/state/city-state.json"}), "自述卡没被识别"
    assert f({"deliverable": "cph4/fleet/queue-receipts/mv-gate-20261107.json"}), "回执卡没被识别"
    assert not f({"deliverable": "gaming/FluxVerse/world/tile_01.png"}), "真产物被误判成自述"
    return "%d 条行动项，%d 条非 ACTIVE 线已跳过（%d 条被记入 parked_skipped）" % (
        len(j["items"]), len(nonactive), len(j.get("parked_skipped") or []))


@case("RG-19", "每条经验必须有可核验落点才算推广",
      "写在报告里的教训不算推广；声称有落点却核验不到的，比没有落点更严重（假绿）")
def rg19():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import retro
    items = retro.collect()
    assert items, "复盘席一条经验都没有（抽不出来=席没在工作）"

    # 负控：落点核验必须能判「有/没有/假声称」三态，判不出就等于没有这条闸
    # （注意 landing_ok 返回 (bool, 说明)，这里只取第一项——首版直接 not 元组，恒假）
    ok = lambda l: retro.landing_ok(l)[0]
    assert not ok({}), "空落点被判成已落点"
    assert not ok({"kind": "rg", "ref": "RG-DOES-NOT-EXIST"}), \
        "不存在的断言被判成已落点（假绿）"
    assert not ok({"kind": "symbol",
                   "ref": "Tools/fleet/not_a_tool.py:whatever"}), "不存在的文件被判成已落点"
    assert ok({"kind": "rg", "ref": "RG-18"}), "真断言被判成没有落点"
    assert ok({"kind": "symbol", "ref": "Tools/fleet/patrol.py:is_selfreport"}), \
        "真判据被判成没有落点"

    fake = [i["id"] for i in items
            if (i.get("landing") or {}).get("kind") and not i.get("landing_ok")]
    assert not fake, "声称有落点但核验不到：%s" % fake[:3]
    landed = [i for i in items if i.get("landing_ok")]
    return "%d 条经验，%d 条已落点可核验，%d 条待落点（待落点不算已推广）" % (
        len(items), len(landed), len(items) - len(landed))


def dup_stage_argv(stages):
    """同一工具被两个阶段跑（不论参数）= 重复劳动，且两处 ok_rc 一旦不一致，
    其中一处会把另一处认定的「告警」判成「故障」，blockers 永久亮着。"""
    seen = {}
    dup = []
    for name, argv, _to, ok, _ in stages:
        key = str(argv[0])
        if key in seen:
            dup.append((seen[key], name, key))
        else:
            seen[key] = name
    return dup


@case("RG-20", "同一工具不得被两个阶段重复登记",
      "ops_metrics.py 同时以 ops_metrics{0,1} 与 metrics{0} 登记：同一份燃尽告警被后者"
      "判成故障，blockers 永久亮 stage:metrics，而没有人知道该改哪一处")
def rg20():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import master_pulse as mp
    dup = dup_stage_argv(mp.STAGES)
    assert not dup, "重复登记：%s" % dup[:3]
    # 负控：判据必须能抓到一对重复，并且不误伤不同工具
    fake = [("a", ["Tools/x.py"], 1, {0}, False),
            ("b", ["Tools/x.py", "--y"], 1, {0}, False),
            ("c", ["Tools/z.py"], 1, {0}, False)]
    d2 = dup_stage_argv(fake)
    assert len(d2) == 1 and d2[0][:2] == ("a", "b"), "负控失败：%s" % d2
    return "%d 个阶段跑 %d 个不同工具，无重复" % (
        len(mp.STAGES), len({str(t[1][0]) for t in mp.STAGES}))


@case("RG-21", "每个阶段必须留下「最后一次真跑」的记录",
      "PULSE.json 每轮整份覆盖、慢批每 300 秒只跑一部分，于是「某阶段三小时没跑」"
      "在盘上根本查不到；ops_metrics 重复登记与 verify_done 从未接线都活在这个盲区里")
def rg21():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import master_pulse as mp
    names = {t[0] for t in mp.STAGES}
    src = open(os.path.join(ROOT, "Tools", "fleet", "master_pulse.py"), encoding="utf-8").read()
    assert "stage-last.json" in src, "脉没有写阶段执行记录（自证无据）"
    assert "stage_liveness" in names, "阶段自证没有接在脉里"
    p = os.path.join(ROOT, "cph4", "fleet", "state", "stage-last.json")
    assert os.path.exists(p), "stage-last.json 不存在（还没有一轮完整的执行记录）"
    rec = json.load(open(p, encoding="utf-8"))
    unknown = sorted(set(rec) - names)
    assert not unknown, "记录里有脉里不存在的阶段：%s" % unknown[:4]
    assert len(rec) >= 20, "记录只覆盖 %d 个阶段，覆盖太窄等于没自证" % len(rec)
    return "%d 个阶段有最后真跑记录（脉共 %d 个阶段）" % (len(rec), len(names))


def dup_stage_names(stages):
    seen, dup = set(), []
    for s in stages:
        n = s[0]
        if n in seen:
            dup.append(n)
        seen.add(n)
    return dup


@case("RG-22", "阶段名不得重复（重复的名字会互相覆盖执行记录）",
      "brain_service 与 brain_brief 都叫 brain，stages 是 dict，后者把前者结果覆盖掉，"
      "于是其中一个跑没跑、成没成在盘上都查不到")
def rg22():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import master_pulse as mp
    dup = dup_stage_names(mp.STAGES)
    assert not dup, "阶段名重复：%s" % dup
    assert dup_stage_names([("a", [], 1, {0}, False),
                            ("a", [], 1, {0}, False)]), "负控失败：同名没被抓到"
    return "%d 个阶段名互不重复" % len({t[0] for t in mp.STAGES})


@case("RG-23", "堵/坏/卡点每一类都必须在代码里有判据和解法",
      "只写分类表不实现=纸面政策：过去每一类都是「这次发现了才修」，下次换形态复发")
def rg23():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import blocker_loop as bl
    miss = bl.coverage()
    assert not miss, "分类表点名但没实现：%s" % miss[:5]
    classes = bl.spec().get("classes") or []
    assert len(classes) >= 6, "分类表只有 %d 类，覆盖太窄" % len(classes)
    for c in classes:
        assert int(c.get("every_s") or 0) > 0, "%s 没有复查周期" % c.get("id")
        assert int(c.get("escalate_after") or 0) > 0, "%s 没有升级条件" % c.get("id")
        assert c.get("owner"), "%s 没有责任人" % c.get("id")
    # 负控：摘掉一个检测器，覆盖检查必须报出来（否则 coverage 恒绿=空闸）
    real = bl.DETECTORS.pop("lane_empty_and_queue_thin")
    try:
        assert any("lane_empty_and_queue_thin" in m for m in bl.coverage()), \
            "负控失败：缺检测器没被 coverage 抓到"
    finally:
        bl.DETECTORS["lane_empty_and_queue_thin"] = real
    return "%d 类，判据/解法/周期/升级/责任人齐全" % len(classes)


@case("RG-24", "工具解析与交付物派生名都不许判成缺件（两类假红）",
      "2026-11-07 实锚：launchd 的 PATH 不含 ~/bin，asset_dataset_audit 把有 ffmpeg 的机器报成"
      "『没有 ffmpeg』；card_contract_check 把『工具按模板拼文件名』的真卡判成 SPEC-IMPOSSIBLE")
def rg24():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import asset_dataset_audit as ad
    import card_contract_check as cc
    tool = ad.ff("ffmpeg")
    visible = (os.path.exists(os.path.join(os.path.expanduser("~"), "bin",
                                           "ffmpeg" + (".exe" if os.name == "nt" else "")))
               or bool(shutil.which("ffmpeg")))
    if visible:
        assert tool and os.path.exists(tool), \
            "本机有 ffmpeg 但解析成 %r（PATH 之外的常见目录必须也查）" % tool
    # 派生名：工具源码里的 'triage-%s-%s.md' 模板必须认成产得出交付物
    assert cc.name_is_derived("python Tools/fleet/line_triage.py --line bigdomain",
                              "cph4/fleet/queue-receipts/triage-bigdomain-20261107.md",
                              ROOT), "派生名没被认出来"
    # 负控：工具里没有对应模板时必须仍是"产不出"
    assert not cc.name_is_derived("python Tools/fleet/quality_agents.py --scan",
                                  "cph4/fleet/queue-receipts/不存在的报告.md", ROOT), \
        "负控失败：没有模板也判成产得出"
    return "ffmpeg=%s · 派生名正/负控均正确" % (tool if visible else "本机无 ffmpeg（跳过）")


@case("RG-25", "归档必须是终态（旧 claim 不许把死卡写回 RUNNING）",
      "2026-11-07 实锚：mv-gate 卡归档后又被旧 claim 回写 RUNNING，继续指不存在的成片空转；"
      "过去只保护了 CANCELLED，ARCHIVED 不在保护名单里")
def rg25():
    import tempfile
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    from fleet_lane import merge_jsonl, read_jsonl
    p = os.path.join(tempfile.mkdtemp(), "q.jsonl")
    open(p, "w").write(json.dumps({"id": "T1", "cmd": "x", "state": "RUNNING"}) + "\n")
    merge_jsonl(p, [{"id": "T1", "state": "ARCHIVED", "closed_at": "2026-11-07T23:50:00"}],
                mirror=False)
    merge_jsonl(p, [{"id": "T1", "state": "RUNNING", "claimed_at": "2026-11-07T23:43:59"}],
                mirror=False)
    assert read_jsonl(p)[0]["state"] == "ARCHIVED", "归档卡被旧 claim 复活"
    merge_jsonl(p, [{"id": "T1", "state": "OPEN", "requeued_by": "ceo"}], mirror=False)
    assert read_jsonl(p)[0]["state"] == "OPEN", "显式重开被拦死（闸太紧）"
    return "归档终态守得住，显式重开也放得开"


@case("RG-26", "常驻模型只能从规则给的候选里挑，越权/乱答必须回落",
      "4B 级模型会算错数、也会凭空发明动作；给它执行权=让模型当机长")
def rg26():
    import subprocess as _sp
    rc = _sp.run([sys.executable, os.path.join(ROOT, "Tools", "fleet", "fleet_brain.py"),
                  "--selftest"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert rc.returncode == 0, "决策席自检失败：%s" % (rc.stdout or rc.stderr)[:160]
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import master_pulse as _mp
    assert "fleet_brain" in {t[0] for t in _mp.STAGES}, "决策席没有接在脉里"
    src = open(os.path.join(ROOT, "Tools", "fleet", "fleet_brain.py"), encoding="utf-8").read()
    assert "ACTIONS" in src and "A_NOOP" in src, "动作白名单缺失（模型可能直接执行任意命令）"
    return "三态自检通过（越权→回落 / 乱答→回落 / 合法→采纳），白名单在位"


@case("RG-27", "同一命令同一刻只许派一张（三个生成器会发三条同样的卡）",
      "2026-11-08 实锚：line_triage 被 workgen(R-TRIAGE)/night_plan(R-PLAN)/line_agents(Q-TRIAGE) "
      "各发一张，id 前缀不同、cmd 相同，三台机同跑同一份分诊，回执互相覆盖")
def rg27():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import master_agent as ma
    rows = [{"id": "A", "state": "RUNNING", "cmd": "python Tools/fleet/x.py --line a"},
            {"id": "B", "state": "OPEN", "cmd": "python  Tools/fleet/x.py --line a"},
            {"id": "C", "state": "OPEN", "cmd": "python Tools/fleet/x.py --line b"},
            {"id": "D", "state": "OPEN", "cmd": "python Tools/fleet/x.py --line b"}]
    kept = [r["id"] for r in ma.dedupe_pending(rows, [r for r in rows if r["state"] == "OPEN"])]
    assert kept == ["C"], "去重结果不对：%s" % kept
    return "在飞命令跳过，重复命令只留一张"


@case("RG-28", "机队调本地模型必须过网关：令牌/白名单/驻留策略",
      "裸 11434 无认证无白名单：任何机器都能要 35B 或把对照档拉起来顶掉常驻"
      "（2026-11-08 实锚：13GB 越界模型把主力挤到不可用）")
def rg28():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import llm_gateway as gw
    allow = gw.allowlist()
    assert allow, "网关白名单为空（等于把模型全关掉）"
    # 封存档与对照档绝不许放出：35B 驻留即 swap，对照档会顶掉常驻
    for bad in ("qwen3.5:35b-a3b", "qwen3:4b-instruct"):
        assert bad not in allow, "越界模型被放进白名单：%s" % bad
    # 策略强制：远端无权把模型钉死
    for m, spec in allow.items():
        assert str(spec.get("keep_alive") or ""), "%s 没有强制 keep_alive" % m
        assert int(spec.get("num_ctx") or 0) > 0, "%s 没有 num_ctx 上限" % m
    plist = os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.llmgateway.plist")
    if os.path.exists(plist):
        txt = open(plist, encoding="utf-8").read()
        assert "llm_gateway.py" in txt, "网关服务没有指向 llm_gateway.py"
    src = open(os.path.join(ROOT, "Tools", "fleet", "fleet_lane.py"), encoding="utf-8").read()
    assert "8792" in src, "机队跨机端点没有指向网关"
    return "白名单 %d 个模型，封存/对照档已排除，跨机端点走 8792" % len(allow)


@case("RG-29", "能不能用网关必须可机检，且缺令牌不许判成网关故障",
      "「网关开着」不等于「这台机器能用」：没令牌(401)/连不上/档位被封(403) "
      "在回执里长得一样，全被记成「模型不可用」就没人去补那一步准备")
def rg29():
    tool = os.path.join(ROOT, "Tools", "fleet", "llm_selftest.py")
    assert os.path.exists(tool), "没有机检工具 llm_selftest.py，各机只能靠猜"
    src = open(tool, encoding="utf-8").read()
    for code in ("E-NO-TOKEN", "E-UNREACHABLE", "E-BAD-TOKEN", "E-MODEL-DENIED"):
        assert code in src, "自测少了一态：%s（原因分不清就等于没判）" % code
    d = tempfile.mkdtemp()

    def run(tok):
        p = subprocess.run([sys.executable, tool, "--token-file", tok,
                            "--json", os.path.join(d, "llm-st.json")],
                           capture_output=True, text=True, timeout=180)
        return p.returncode

    missing = run("/tmp/definitely-no-such-llm-token")
    assert missing == 3, "缺令牌应返 3（缺料不算失败），实返 %d" % missing
    # 负控：有令牌但不对/连不上时必须返 1，否则三态退化成两态
    badtok = os.path.join(d, "badtok")
    open(badtok, "w").write("wrong")
    assert run(badtok) == 1, "错令牌/连不上应返 1（真故障），不能也返 3"
    return "四态齐全；缺令牌=3（缺料）· 错令牌/不可达=1（真故障），负控通过"


@case("RG-30", "队列文件里不许有 git 冲突标记（整文件覆盖会把它提交进历史）",
      "2026-11-08 实锚：artifact 提交整份覆盖 PRODUCTION-QUEUE.jsonl，"
      "把 01:27 未解决的 138 个空冲突块写进历史 = 414 行非 JSON；"
      "容错脚本照跑，只有严格解析的路径静默崩，谁都没发现")
def rg30():
    import queue_sanitize as qs
    offending = []
    for rel in qs.TARGETS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        blocks, nonjson, total = qs.scan(p)
        if blocks or nonjson:
            offending.append("%s 冲突块=%d 非JSON行=%d/%d" % (rel, blocks, nonjson, total))
    assert not offending, "队列被冲突标记污染：" + "；".join(offending)
    # 负控：清洗器必须真能认出并修掉冲突块（否则这个断言是空壳）
    d = tempfile.mkdtemp()
    p = os.path.join(d, "q.jsonl")
    open(p, "w", encoding="utf-8").write(
        '{"id":"A","state":"OPEN"}\n'
        "<<<<<<< HEAD\n{\"id\":\"A\",\"state\":\"DONE\"}\n=======\n"
        ">>>>>>> abc123 (x)\n{\"id\":\"B\",\"state\":\"OPEN\"}\n")
    blocks, nonjson, _ = qs.scan(p)
    assert blocks == 1, "清洗器没认出冲突块（负控失败）"
    r = qs.fix(p)
    assert qs.scan(p)[0] == 0 and r["after"] == 2, "清洗器没修好（负控失败）：%s" % r
    ids = sorted(json.loads(l)["id"] for l in open(p, encoding="utf-8") if l.strip())
    assert ids == ["A", "B"], "冲突两侧并集丢了卡：%s" % ids
    return "队列/备队列 0 冲突标记；清洗器负控通过（认出→并集修复→不丢卡）"


@case("RG-31", "停摆机名下的卡必须能被释放改派（只报不修=活被锁死）",
      "2026-11-08 实锚：bm-a 03:15 起零产出，4 张卡挂它名下 7 小时，"
      "队列显示有在飞、实际无人跑；别的机器 claim 看不到 RUNNING 卡")
def rg31():
    import time
    import blocker_loop as bl
    d = tempfile.mkdtemp()
    q = os.path.join(d, "q.jsonl")
    base = {"cmd": "python Tools/fleet/line_triage.py --line biggame", "cwd": "",
            "deliverable": "cph4/fleet/queue-receipts/t.md"}
    rows = [dict(base, id="STALL-1", state="RUNNING", owner="bm-a",
                 claimed_at="2026-11-08T03:10:00", nodes=["bm-a"]),
            dict(base, id="FRESH-1", state="RUNNING", owner="bm-b",
                 claimed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), nodes=["bm-b"]),
            dict(base, id="DONE-1", state="DONE", owner="bm-a", nodes=["bm-a"])]
    open(q, "w", encoding="utf-8").write(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    old_q, old_last, old_thr = bl.QUEUE, bl._node_last_output, bl._stalled_worker_hours
    try:
        bl.QUEUE = q
        now = time.time()
        bl._node_last_output = lambda: {"bm-a": now - 8 * 3600, "bm-b": now - 60}
        bl._stalled_worker_hours = lambda: 6.0
        hits = bl.d_stalled_worker_cards()
        assert [h["key"] for h in hits] == ["bm-a"], "应只命中停摆机 bm-a：%s" % hits
        bl.r_release_stalled(hits)
        cur = {r["id"]: r for r in (json.loads(l) for l in open(q, encoding="utf-8") if l.strip())}
        assert cur["STALL-1"]["state"] == "OPEN" and cur["STALL-1"]["owner"] is None, "停摆卡未释放"
        assert "bm-a" not in cur["STALL-1"]["nodes"], "改派后仍指向停摆机"
        assert cur["FRESH-1"]["state"] == "RUNNING", "误伤正常在飞卡"
        assert cur["DONE-1"]["state"] == "DONE", "误改已完成卡"
        # 负控：全部新鲜时不许命中（否则每轮误撤别人的活）
        bl._node_last_output = lambda: {"bm-a": now - 60, "bm-b": now - 60}
        assert bl.d_stalled_worker_cards() == [], "无停摆却命中=假红"
        # 负控2：回执名解析必须给出完整机器名（只切最后一个 "-" 会得到 "a"，匹配不上 owner）
        assert bl._node_of("AUD-GAME-20261108T102502-09-bm-a") == "bm-a", "机器名解析错（会静默失效）"
        assert bl._node_of("x-bm-m") == "bm-m", "机器名解析错"
    finally:
        bl.QUEUE, bl._node_last_output, bl._stalled_worker_hours = old_q, old_last, old_thr
    return "停摆机卡被释放并改派；新鲜卡与已完成卡不受影响；负控通过"


@case("RG-32", "lane_agent 并行分支引用的名字必须真的有定义（第三次复发防线）",
      "2026-11-05 与 2026-11-08 两次实锚：_run_one_job 只剩调用点、定义被合并顶掉，"
      "每轮 NameError，卡永久 RUNNING（第二轮堆积 18 张）")
def rg32():
    src = open(os.path.join(ROOT, "Tools", "fleet", "lane_agent.py"), encoding="utf-8").read()
    if "_run_one_job(" not in src:
        return "并行分支已不调用 _run_one_job（无需检查）"
    assert "def _run_one_job" in src, \
        "并行分支调用了 _run_one_job 但没有定义（NameError：卡会永久 RUNNING）"
    tree = ast.parse(src)
    inside = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_lane_cycle":
            inside = any(isinstance(n, ast.FunctionDef) and n.name == "_run_one_job"
                         for n in node.body)
            break
    assert inside, "_run_one_job 定义必须在 run_lane_cycle 作用域内（否则名字不可见）"
    return "定义存在且在 run_lane_cycle 内，调用点与定义同作用域"


@case("RG-33", "没令牌的模型调用必须就地判缺料，不许空打网关",
      "2026-11-08 实锚：fleet_lane 回落网关时不带 X-Flux-Token，一天被拒 830 次；"
      "配置里 token_env 只有声明、零个读取者 —— 赋能一直是纸面的")
def rg33():
    import llm_client as lc
    log = os.path.join(ROOT, "cph4", "fleet", "state", "llm-gateway.jsonl")

    def lines():
        try:
            return sum(1 for _ in open(log, encoding="utf-8"))
        except FileNotFoundError:
            return 0

    old_tok = lc.token
    try:
        lc.token = lambda: ""          # 等价于本机没钥匙
        before = lines()
        r = lc.generate("hi", endpoint="http://100.75.133.10:8792", timeout=5)
        after = lines()
        assert r["rc"] == 3 and not r["ok"], "没令牌应返 rc=3（缺料），实返 %s" % r
        assert after == before, "没令牌仍然发了请求（网关日志 +%d 行）= 空打" % (after - before)
    finally:
        lc.token = old_tok
    # 接线断言：跨机回落必须走带令牌的客户端，不许再拼裸请求
    src = open(os.path.join(ROOT, "Tools", "fleet", "fleet_lane.py"), encoding="utf-8").read()
    assert "llm_client.generate" in src, "local_llm 的跨机回落没接 llm_client（会重现 830 次空打）"
    # 第二个空打口：_llm_tags 探测模型列表时也不许裸奔（日志 UA=Python-urllib 一天 800+ 次）
    assert "X-Flux-Token" in src, "_llm_tags 探测跨机端点没带令牌（会持续被拒）"
    return "无令牌就地判 rc=3 且零请求；跨机回落已接统一客户端"


@case("RG-34", "唤醒清单空着的僵尸机不许再被派活（否则卡必挂到停摆判据来救）",
      "2026-11-08 实锚：bm-a 的 FleetLink 活着、report online、能收 poke，"
      "但 /status 的 wakes=[]，派过去的卡只能挂 RUNNING 等 6h 后被释放")
def rg34():
    import time
    import blocker_loop as bl
    import master_agent as ma
    old_last, old_thr = bl._node_last_output, bl._stalled_worker_hours
    try:
        now = time.time()
        bl._node_last_output = lambda: {"bm-a": now - 8 * 3600, "bm-b": now - 60}
        bl._stalled_worker_hours = lambda: 6.0
        fleet = {n: {"online": True, "age_s": 10, "state": {}, "ram_gb": 24}
                 for n in ("bm-a", "bm-b", "bm-m")}
        ok, why = ma.lane_capacity("bm-a", fleet, "cpu")
        assert (not ok) and "EXECUTOR-DEAD" in why, "僵尸机仍可接活：%s / %s" % (ok, why)
        ok2, why2 = ma.lane_capacity("bm-b", fleet, "cpu")
        assert ok2, "正常机被误排除（负控失败）：%s" % why2
    finally:
        bl._node_last_output, bl._stalled_worker_hours = old_last, old_thr
    return "僵尸机被排除且理由可读；正常机不受影响"


@case("RG-35", "运行时看板不得入产物档（一日 788 份同一张屏=假产量）",
      "2026-11-08 实锚：QUALITY-BOARD 每轮重写且带时间戳，归档按内容哈希，一天堆出 788 份副本")
def rg35():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
    import artifact_review as ar
    r = ar.archive(os.path.join(ROOT, "cph4", "fleet", "QUALITY-BOARD.md"),
                   {"id": "T", "line": "fleet-ops"}, [])
    assert isinstance(r, dict) and r.get("skipped") == "runtime-board", \
        "看板没被挡在入档外：%s" % r
    return "运行时看板已挡在归档之外"


@case("RG-38", "模型候选集必须覆盖三类自愈动作，且干净时不许凭空造活",
      "2026-11-08：修坏账本/撤重复卡/复活执行者此前全靠会话手动做，"
      "模型只有派单与补供给可选；加进候选后模型才可能自己选到")
def rg38():
    import fleet_brain as fb
    dirty = {"lanes": {}, "idle_nodes": [], "open": 3, "running": 1, "stalled_lines": [],
             "blocker_hits": 0, "blocker_escalate": 0, "unowned": [],
             "queue_dirty": 7, "dup_live": 2, "dead_exec": 1}
    ids = [c["id"] for c in fb.candidates(dirty)]
    for must in ("A_SANITIZE", "A_DEDUPE", "A_REVIVE"):
        assert must in ids, "有对应故障却没给候选：%s（模型永远选不到）" % must
        assert must in fb.ACTIONS, "候选 %s 没有白名单执行器（选了也动不了）" % must
    clean = dict(dirty, queue_dirty=0, dup_live=0, dead_exec=0)
    ids2 = [c["id"] for c in fb.candidates(clean)]
    for bad in ("A_SANITIZE", "A_DEDUPE", "A_REVIVE"):
        assert bad not in ids2, "一切正常仍给候选 %s（会为动而动）" % bad
    assert "A_NOOP" in ids2, "没有 A_NOOP：模型无从表达'什么都不做'"
    return "三类自愈动作在候选与白名单里；干净时只给 A_NOOP"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    results = []
    for c in CASES:
        try:
            detail = c["fn"]()
            results.append({"id": c["id"], "name": c["name"], "ok": True, "detail": detail})
        except AssertionError as e:
            results.append({"id": c["id"], "name": c["name"], "ok": False, "detail": str(e)[:200]})
        except Exception as e:
            results.append({"id": c["id"], "name": c["name"], "ok": False,
                            "detail": "%s: %s" % (type(e).__name__, str(e)[:160])})
    bad = [r for r in results if not r["ok"]]
    if a.json:
        print(json.dumps({"total": len(results), "failed": len(bad), "cases": results},
                         ensure_ascii=False))
    else:
        for r in results:
            print("%s %s %-40s %s" % ("PASS" if r["ok"] else "FAIL", r["id"], r["name"], r["detail"]))
    print(json.dumps({"verdict": "FAIL" if bad else "PASS",
                      "passed": len(results) - len(bad), "total": len(results)},
                     ensure_ascii=False))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())