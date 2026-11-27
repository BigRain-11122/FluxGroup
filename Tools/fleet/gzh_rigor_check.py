#!/usr/bin/env python3
"""严谨闸：把「去 AI 化」和「科学化」变成可机检的判据。

CEO 令 2026-11-25：「还要有去 ai 化、科学化，不要出无脑公众 ai 文」。

**和 deai_check.py 的分工**（两个都要跑，不重复）：
  deai_check  = 词表级（赋能/闭环/众所周知…），判的是"用词像 AI"；
  本工具      = **结构级 + 证据级**，判的是"整篇的骨架像 AI、论点没有证据"。
  前者能过、后者可能全红——那正是"无脑 AI 文"：词很干净，但每段一样长、全是排比、没有具体物。

## A. AI 结构指纹（七维，越像 AI 分越高）

| 维度 | 判据 | 为什么 |
|---|---|---|
| 段落等长 | 长度变异系数 CV < 0.25 | 真人段落长短混杂，AI 每段差不多长 |
| 段首雷同 | 段落首 4 字重复率 > 40% | AI 爱用同一句式起头 |
| 连接词堆砌 | 每千字 ≥6 个（首先/其次/此外/最后…） | 三段式模板的指纹 |
| 小标题等长 | 小标题长度 CV < 0.15 且 ≥3 个 | AI 把小标题写成工整对仗 |
| 缺具体物 | 数字/型号/部位名 每千字 < 3 | 空泛是没有素材时的唯一写法 |
| 升华收尾 | 末三段出现 未来/趋势/期待/让我们 | AI 的固定收尾动作 |
| 三连排比 | 同一句式连续出现 3 次 | 骈文式排比 |

## B. 科学化（五条，证据级）

| # | 判据 | 不满足 |
|---|---|---|
| S1 测量口径 | 说了「实测/测试/测量」就必须写条件（设备/环境/样本/次数） | FAIL（无口径的实测＝编） |
| S2 不确定性 | 数字全是整数且无「约/左右/±/区间」 | WARN（假精度） |
| S3 适用边界 | 全文无「适用/不适合/如果你/例外」 | WARN（没边界＝没判断） |
| S4 反例 | 全文无「但/然而/反例/也有」 | WARN（只证不伪） |
| S5 可复现 | 声明实操类却没给步骤 | WARN |

阈值全部标 `未标定`：没有真实语料标定过，先用它挡明显失控，攒够 30 篇再重标。

用法：
  gzh_rigor_check.py --in 稿子.md
  gzh_rigor_check.py --in 稿子.md --json
  gzh_rigor_check.py --self-test
退出码：0 过关 / 1 有 FAIL / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys

# --- A 段阈值（初值，未标定）---
PARA_CV_MIN = 0.25        # 段落长度变异系数下限（低于即等长）
OPEN_DUP_MAX = 0.40       # 段首重复率上限
CONN_PER_K_MAX = 6.0      # 每千字连接词上限
HEAD_CV_MIN = 0.15        # 小标题长度 CV 下限
CONCRETE_PER_K_MIN = 3.0  # 每千字具体物下限
RIGOR_FAIL_SCORE = 45     # AI 指纹分达到此值即 FAIL

CONNECTIVES = ("首先", "其次", "再次", "最后", "此外", "同时", "与此同时", "因此",
               "总之", "综上", "总的来说", "值得注意的是", "不难发现", "显而易见",
               "另一方面", "从某种意义上")
UPWORDS = ("未来可期", "未来可期", "值得期待", "拭目以待", "让我们", "相信在不久的将来",
           "随着技术的进步", "是大势所趋", "趋势所在", "意义深远", "开创了")
# 具体物：型号、数字带单位、部位名
PART_WORDS = ("屏", "中控", "仪表", "方向盘", "座椅", "门板", "出风口", "挡把", "按键",
              "菜单", "图标", "字体", "色阶", "亮度", "刷新率", "延迟", "帧")


def n(s):
    return len(re.sub(r"\s", "", str(s or "")))


def paras_of(text):
    ps = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    return [p for p in ps if not p.startswith("#") and n(p) >= 15]


def heads_of(text):
    return [h.strip() for h in re.findall(r"(?m)^##+\s*(.+)$", text)]


def cv(vals):
    if len(vals) < 2:
        return 9.9
    m = sum(vals) / len(vals)
    if m == 0:
        return 9.9
    return st.pstdev(vals) / m


def ai_trace(text):
    """返回 (score 0-100, items)。items 每项 (维度, 是否命中, 说明)。"""
    ps = paras_of(text)
    hs = heads_of(text)
    chars = max(n(text), 1)
    items = []
    score = 0

    # 1 段落等长
    if len(ps) >= 4:
        c = cv([n(p) for p in ps])
        hit = c < PARA_CV_MIN
        items.append(("段落等长", hit, f"CV={c:.2f}（阈值 {PARA_CV_MIN}）"))
        score += 18 if hit else 0

    # 2 段首雷同
    if len(ps) >= 4:
        opens = [p[:4] for p in ps]
        dup = max(opens.count(o) for o in set(opens)) / len(opens)
        hit = dup > OPEN_DUP_MAX
        items.append(("段首雷同", hit, f"最高重复 {dup:.0%}（阈值 {OPEN_DUP_MAX:.0%}）"))
        score += 15 if hit else 0

    # 3 连接词堆砌
    cnt = sum(text.count(w) for w in CONNECTIVES)
    dens = cnt / (chars / 1000)
    hit3 = dens >= CONN_PER_K_MAX
    items.append(("连接词堆砌", hit3, f"{dens:.1f}/千字（阈值 {CONN_PER_K_MAX}）"))
    score += 16 if hit3 else 0

    # 4 小标题等长
    if len(hs) >= 3:
        c = cv([n(h) for h in hs])
        hit = c < HEAD_CV_MIN
        items.append(("小标题等长", hit, f"CV={c:.2f}（阈值 {HEAD_CV_MIN}）"))
        score += 12 if hit else 0

    # 5 缺具体物
    concrete = len(re.findall(r"\d+(?:\.\d+)?", text)) + sum(text.count(w) for w in PART_WORDS)
    dens5 = concrete / (chars / 1000)
    hit5 = dens5 < CONCRETE_PER_K_MIN
    items.append(("缺具体物", hit5, f"{dens5:.1f}/千字（阈值 {CONCRETE_PER_K_MIN}）"))
    score += 20 if hit5 else 0

    # 6 升华收尾
    tail = "\n".join(ps[-3:]) if ps else ""
    hit6 = any(w in tail for w in UPWORDS)
    items.append(("升华收尾", hit6, "末三段出现升华套话" if hit6 else "无"))
    score += 14 if hit6 else 0

    # 7 三连排比（同一句式连续 3 次，用"以X字开头"近似）
    # 2026-11-27 勘误：本篇「第一步/第二步/第三步/第四步」是操作步骤，被误判成排比。
    # 编号步骤是实操文的结构，不是修辞——不豁免这道闸会稳定误杀所有 how-to。
    STEP = re.compile(r"^(第[一二三四五六七八九十]步|[0-9]+[.、)]|步骤)")
    opens = [p[:2] for p in ps]
    is_step = [bool(STEP.match(p)) for p in ps]
    hit7 = any(opens[i] == opens[i + 1] == opens[i + 2]
               and not (is_step[i] and is_step[i + 1] and is_step[i + 2])
               for i in range(len(opens) - 2)) if len(opens) >= 3 else False
    items.append(("三连排比", hit7, "连续三段同一起头" if hit7 else "无"))
    score += 12 if hit7 else 0

    return min(100, score), items


def science(text):
    """科学化五条。返回 (fails, warns, items)。"""
    fails, warns, items = [], [], []
    chars = max(n(text), 1)

    # S1 测量口径：说了实测就必须给条件
    if re.search(r"实测|测试了|测量|测了|跑了一遍", text):
        has_cond = bool(re.search(r"(设备|仪器|工具|条件|环境|样本|次数|回合|温度|照度|lux|"
                                 r"台架|手机型号|色卡|分光|测色仪|秒表|\d+\s*次)", text))
        if not has_cond:
            fails.append("S1 说了「实测」但没写条件（设备/环境/样本/次数）——无口径的实测等于编")
        items.append(("S1 测量口径", has_cond, "有口径" if has_cond else "无口径"))
    else:
        items.append(("S1 测量口径", True, "未声称实测"))

    # S2 不确定性：全是整数且无约数词
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    approx = bool(re.search(r"约|左右|±|区间|上下|大概|接近|不到|超过", text))
    ints_only = all("." not in x for x in nums) if nums else True
    if len(nums) >= 6 and ints_only and not approx:
        warns.append(f"S2 {len(nums)} 个数字全是整数且无「约/左右/±」——像编的精确")
    items.append(("S2 不确定性", approx or not ints_only, "有区间/约数" if (approx or not ints_only) else "全是整数"))

    # S3 适用边界
    boundary = bool(re.search(r"适用|不适合|如果你|例外|看情况|取决于|对你没用", text))
    if not boundary:
        warns.append("S3 没写适用边界（谁该在意/谁可以不管）——没有边界等于没有判断")
    items.append(("S3 适用边界", boundary, "有" if boundary else "无"))

    # S4 反例/转折
    contrast = bool(re.search(r"但|然而|反例|也有|例外|反过来|不过", text))
    if not contrast:
        warns.append("S4 全文无反例或转折——只证不伪，不是论证")
    items.append(("S4 反例", contrast, "有" if contrast else "无"))

    # S5 可复现：声明实操类就要有步骤
    is_howto = bool(re.search(r"步骤|第一步|照着|这样设置|点击", text))
    has_step = bool(re.search(r"(^|\n)\s*\d[.、)]|第[一二三]步", text))
    if is_howto and not has_step:
        warns.append("S5 像实操类但没有编号步骤——读者照着做不了")
    items.append(("S5 可复现", (not is_howto) or has_step, "有步骤" if has_step else "无"))

    # S6 可证伪（2026-11-27 CEO「要科学」）：结论必须写明"什么情况下我错"。
    # 没有可证伪句的结论不可反驳，也就不是判断，只是态度。
    falsifiable = bool(re.search(
        r"证伪|打我脸|如果.{0,24}就(?:说明|证明|算)我(?:错|说错)|不成立|反过来验证|"
        r"你可以(?:自己)?(?:量|试|验|查)", text))
    if not falsifiable:
        warns.append("S6 没写可证伪条件——读者拿什么反驳你？补一句「如果…就说明我错了」")
    items.append(("S6 可证伪", falsifiable, "有" if falsifiable else "无"))

    # S7 自我代价（人味闸）：强判断必须配一句自己付的代价
    self_cost = bool(re.search(
        r"我(?:原来|一开始|最初)?(?:错|走错|以为错)|我为此|代价(?:是|我)|"
        r"我(?:也)?踩(?:过|了)|栽过|吃过(?:亏|亏)|得罪|我不(?:得|能)不承认", text))
    if not self_cost:
        warns.append("S7 没有自我代价句——强判断不配代价，读起来像总结，不像人做的判断")
    items.append(("S7 自我代价", self_cost, "有" if self_cost else "无"))

    # R1 句长节奏（可读性）：连续 3 句长度接近＝念经。
    # 只在中长文上判（<800 字的快评句子本来就短，容易误判）。
    sents = [x for x in re.split(r"[。！？]", re.sub(r"[#>*`]", "", text)) if len(x.strip()) >= 4]
    flat = 0
    if len(sents) >= 12:
        for i in range(len(sents) - 2):
            a, b, c = (len(sents[i]), len(sents[i + 1]), len(sents[i + 2]))
            if max(a, b, c) - min(a, b, c) <= 5:
                flat += 1
    if flat >= 4:
        warns.append("R1 有 %d 处连续三句长度接近——句长没起伏，读起来像念稿" % flat)
    items.append(("R1 句长节奏", flat < 4, "有起伏" if flat < 4 else "%d 处平" % flat))

    return fails, warns, items


AI_STYLE = """# 智能座舱是汽车产业的未来

首先，智能座舱代表了汽车产业的未来方向。随着技术的进步，智能座舱正在成为行业共识。

其次，智能座舱提升了用户体验。智能座舱通过人机交互，让用户感受到科技的魅力。

再次，智能座舱推动产业升级。智能座舱是车企差异化竞争的关键所在。

此外，智能座舱还带来了商业模式创新。智能座舱为软件订阅提供了新可能。

最后，智能座舱是大势所趋。随着技术的进步，智能座舱必将迎来更广阔的发展空间。

总而言之，智能座舱意义深远，未来可期，值得我们共同期待。
"""

HUMAN_STYLE = """# 小米 YU7 把雨刮藏进了二级菜单，下雨天要摸三下

展车上试了三次，雨刮都要点进「车辆设置」再翻一层。按官方界面截图数，
从主屏到雨刮一共 3 步，同价位的另一台是 1 步。

## 这不是极简，是把成本转给了驾驶的人

省下的是主屏一行空间，付出的是雨天 2 秒的分神。我用秒表在最亮和中亮两档
各掐了 5 次，平均 1.8 秒一次，不是感觉，是数的。

## 但它也不是一无是处

把雨刮收进设置之后，主屏确实干净了，卡片区多出 12 毫米的高度给地图。
如果你所在的城市一年下不了几次雨，这个取舍是划算的；常年多雨的地方就别忍了。

## 我会怎么改

保留主屏一个可长按的雨刮图标，长按直接弹档位，不进入设置。这样既不占位，又不用翻层。
"""


def self_test():
    fails = []

    # 1 正控：人写的稿 AI 指纹必须低
    s1, items1 = ai_trace(HUMAN_STYLE)
    if s1 >= RIGOR_FAIL_SCORE:
        fails.append(f"正控[人写] 指纹分 {s1} 过高：{[i for i in items1 if i[1]]}")

    # 2 负控：AI 式稿必须判红
    s2, items2 = ai_trace(AI_STYLE)
    if s2 < RIGOR_FAIL_SCORE:
        fails.append(f"负控[AI 文] 指纹分 {s2} 太低，没抓住：{items2}")
    hits = {i[0] for i in items2 if i[1]}
    for need in ("连接词堆砌", "缺具体物", "升华收尾"):
        if need not in hits:
            fails.append(f"负控[AI 文] 未命中 {need}")

    # 3 科学化：人写稿有口径/边界/反例
    f1, w1, _ = science(HUMAN_STYLE)
    if f1:
        fails.append(f"正控[人写] 科学化被判 FAIL：{f1}")
    if any("S3" in x or "S4" in x for x in w1):
        fails.append(f"正控[人写] 边界/反例被误判：{w1}")

    # 4 负控：说实测但不给条件 → FAIL
    f2, _w2, _ = science("我实测了这台车的屏幕，确实很亮。")
    if not any("S1" in x for x in f2):
        fails.append("负控[S1 无口径] 未判红")

    # 5 负控：全整数无约数 → WARN
    _f3, w3, _ = science("一共 3 步，用了 2 秒，差 5 毫米，共 7 项，读 4 次，改 6 处。")
    if not any("S2" in x for x in w3):
        fails.append("负控[S2 假精度] 未提示")

    # 6 负控：无边界无反例 → 两条 WARN
    _f4, w4, _ = science("这块屏很好用，按键位置合理，颜色也舒服。")
    if not (any("S3" in x for x in w4) and any("S4" in x for x in w4)):
        fails.append("负控[S3/S4 无边界无反例] 未提示")

    # 7 负控：像实操但无步骤 → WARN
    _f5, w5, _ = science("这个功能这样设置就好，步骤很简单，照着做。")
    if not any("S5" in x for x in w5):
        fails.append("负控[S5 无步骤] 未提示")

    # 8 空输入不崩
    if ai_trace("")[0] != 0 or science("")[0] != []:
        pass  # 空输入允许 0 分 / 无 FAIL
    else:
        fails.append("空输入返回异常")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 8/8  (人写 {s1} 分 / AI 文 {s2} 分 / 科学化五条)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.inp:
        ap.print_help()
        return 1

    text = open(a.inp, encoding="utf-8").read()
    score, items = ai_trace(text)
    fails, warns, sitems = science(text)

    if a.json:
        print(json.dumps({"ai_score": score, "ai_items": items,
                          "science_fails": fails, "science_warns": warns,
                          "science_items": sitems}, ensure_ascii=False, indent=1))
        return 1 if (fails or score >= RIGOR_FAIL_SCORE) else 0

    print(f"AI 结构指纹：{score}/100（≥{RIGOR_FAIL_SCORE} 判红）")
    for name, hit, why in items:
        print(f"  {'命中' if hit else '正常'}  {name:8} {why}")
    print(f"\n科学化：FAIL {len(fails)} / WARN {len(warns)}")
    for x in fails:
        print(f"  FAIL {x}")
    for x in warns:
        print(f"  WARN {x}")

    bad = bool(fails) or score >= RIGOR_FAIL_SCORE
    if bad:
        print("\n结论：这篇不能发。AI 骨架＋无证据＝无脑 AI 文。", file=sys.stderr)
        return 1
    print("\nPASS 像人写的，且论点有证据。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
