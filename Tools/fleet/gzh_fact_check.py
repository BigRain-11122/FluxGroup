#!/usr/bin/env python3
"""事实核查器：把全文所有「需要溯源的数字」清点出来，逐个判有源/无源。

和 gzh_logic_check 的 L5 分工不同，两者都要跑：
  L5 只看句内 25 字窗口，用来抓「这一句的数字没交代出处」；
  本工具做**全文清点**，额外能做 L5 做不到的三件事：
    ① 四位以上精度无源 → 判「疑似编造」（编数据最容易露的就是这种假精度）
    ② 同指标两个不同值 → 判冲突（前后改数最常见的错）
    ③ 输出成清单给作者逐条补源，而不是只在终端刷一行

什么算「需要溯源」：带计量单位的数字（%, 元, 公里, 度, TOPS, kW, 英寸…）。
不追踪 个/项/层/次/台/款/种 ——那是在数场景里的东西（「点了三层菜单」），
不是对外部事实的主张；把它们塞进来只会刷屏、让人关掉闸。

四级判定：
  FAIL 无源       同句与左右各 1 句都没有来源词
  WARN 疑似编造    整数位 >=4 位、或小数位 >=2 位，且无源
  INFO 同指标两值  前后两个值挂在同一个指标上且不同
  OK   有源

用法：
  gzh_fact_check.py --in article.md
  gzh_fact_check.py --in article.md --strict     # WARN 也算失败
  gzh_fact_check.py --in article.md --json
  gzh_fact_check.py --self-test
退出码：0 全有源 / 1 有 FAIL（或 strict 下有 WARN）/ 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# 单位按长度降序尝试，避免 "km/h" 被 "km" 先吃掉
UNITS = ("TOPS", "nits", "kWh", "km/h", "kW", "Ah", "mm", "cm", "ms", "km", "Hz",
         "kg", "%", "元", "万", "亿", "公里", "度", "英寸", "寸", "倍", "分贝", "dB")

# 来源词：出现即视为作者给了出处（宁可宽，也不要逼人写八股）
SOURCE = ("根据", "来源", "官方", "官网", "公告", "财报", "报告", "配置表", "工信部",
          "国标", "标准", "实测", "测算", "估算", "报价", "页面", "截图", "原文",
          "数据", "白皮书", "发布会", "宣布", "公布", "名单", "榜单", "参数", "口径",
          "来源：", "据")

# 冲突比对用的指标白名单（按单位分组）。只认这些词，避免「同单位不同值」一刀切误报。
METRIC = {
    "kg": ("整备质量", "质量", "重量", "载重"),
    "公里": ("续航", "里程", "距离"), "km": ("续航", "里程", "距离"),
    "度": ("电池", "容量", "电量"), "kWh": ("电池", "容量", "电量"),
    "元": ("差价", "售价", "价格", "成本", "定价"), "万": ("差价", "售价", "价格", "成本", "定价"),
    "%": ("占比", "比例", "效率", "渗透率", "提升"),
    "TOPS": ("算力",), "ms": ("延迟",), "倍": ("倍",),
    "英寸": ("屏幕", "尺寸"), "寸": ("屏幕", "尺寸"),
}


def _num_unit_re():
    units = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
    # 数字后允许空格/不换行空格，再跟单位
    return re.compile(r"(?<![\d.])(\d[\d,]*(?:\.\d+)?)[\u00a0 ]*(" + units + r")")


def _sentences(md):
    """切句，标题行独立成句（否则标题会与首句粘连，借走下一句的来源）。"""
    text = re.sub(r"```[\s\S]*?```", "", md)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)     # 图片
    text = re.sub(r"https?://\S+", "", text)             # 链接
    text = re.sub(r"(?m)^#+\s*(.+)$", r"\1。", text)
    parts = re.split(r"(?<=[。！？!?；;])\s*", text)
    return [(i, s.strip()) for i, s in enumerate(parts) if s.strip()]


def _has_source(window):
    return any(w in window for w in SOURCE)


def _sig_digits(raw):
    """返回 (整数位数, 小数位数, 是否疑似假精度)。

    坑：3000 / 7500 这种整千整百是**取整**，不是假精度；
    真正像编造的是 3127、587.32 这种末位不为零的长数。
    """
    s = raw.replace(",", "")
    if "." in s:
        ip, fp = s.split(".", 1)
        return len(ip.lstrip("0")), len(fp), len(fp) >= 2
    ip = s.lstrip("0")
    return len(ip), 0, len(ip) >= 4 and not ip.endswith("0")


def check(md):
    """返回 (rows, stats)。rows 每项 dict：level/value/unit/sent/excerpt/note。"""
    sents = _sentences(md)
    rows = []
    for pos, s in sents:
        for m in _num_unit_re().finditer(s):
            raw, unit = m.group(1), m.group(2)
            # 窗口：本句 + 左右各 1 句（跨句来源是合法的，如上一句说「据配置表」）
            window = " ".join(x for p, x in sents if pos - 1 <= p <= pos + 1)
            sourced = _has_source(window)
            _, _, fake_precision = _sig_digits(raw)
            level, note = "OK", ""
            if not sourced:
                if fake_precision:
                    level, note = "WARN", "末位非零的长数字且无来源——疑似编造"
                else:
                    level, note = "FAIL", "附近无来源"
            rows.append({"level": level, "value": f"{raw}{unit}", "raw": raw,
                         "unit": unit, "sent": pos,
                         "excerpt": s[:60], "note": note})

    # 同指标两值：只对白名单指标比对，宁可漏也不刷屏。
    # 两条防误报规则：
    #   ① 指标词优先取本句；本句没有才向**紧邻上一句**继承（写作者常先说指标再给两个数）；
    #   ② 只有落在**不同句子**里的两个值才判冲突——同一句里的两个值是两台车对比，合法。
    def _metrics(text, unit):
        """取该句命中的指标词；去掉被更长命中词包含的短词（「质量」vs「整备质量」只留后者）。"""
        hits = [m for m in METRIC.get(unit, ()) if m in text]
        return [m for m in hits if not any(m != o and m in o for o in hits)]

    by_pos = dict(sents)
    for r in rows:
        own = _metrics(r["excerpt"], r["unit"]) or _metrics(by_pos.get(r["sent"] - 1, ""), r["unit"])
        if own:
            r["metrics"] = own

    groups = {}
    for r in rows:
        for metric in r.get("metrics", []):
            groups.setdefault((metric, r["unit"]), []).append(r)
    for (metric, unit), items in groups.items():
        if len({i["sent"] for i in items}) < 2:
            continue
        vals = sorted({i["raw"].replace(",", "") for i in items})
        if len(vals) > 1:
            for i in items:
                if i["level"] == "OK":
                    i["level"] = "INFO"
                i["note"] = (i["note"] + "；" if i["note"] else "") + \
                    f"同指标「{metric}」出现 {len(vals)} 个值：{'/'.join(vals)}{unit}"

    stats = {
        "sentences": len(sents),
        "numbers": len(rows),
        "fail": sum(1 for r in rows if r["level"] == "FAIL"),
        "warn": sum(1 for r in rows if r["level"] == "WARN"),
        "info": sum(1 for r in rows if r["level"] == "INFO"),
        "ok": sum(1 for r in rows if r["level"] == "OK"),
    }
    return rows, stats


GOOD = """# 秦PLUS 和海豹06 差两万，我把两页配置表叠在一起看

把两页配置表打印出来，用红笔把多出来的项圈掉，桌上一共 7 个红圈。

## 多出来的第一项是后悬架

秦PLUS 用的是扭力梁，海豹06 用的是多连杆。根据两车官方配置表，这一项差价约 3000 元。

## 第二项是电池容量

海豹06 电池 60.5 度，秦PLUS 是 48 度。按官网报价每度 600 元算，这一项差 7500 元。

## 这两项占了差价的七成

两万差价里，电池和悬架合起来约 1.4 万，占了七成。工信部公告的整备质量两者相差 45 kg。
"""

BAD_BARE = GOOD.replace("根据两车官方配置表，这一项差价约 3000 元。",
                        "这一项差价约 3000 元。")
BAD_PRECISION = GOOD.replace("按官网报价每度 600 元算，这一项差 7500 元。",
                             "按每度 587.32 元算，这一项差 7541 元。")
BAD_CONFLICT = GOOD.replace("工信部公告的整备质量两者相差 45 kg。",
                            "工信部公告的整备质量两者相差 45 kg。另一份资料写的是 51 kg。")
COUNTING = """# 同一块屏，为什么有人点三下有人点五下

同一个「关闭车道保持」，一台点 2 项，一台点 5 项，指尖在屏幕上找了三圈。
"""


def self_test():
    fails = []
    rows, st = check(GOOD)
    bad = [r for r in rows if r["level"] in ("FAIL", "WARN")]
    if bad:
        fails.append(f"正控[好稿] 被判问题: {bad[:2]}")
    if st["numbers"] < 4:
        fails.append(f"正控[好稿] 只清点到 {st['numbers']} 个数字，明显漏检")

    def level_of(doc, value):
        rs, _ = check(doc)
        hit = [r for r in rs if r["value"] == value]
        return hit[0]["level"] if hit else None

    if level_of(BAD_BARE, "3000元") != "FAIL":
        fails.append("负控[无源] 未判 FAIL")
    if level_of(BAD_PRECISION, "587.32元") != "WARN":
        fails.append("负控[假精度] 未判 WARN")
    if level_of(BAD_CONFLICT, "51kg") not in ("INFO", "FAIL"):
        fails.append("负控[同指标两值] 未判 INFO")

    # 不追踪纯计数，避免刷屏
    rs, _ = check(COUNTING)
    if rs:
        fails.append(f"负控[纯计数] 被误报 {len(rs)} 条（应 0 条）")

    # 跨句来源要认（上一句给「据配置表」，本句数字算有源）
    cross = "据官方配置表，两车差别如下。\n\n电池 60.5 度，另一台 48 度。\n"
    rs2, _ = check(cross)
    if any(r["level"] == "FAIL" for r in rs2):
        fails.append("正控[跨句来源] 被误判无源")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 6/6  (正控清点 {st['numbers']} 处 + 4 类负控 + 跨句来源)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="WARN 也算失败")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.inp:
        ap.print_help()
        return 1

    md = open(a.inp, encoding="utf-8").read()
    rows, st = check(md)

    if a.json:
        print(json.dumps({"stats": st, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        order = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}
        print(f"数字清点: {st['numbers']} 处（FAIL {st['fail']} / WARN {st['warn']} "
              f"/ INFO {st['info']} / OK {st['ok']}）\n")
        for r in sorted(rows, key=lambda x: (order[x["level"]], x["sent"])):
            tag = r["level"]
            print(f"{tag:4} {r['value']:>12}  句#{r['sent']:<3} {r['note']}")
            if r["level"] != "OK":
                print(f"     ↳ {r['excerpt']}")
        print("\n清单用法：把每条 FAIL 补上出处（官方配置表/公告/财报/页面），"
              "WARN 若确实是估算就写「估算」并把精度降下来。")

    bad = st["fail"] + (st["warn"] if a.strict else 0)
    if bad:
        print(f"\nFAIL {bad} 项需补源", file=sys.stderr)
        return 1
    print("\nPASS 全有源")
    return 0


if __name__ == "__main__":
    sys.exit(main())
