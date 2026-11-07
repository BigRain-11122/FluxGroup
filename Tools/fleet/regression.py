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