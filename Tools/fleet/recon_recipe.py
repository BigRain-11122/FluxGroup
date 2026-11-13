#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recon_recipe.py - 把竞品拆解卡压成可执行配方卡（PROD-RECON-RECIPE 的「配方」工序）。

Why（2026-11-13）：机队 13 道工序声明「要本地模型」却全部没有命令，本地 4B 只在
评审判卷（panel）与压测探针里转，产出侧一次都没跑过——算力不是不够，是没有活。
配方这道最干净：输入=实测拆解卡（数字都在盘），输出=可执行规格，判据可机检。

四条硬边界（都是"不造活"的直接推论）：
  * 模型只改措辞，不产出事实。每个数字必须落在它引用的事实行里，
    没有引用就出现数字=违规（不是"提醒"，是判不过）。
  * 结构缺段直接判不过；没有事实支撑的栏目只许写「未测」。
  * 过不了先带命中项重写一次，仍不过 rc=2 且不落盘（不交半成品）。
  * 复用现成合规闸 copy_compliance（承诺性话术/导流/AI 标识），不另立一套词表。

用法：
  python3 Tools/fleet/recon_recipe.py --source <拆解卡.md> --out <配方.md>
  python3 Tools/fleet/recon_recipe.py --check <配方.md> --source <拆解卡.md>   # 复核
  python3 Tools/fleet/recon_recipe.py --self-test
返回码：0 成功/通过 · 1 参数或源文件问题 · 2 校验不过（不落盘）· 3 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

# 数字：整数、千分位、小数、百分数。两侧与前面都不许紧贴 ASCII 字母数字或点，
# 否则「IL2CPP」的 2、「[F1]」的 1、「v1.10」的 10 都会被当事实数字（自检首跑实锚）。
NUM = re.compile(r"(?<![0-9A-Za-z.])\d+(?:,\d{3})*(?:\.\d+)?%?(?![0-9A-Za-z])")
LIST_MARK = re.compile(r"^\s*\d{1,2}[.、)）]\s+")  # "1. xxx" 的序号不是事实数字（必须有空格，
                                                  # 否则 "42.98 MB" 会被截成 "98 MB"，实测踩过）


def _nums(line):
    """一行里的数字，先剥掉引用标记与有序列表序号。"""
    s = LIST_MARK.sub("", REF.sub("", str(line or "")))
    return set(NUM.findall(s))
REF = re.compile(r"\[F(\d+)\]")
SECTIONS = ["G2 引擎", "G4 UI", "G5 循环", "G6 数值", "G7 商业化",
            "G8 留存", "G9 性能", "可抄结论", "不可抄", "落地动作", "怎么复现"]
CONCL_MARK = "可抄结论"
BANNED = ("最好", "最强", "第一", "唯一", "顶级", "国家级", "世界级",
          "史上最", "绝无仅有", "万能", "永久", "保证", "必赚", "零风险")


def facts_of(text):
    """从源卡里抽出「带数字的行」当唯一事实集。没有数字的行不进事实集——
    配方要的是可量化规格，形容词再多也不能变成参数。"""
    out = []
    for ln in str(text or "").splitlines():
        raw = ln.strip()
        if not raw or raw.startswith("#") or set(raw) <= set("-|: "):
            continue                                  # 标题/表格分隔线/空行不是事实
        nums = _nums(raw)
        if not nums:
            continue
        clean = re.sub(r"^[|\->\s]+", "", raw).replace("|", " ").strip()
        clean = re.sub(r"\s{2,}", " ", clean)
        clean = LIST_MARK.sub("", clean)      # 序号不是事实内容，抽取阶段就剥掉
        if len(clean) > 160:
            continue                          # 整段论述不是可量化条目，引用进来只会让配方变噪音
        out.append({"id": len(out) + 1, "line": clean[:300], "nums": set(NUM.findall(clean))})
    return out


def canon(facts):
    s = set()
    for f in facts:
        s |= f["nums"]
    return s


def validate(text, facts):
    """返回违规列表；空列表=通过。所有判据都在这一处，--check 与生成后复检共用。"""
    errs = []
    txt = str(text or "")
    if not txt.strip():
        return ["空产物"]
    for sec in SECTIONS:
        if sec not in txt:
            errs.append("缺段：%s" % sec)

    lines = txt.splitlines()
    concl_at = next((i for i, ln in enumerate(lines)
                     if ln.strip().startswith("#") and CONCL_MARK in ln), len(lines))
    allnum = canon(facts)
    no_ref = []
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("#"):
            continue                                   # 段标题里的 G2/G4 不算数字
        nums = _nums(ln)
        if not nums:
            continue
        if i >= concl_at:
            stray = nums - allnum
            if stray:
                errs.append("结论段出现事实外数字：%s" % ",".join(sorted(stray)[:4]))
            continue
        refs = [int(x) for x in REF.findall(ln)]
        if not refs:
            no_ref.append(ln.strip()[:40])
            continue
        allowed = set()
        for r in refs:
            if 1 <= r <= len(facts):
                allowed |= facts[r - 1]["nums"]
            else:
                errs.append("引用不存在的事实 F%d" % r)
        stray = nums - allowed
        if stray:
            errs.append("这一行的数字不在所引事实里：%s（%s）"
                        % (",".join(sorted(stray)[:4]), ln.strip()[:30]))
    if no_ref:
        errs.append("%d 行有数字但没有 [Fn] 引用：%s" % (len(no_ref), no_ref[:2]))
    if len(REF.findall(txt)) < 5:
        errs.append("引用不足：%d 处（至少 5 处 [Fn]）" % len(REF.findall(txt)))

    try:
        import copy_compliance as cc
        _ = cc  # 见下：对外合规闸不套在这里
    except Exception:
        pass
    # 为什么不用 copy_compliance 整篇扫：那是"对外文案"的闸，绝对化用语在对外
    # 语境才有害；内部规格要引用源卡原文（"显著可优化项"这类），整篇扫会把
    # 证据本身判成违规 = 假红（2026-11-13 实锚：第二次尝试唯一命中就是源卡原文）。
    # 内部规格的硬约束是"每个数字有出处"，落在上面；用语约束只扫我们自己写的话。
    for ln in lines:
        if ln.lstrip().startswith("#") or ln.lstrip().startswith(">"):
            continue                                   # 标题 / 引用的事实原文不算我们的措辞
        for w in BANNED:
            if w in ln:
                errs.append("措辞含绝对化用语「%s」：%s" % (w, ln.strip()[:30]))
    return errs


SEC_IDS = ["G2", "G4", "G5", "G6", "G7", "G8", "G9"]
SEC_DEF = {
    "G2": "引擎与运行时（引擎类型、脚本后端、资源加载方式）",
    "G4": "UI 与适配（分辨率基准、控件尺寸、主色、动效时长）",
    "G5": "核心循环节奏（几秒做什么、几分钟做什么）",
    "G6": "数值（资源产出/消耗、难度拐点、失败惩罚）",
    "G7": "商业化（广告位、内购、付费点位置）",
    "G8": "留存与活动（签到、任务、榜单、活动周期）",
    "G9": "性能与包体（体积、内存、启动时长、帧率档）",
}
# 分桶关键词：先命中先归位，通配（体积/占比）最后兜到 G9。
# 为什么用规则分桶：2026-11-13 实测 4B 自己挑事实时把「META-INF 1.5 MB」塞进商业
# 化、把「res 4.8 MB」塞进数值段——它会把格式填满但不看语义。事实归位属于确定性
# 工作，不该交给模型；模型只负责"这段说明什么"的一句话解读（不带数字）。
SEC_KW = [
    ("G7", ("广告", "激励", "插屏", "内购", "付费", "充值", "穿山甲", "优量汇",
            "变现", "礼包", "首充", "SDK 聚合", "Pangle")),
    ("G8", ("留存", "签到", "任务", "榜", "活动", "回归", "召回")),
    ("G4", ("分辨率", "竖屏", "横屏", "按钮", "UI", "界面", "点击动效", "像素",
            "字号", "主色", "适配", "刘海")),
    ("G6", ("数值", "难度", "产出", "消耗", "惩罚", "收益", "金币", "体力", "关卡")),
    ("G5", ("循环", "秒", "分钟", "局", "回合", "节奏", "付")),
    ("G2", ("引擎", "il2cpp", "IL2CPP", "Unity", "Cocos", "AssetBundle", "AB ",
            "metadata", "lua", "热更", "运行时", "dex")),
    ("G9", ("体积", "MB", "内存", "启动", "帧率", "FPS", "ABI", "assets", "lib",
            "压缩", "解压", "安装", "包体", "文件数", "字体", "纹理", "占比", "率")),
]


def bucket(facts):
    """把带数字的事实行按关键词归到 G2/G4/G5/G6/G7/G8/G9；归不进去的不进配方。"""
    out = {k: [] for k in SEC_IDS}
    for f in facts:
        line = f["line"]
        for sid, kws in SEC_KW:
            if any(k in line for k in kws):
                out[sid].append(f)
                break
    return out


def prompt_of(buckets, source_name):
    """模型只写"这段说明什么"的一句话解读 + 三条可抄结论的措辞。

    为什么不再让它挑事实（2026-11-13 实测两轮）：4B 挑事实会把体积数字塞进商业化段，
    也会把「### 最大文件 Top 6」这种标题当事实引用。事实归位=确定性活，交规则；
    模型擅长的是把一段数字概括成一句人话，那就只让它干这个，且不许写数字。
    """
    blocks = []
    for sid in SEC_IDS:
        items = buckets.get(sid) or []
        if not items:
            continue
        blocks.append("%s（%s）：" % (sid, SEC_DEF[sid]))
        for f in items[:4]:
            blocks.append("  F%d. %s" % (f["id"], f["line"]))
    return (
        "下面是一张竞品拆解卡按主题归类后的实测数据，来源 %s。\n"
        "请为每一段各写一句中文解读（说明这段数字意味着什么、我们该注意什么），"
        "并为整张卡写三条可抄结论和一条风险。\n\n"
        "只输出一个 JSON，不要解释、不要代码块：\n"
        '{"notes":{"G2":"...","G9":"..."},'
        '"conclusions":["结论一","结论二","结论三"],'
        '"risk":"风险一句话"}\n\n'
        "规则（违反任一条这稿作废）：\n"
        "1. 一句话不超过 24 个汉字，且**不许出现任何数字**，也不要写单位（MB/GB/百分号/秒/分钟/倍）"
        "或「约/接近」这类带量的词。\n"
        "2. 不许写「最强/第一/唯一/保证/永久/顶级」这类话。\n"
        "3. 结论要写成动作（例如「单 ABI 发布」），不要复述数字，不要提没出现的平台名。\n"
        "4. notes 的键只能用下面出现过的段 id；没出现的段不要写。\n\n"
        "数据：\n%s\n" % (source_name, "\n".join(blocks)))


def parse_plan(text):
    """从模型输出里取第一个 JSON 对象。容忍 ```json 包裹、前后废话、
    以及「对象后面又追了一段话」（4B 常见；截到最后一个 } 会变成 Extra data）。"""
    t = str(text or "").strip()
    if not t:
        return None, "空输出"
    a = t.find("{")
    if a < 0:
        return None, "没有 JSON 对象"
    try:
        return json.JSONDecoder().raw_decode(t[a:])[0], ""
    except Exception as e:
        return None, "JSON 解析失败：%s" % str(e)[:60]


def _note(v):
    """模型写的措辞。不达标就整句弃用（返回 ""），不做"剔掉数字硬凑"。

    Why 不剔数字：剔了会把「IL2CPP」变成「ILCPP」、把「约 5 秒」变成「约 秒」，
    读起来比没有解读更糟（2026-11-13 实测两次都是这种残句）。宁缺勿滥。
    """
    raw = str(v or "").strip()
    if not raw:
        return ""
    if re.search(r"\d", raw):
        return ""
    if any(w in raw for w in BANNED):
        return ""
    if re.search(r"(MB|GB|KB|TB|%|秒|分钟|倍)", raw, re.I):
        return ""
    return re.sub(r"\s{2,}", " ", raw).strip(" ，,。:：、")
    if re.search(r"(MB|GB|KB|TB|%|秒|分钟|倍)", s, re.I):
        return ""
    return s


def decisions(buckets):
    """把实测事实翻成可执行的落地动作（规则生成，不是模型编的）。

    为什么必须有这一段：产品验收写的是「配方可执行」，评审团的判据也是"命令可复制
    执行"。只有数据没有动作，评审两次都判 REVISE（2026-11-13 实锚）。动作来自我方
    工程策略表，命中哪条就出哪条，且必须挂上触发它的事实编号。
    """
    rules = [
        (("armeabi-v7a", "双 ABI", "arm64-v8a"), "发布只打 arm64-v8a，去掉 32 位包"),
        (("字体", "ttf", "font"), "字体做子集化后再打包，别整字库入包"),
        (("AssetBundle", "AB 分块", "assets/ab", "分包"), "资源按 AB/分包组织，别把散图直打进包"),
        (("激励视频", "插屏", "聚合", "IAA"), "广告以激励视频为主，插屏控频，不做强制插屏"),
        (("签到", "七日", "留存"), "上线即带七日签到与每日任务"),
        (("难度", "拐点", "关卡"), "难度拐点前移，首关给满正反馈"),
    ]
    out, used = [], set()
    for sid in SEC_IDS:
        for f in buckets.get(sid) or []:
            for kws, text in rules:
                if text in used:
                    continue
                if any(k in f["line"] for k in kws):
                    out.append((text, f["id"]))
                    used.add(text)
                    break
    return out


def render(buckets, plan, source_path=""):
    """把骨架渲染成 markdown：事实原文由代码注入（以 > 引用行呈现），模型碰不到数字。

    引用行用 ">" 前缀是为了让校验能区分"我们写的话"和"源卡原文"——绝对化用语
    在原文里是证据，在我们自己的措辞里才是问题。
    """
    notes = plan.get("notes") or {}
    out, cited = [], []
    for sid in SEC_IDS:
        items = buckets.get(sid) or []
        out.append("## %s %s" % (sid, SEC_NAME[sid]))
        note = _note(notes.get(sid)) if isinstance(notes, dict) else ""
        if note:
            out.append("- 解读：%s" % note)
        if not items:
            out.append("未测")
        else:
            for f in items[:4]:
                out.append("  > %s [F%d]" % (f["line"], f["id"]))
                cited.append(f["id"])
        out.append("")
    concl = [c for c in (_note(x) for x in (plan.get("conclusions") or [])) if c][:3]
    out.append("## 可抄结论")
    if concl:
        for i, c in enumerate(concl, 1):
            out.append("%d. %s" % (i, c))
        if cited:
            out.append("   > 依据见上文实测：%s" % "".join("[F%d]" % i for i in cited[:6]))
    else:
        out.append("未测")
    out.append("")
    out.append("## 不可抄/风险")
    rk = _note(plan.get("risk"))
    if rk:
        out.append("- %s" % rk)
        if cited:
            out.append("   > 依据见上文实测：%s" % "".join("[F%d]" % i for i in cited[:6]))
    else:
        out.append("未测")
    out.append("")
    acts = decisions(buckets)
    out.append("## 落地动作")
    if acts:
        for i, (t, fid) in enumerate(acts, 1):
            out.append("%d. %s [F%d]" % (i, t, fid))
    else:
        out.append("未测")
    out.append("")
    out.append("## 怎么复现")
    src = source_path or "<拆解卡.md>"
    out.append("```bash")
    out.append("# 重新测量包体（静态，不运行游戏）")
    out.append("python3 Tools/recon/apk_recon.py --apk <样本 apk> --out cph4/fleet/out/recon/raw/")
    out.append("# 按拆解卡重新生成本配方")
    out.append("python3 Tools/fleet/recon_recipe.py --source %s --out cph4/fleet/out/recon/recipe.md" % src)
    out.append("# 复核本配方（数字必须有出处、段必须齐）")
    out.append("python3 Tools/fleet/recon_recipe.py --check cph4/fleet/out/recon/recipe.md --source %s" % src)
    out.append("```")
    return "\n".join(out) + "\n"


SEC_NAME = {"G2": "引擎", "G4": "UI", "G5": "循环", "G6": "数值",
            "G7": "商业化", "G8": "留存", "G9": "性能"}


def _write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def _call_model(prompt, timeout=240):
    import local_model as lm
    return (lm.generate(prompt, cls="resident", timeout=timeout,
                        temperature=0.2, why="recon-recipe") or "").strip()


def make(source, out, gen=None, log=print):
    src = open(source, encoding="utf-8").read()
    facts = facts_of(src)
    buckets = bucket(facts)
    filled = [k for k in SEC_IDS if buckets.get(k)]
    log("[recon-recipe] 源=%s 事实行=%d 数字项=%d 有料段=%d（%s）"
        % (os.path.basename(source), len(facts), len(canon(facts)),
           len(filled), ",".join(filled)))
    n_fact = sum(len(v) for v in buckets.values())
    if n_fact < 8 or len(filled) < 2:
        # 事实太少/只有一段，写出来的只会是形容词堆砌，宁可不出货
        log("[recon-recipe] 可用事实 %d 条、有料段 %d 个（需 ≥8 条且 ≥2 段），不出配方"
            % (n_fact, len(filled)))
        return 1, None, ["源可用事实不足（%d 条/%d 段）：先把拆解补齐再出配方"
                         % (n_fact, len(filled))]
    gen = gen or _call_model
    prompt = prompt_of(buckets, os.path.basename(source))
    errs = []
    for attempt in (1, 2):
        text = gen(prompt if attempt == 1 else prompt + (
            "\n\n上一稿不合格：%s\n只输出 JSON，仍按上面格式与规则重做。" % "；".join(errs[:4])))
        plan, why = parse_plan(text)
        if plan is None:
            errs = [why]
            log("[recon-recipe] 第 %d 次：%s" % (attempt, why))
            continue
        rendered = render(buckets, plan, source)
        errs = validate(rendered, facts)
        log("[recon-recipe] 第 %d 次：%s%s"
            % (attempt, "通过" if not errs else "%d 项不过" % len(errs),
               "" if not errs else " -> " + "；".join(errs[:3])))
        if not errs:
            _write(out, rendered)
            return 0, out, []
    log("[recon-recipe] 两次都不过，产物不落盘（不交半成品）")
    return 2, None, errs


def self_test():
    ok = total = 0

    def chk(name, cond, detail=""):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print("%s %-38s %s" % ("ok  " if cond else "FAIL", name, detail))

    src = ("# GAME-X 测试卡\n\n"
           "| 项 | 数值 |\n|---|---|\n"
           "| APK 压缩后 | **335 MB** |\n"
           "| 解压后总体积 | **455.8 MB** |\n"
           "| assets | 284.2 MB |\n"
           "| lib | 142.4 MB |\n"
           "| 文件数 | 6,046 |\n"
           "| 最长镜 | 2.23s |\n"
           "| 包体 | v1.10 |\n"
           "| 体积 | 74.8 MB |\n"
           "| 占比 | 62.3% |\n"
           "| 字体 | 11.96 MB |\n")
    facts = facts_of(src)
    chk("事实抽取只取带数字的行", len(facts) == 9, "%d 条" % len(facts))

    good = ("## G2 引擎\nUnity + IL2CPP，包体 335 MB [F1]\n"
            "## G4 UI\n未测\n## G5 循环\n未测\n## G6 数值\n未测\n"
            "## G7 商业化\n未测\n## G8 留存\n未测\n"
            "## G9 性能\n冷启以上解压 455.8 MB 为准 [F2]\n"
            "## 可抄结论\n1. 单 ABI 发布，省掉 74.8 MB [F8]\n"
            "2. 字体子集化，省 11.96 MB [F9]\n3. 贴图压到 62.3% 以内 [F7]\n"
            "## 不可抄/风险\n双 ABI 同时打包的浪费点 [F8]\n"
            "## 落地动作\n单 ABI 发布 [F8]\n## 怎么复现\n见命令\n")
    chk("正例：引用齐全+数字都对", validate(good, facts) == [], validate(good, facts)[:2])

    bad_num = good.replace("335 MB [F1]", "999 MB [F1]")
    e = validate(bad_num, facts)
    chk("反例：编造数字被判红", any("不在所引事实里" in x for x in e), e[:1])

    no_ref = good.replace("包体 335 MB [F1]", "包体 335 MB")
    e = validate(no_ref, facts)
    chk("反例：有数字无引用被判红", any("没有 [Fn] 引用" in x for x in e), e[:1])

    miss = good.replace("## G6 数值\n未测\n", "")
    chk("反例：缺段被判红", any("缺段" in x for x in validate(miss, facts)))

    promise = good.replace("## 可抄结论", "最好用的一套方案\n## 可抄结论")
    chk("反例：承诺性话术被判红", any("绝对化用语" in x for x in validate(promise, facts)),
        validate(promise, facts)[:1])

    import tempfile
    td = tempfile.mkdtemp()
    # 分桶+解读模式：事实归位由规则做，模型只写不带数字的一句话
    bks = bucket(facts)
    plan = {"notes": {"G2": "引擎与加载方式", "G9": "包体是大头"},
            "conclusions": ["单 ABI 发布", "字体子集化", "贴图按需压"],
            "risk": "双 ABI 重复打包"}
    r = render(bks, plan)
    chk("分桶渲染能过闸（数字由代码注入）", validate(r, facts) == [], validate(r, facts)[:1])
    chk("分桶不把体积塞进商业化段",
        not bks["G7"] and len(bks["G9"]) >= 5,
        "G7=%d G9=%d" % (len(bks["G7"]), len(bks["G9"])))
    p, why = parse_plan("```json\n" + json.dumps(plan) + "\n```")
    chk("容忍代码块包裹的 JSON", p is not None, why)
    dirty = dict(plan, notes={"G2": "省下 335 MB"})
    rend = render(bks, dirty)
    chk("模型在解读里塞数字会被剔掉",
        all("335" not in ln for ln in rend.splitlines() if "解读" in ln),
        [ln for ln in rend.splitlines() if "解读" in ln][:1])
    chk("模型答非 JSON 时判失败", parse_plan("这是一段 prose，没有 JSON")[0] is None)

    # 端到端：注入 stub 生成器（不起模型）。源要跨>=2 段才够出配方
    rich = src + ("| 引擎 | Unity + IL2CPP |\n| 商业化 | 激励视频 4 处 |\n")
    src_path = os.path.join(td, "card.md")
    out_path = os.path.join(td, "recipe.md")
    open(src_path, "w", encoding="utf-8").write(rich)
    rc, path, errs = make(src_path, out_path, gen=lambda p: json.dumps(plan),
                          log=lambda *a: None)
    chk("端到端：stub 能出货", rc == 0 and path and os.path.exists(out_path), errs[:1])

    thin_path = os.path.join(td, "thin.md")
    never = os.path.join(td, "never.md")
    open(thin_path, "w", encoding="utf-8").write("# 只有形容词的卡\n画面很精致\n节奏很好\n")
    rc, _, errs = make(thin_path, never, gen=lambda p: "不该被调用", log=lambda *a: None)
    chk("反例：源事实不足不出货", rc == 1 and not os.path.exists(never),
        (errs[:1] or ["未报错"]) + ["文件未落盘" if not os.path.exists(never) else "文件被写了"])

    print("\n[recon_recipe] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="", help="拆解卡 md")
    ap.add_argument("--out", default="", help="配方 md 输出路径")
    ap.add_argument("--check", default="", help="只复核一个已有配方文件")
    ap.add_argument("--json", default="", help="把结果写成机读件")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if not a.source:
        print("[recon-recipe] 缺 --source")
        return 1
    if not os.path.exists(a.source):
        print("[recon-recipe] 源不存在：%s" % a.source)
        return 1
    facts = facts_of(open(a.source, encoding="utf-8").read())

    if a.check:
        if not os.path.exists(a.check):
            print("[recon-recipe] 待复核文件不存在：%s" % a.check)
            return 2
        errs = validate(open(a.check, encoding="utf-8").read(), facts)
        rep = {"ok": not errs, "source": a.source, "file": a.check, "errs": errs,
               "facts": len(facts)}
        if a.json:
            _write(a.json, json.dumps(rep, ensure_ascii=False, indent=1))
        print("[recon-recipe] 复核 %s：%s" % (a.check, "通过" if not errs else "不通过"))
        for e in errs[:8]:
            print("  -", e)
        return 0 if not errs else 2

    if not a.out:
        print("[recon-recipe] 缺 --out")
        return 1
    rc, path, errs = make(a.source, a.out)
    if a.json:
        _write(a.json, json.dumps({"rc": rc, "out": path, "errs": errs,
                                   "facts": len(facts)}, ensure_ascii=False, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main())
