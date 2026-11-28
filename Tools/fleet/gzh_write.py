#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_write.py — 公众号成稿器：拿算力 → 按本周主题写 → 过闸 → 落盘。

CEO 2026-11-27 两条令：
  ① 「每周要有一个主题，围绕主题去写」→ 主题由 gzh_week.py 唯一决定，本器不自选。
  ② 「训练占用了太多的模型，分一个算力和模型出来给公众号」
     → 席位 gzh_writer（qwen3.5:9b-mlx）写进 LOCAL-MODEL-POLICY；
       加载前先抢 gpu_lease("gzh")，训练拿不到同一把锁，两者不同时抢显存。

诚实边界（写在代码里，不靠记性）：
  · 9B 一进 9GB 训练就被换出（2026-11-18 实锚），所以本器**必须独占窗口**，
    抢不到租约就返回 DEFER 并记原因，绝不空转后再宣称"写过"。
  · 模型出的稿子是**初稿**，闸只拦形态与 AI 腔，判不了"好不好"。
    状态只能到 NEEDS-HUMAN，不许自己升级成 READY。

用法：
  python3 Tools/fleet/gzh_write.py --topic "深色模式发灰：不是屏幕问题，是色阶没做" --quadrant 硬核
  python3 Tools/fleet/gzh_write.py --self-test
退出码：0 出稿并通过闸 / 1 今天不在任何一周（季外）/ 2 出稿但闸未过 / 3 缺料或算力让路 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
DRAFTS = os.path.join(GZH, "drafts")
OLLAMA = "http://127.0.0.1:11434"
SEAT = "gzh_writer"
FREE_NEED_MB = 11500          # 9B@8k 加上浏览器/系统的余量，低于此先卸竞品


# ---------------------------------------------------------------- 算力

def _post(path, payload, timeout=30):
    req = urllib.request.Request(OLLAMA + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def resident_models():
    try:
        d = _post("/api/ps", {})
        return [m.get("name") for m in d.get("models") or []]
    except Exception:
        return []


def mem_free_mb():
    try:
        import res_alloc
        return int(res_alloc.mem_free_mb())
    except Exception:
        return -1


def make_room(seat_model, log=print):
    """把竞品常驻模型卸掉，给 9B 腾地方。只卸本机能重载的小档，不动 8788 训练服务。

    为什么必须显式卸：Ollama 不会自动为一个大模型挤走小模型，它会两边都留，
    结果 4B+2B+9B 同时驻留，直接换页——正是 CEO 说的「模型占太多」。
    """
    freed = []
    if mem_free_mb() >= FREE_NEED_MB:
        return freed
    for m in resident_models():
        if m == seat_model:
            continue
        try:
            _post("/api/generate", {"model": m, "keep_alive": 0, "prompt": ""})
            freed.append(m)
            log("[算力] 卸下常驻 %s（给 %s 让内存）" % (m, seat_model))
        except Exception:
            pass
    if freed:
        time.sleep(2)
    return freed


# ---------------------------------------------------------------- 提示词

# 象限 → (kind, 字数区间)。原来一律按 long 出，实操题自然写不到 1500 字就挂结构闸
# （2026-11-28 实锚：实操题 541 字，闸判"太短说不清一件事"）。
QUAD_KIND = {"硬核": ("long", "2000-3500"), "科技": ("long", "1500-2800"),
             "实操": ("short", "800-1500"), "大众": ("short", "600-1200")}


def kind_for(quadrant, kind=None):
    want = (QUAD_KIND.get(quadrant) or ("long", "1200-1800"))[0]
    return want if kind in (None, "auto") else kind


def exemplar_heads(limit=3):
    """从真实语料里取几条小标题当"结构参照"，只给小标题不给正文。

    为什么不给整段：2026-11-17 实锚——整句进 prompt 会被照抄。
    小标题是结构不是句子，风险低；同时在提示词里明写"不许照抄这几条"。
    """
    import glob
    out = []
    for f in (os.path.join(GZH, "ARTICLES.jsonl"),
              os.path.join(os.path.expanduser("~"), "BigLoom", "collect",
                           "ARTICLES-GENERIC.jsonl")):
        if not os.path.exists(f):
            continue
        for ln in open(f, encoding="utf-8"):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if (r.get("genre") or "") not in ("review", "feature", "essay"):
                continue
            for h in (r.get("heads") or [])[:2]:
                h = str(h).strip()
                if 6 <= len(h) <= 26 and not h.endswith(("？", "?")):
                    out.append(h)
            if len(out) >= limit * 2:
                break
    return out[:limit]


def build_prompt(week, season, topic, quadrant, kind):
    import llm_client as L
    kind, span = QUAD_KIND.get(quadrant, ("long", "1200-1800"))
    spec = {
        "硬核": "给可复现的测量/计算方法，给改法，同行能拿去用。",
        "实操": "步骤可照着做，每步说清在哪、点什么、做完会有什么区别。",
        "大众": "给明确取舍，结尾写清什么人适用、什么人不适用。",
        "科技": "一个技术点讲透，落到用户能感知的差别。",
    }.get(quadrant, "把一件事讲透，给可核验的细节。") + "篇幅 %s 字。" % span
    heads_ref = exemplar_heads()
    ref_line = ("【小标题参照（照这个句式与长度，不许照抄原句）】"
                + "｜".join(heads_ref) + "\n") if heads_ref else ""
    return (
        "你在给一个汽车 HMI 视觉设计师写公众号长文初稿。作者身份：专职做汽车座舱视觉设计，"
        "只看一块屏——层级、留白、配色、动效、字体、图标、质感。不聊动力、底盘、空间、油耗。\n\n"
        "【本周主题】%s（%s，%s → %s）\n"
        "【本周为什么写这个】%s\n"
        "【本周关键词】%s\n"
        "【这一篇的题目】%s\n"
        "【类型】%s，篇幅 %s\n\n"
        "%s\n%s"
        "【硬要求】\n"
        "0. 正文必须达到上面给的篇幅区间下限，低于下限视为没写完。\n"
        "1. 第一句不超过 30 字，落到一个具体场景或具体物，不铺垫、不写「随着…」。\n"
        "2. 小标题**恰好 3 到 4 个，超过 4 个直接判不合格**；必须是断言式短句，禁止疑问句。\n"
        "3. 每段 60-100 字，最长不超过 120 字。\n"
        "4. 每 300 字至少一个可核验细节（比例、尺寸、色值、次数、参数），"
        "**全文数字密度不低于每千字 10 个**，数字必须带口径，"
        "写清是谁测的、什么条件。\n"
        "5. 至少一处「我自己的」经历或代价，但不许编造实测（不写我开了几万公里、我拆了车）。\n"
        "6. 必须写出最强反对意见，并说明你为什么不让步。\n"
        "7. 结尾给明确建议，写清什么人不该听你的。\n"
        "8. 全文至少一处自我代价（我原来错了/我为此多花了钱/这句话会得罪人）。\n"
        "9. 不要写「总而言之」「首先其次」「赋能」「助力」这类词，不要写口号结尾。\n"
        "10. **不许引用任何标准或法规编号**（ISO/SAE/ECE/GB/NHTSA/DIN 一律不写）。"
        "要表达\"规范要求\"就写\"有些厂商的规范要求\"或\"业内常见做法\"；"
        "唯一例外是 WCAG 2.1，且必须说明它是网页对比度标准。"
        "（实测：9B 会凭空写出 ISO 15008 / ISO 13485 / ECE R124 三套假条款。）\n"
        "11. **每个数字后面必须紧跟口径**（据某官方/据公开资料/估算/我量的），"
        "拿不到口径就不写这个数字——宁可少一个数，也不要一个无源的数。\n"
        "12. 必须给一个**读者能自己做的检验**：编号步骤，或写明「你可以自己量/自己查」怎么做。\n"
        "13. 必须写明**谁不适用**（如果…这篇你用不上）。\n"
        "14. 必须有一句**明确的取舍**（我选/我建议/宁可…也不）。\n"
        "15. 只输出文章本身：第一行是 Markdown 一级标题，不要任何解释、不要前后缀。\n"
        % (week["主题"], week["week"], week["from"], week["to"],
           week.get("为什么这周写这个") or "", "、".join(week.get("关键词") or []),
           topic, quadrant, spec, ref_line, L.gzh_block())
    )


# ---------------------------------------------------------------- 闸

def run_gate(script, path, *extra):
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, script), "--in", path, *extra],
                           capture_output=True, text=True, timeout=180)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 9, "闸跑不起来：%s" % e


# ---------------------------------------------------------------- 主流程

def write_one(week, topic, quadrant, kind="long", attempts=2, budget_s=420,
              slug=None, log=print):
    import gpu_lease
    import llm_client as L

    kind = kind_for(quadrant, kind)   # 体裁决定篇幅与闸模式，别一律按长文
    seat_model = L._model_for(SEAT)
    # 2026-11-27 实锚：9B 在本机（32GB，桌面应用已占十几 GB）加载的那 39 秒里
    # swap +2100MB、swapouts +135432 页。所以出稿前必须先问内存闸：
    # 装不下就不许用 9B，降到 4B 出稿（质量差一档，但机器不会换页）。
    try:
        import mem_gate
        need_gb = 9.1 if "9b" in str(seat_model).lower() else 3.3
        _d = mem_gate.decide(need_gb)
        if _d.get("verdict") != "OK":
            if need_gb >= 9.0:
                seat_model = "qwen3.5:4b-mlx"
                log("[算力] 9B 装不下（%s，上限 %.1fGB）→ 降到 4B 出稿"
                    % (_d.get("note") or _d.get("verdict"), _d.get("model_max_gb") or 0))
            else:
                log("[算力] 连 4B 都装不下（%s）→ 本拍不出稿" % (_d.get("note") or ""))
                return 3, {"why": "内存不足：" + str(_d.get("note") or _d.get("verdict"))}
    except Exception as e:
        log("[算力] 内存闸不可用（%s）→ 按 4B 保守出稿" % str(e)[:40])
        seat_model = "qwen3.5:4b-mlx"
    deadline = time.time() + budget_s   # 2026-11-27 实锚：无预算时两轮烧了 59 分钟
    got, why = gpu_lease.acquire("gzh", ttl_s=1500, wait_s=420)
    if not got:
        log("[算力] 让路：%s" % why)
        return 3, {"why": "算力让路：" + why}
    try:
        make_room(seat_model, log=log)
        log("[算力] 席位 %s → %s ｜ 可用内存 %dMB" % (SEAT, seat_model, mem_free_mb()))
        prompt = build_prompt(week, None, topic, quadrant, kind)
        last = None
        for i in range(1, attempts + 1):
            left = deadline - time.time()
            if left < 60:
                log("[预算] 剩 %.0fs，不再重写（宁可交初稿加备注，也不许把时段烧光）" % left)
                break
            r = L.generate(prompt, cls=SEAT, model=seat_model, keep_alive="20m",
                           num_predict=4200,
                           timeout=min(900, int(left)), think=False)
            if not r.get("ok"):
                log("[模型] 第 %d 次失败：%s" % (i, r.get("why")))
                last = {"why": r.get("why") or "模型失败"}
                if r.get("rc") in (3, 5):
                    return 3, last
                continue
            text = (r.get("text") or "").strip()
            if len(text) < 400:
                log("[模型] 第 %d 次产出过短（%d 字），判废" % (i, len(text)))
                last = {"why": "产出过短 %d 字" % len(text)}
                continue
            # 剥掉模型可能带的前后缀（只留第一个 # 标题之后）
            k = text.find("\n# ")
            if k > 0:
                text = text[k + 1:]
            text = fix_title(text, topic)
            text = polish_markdown(text)   # 格式先修，再进闸
            d = date.today().isoformat()
            outdir = os.path.join(DRAFTS, d) if not slug else os.path.join(DRAFTS, d, slug)
            os.makedirs(outdir, exist_ok=True)
            path = os.path.join(outdir, "draft.md")
            open(path, "w", encoding="utf-8").write(text + "\n")
            rc_s, out_s = run_gate("gzh_article_check.py", path,
                                   "--mode", "long" if kind == "long" else "short")
            rc_r, out_r = run_gate("gzh_rigor_check.py", path)
            # 第三闸：编标准/编履历。2026-11-27 实测 9B 会凭空写 ISO/SAE/NHTSA 条款，
            # 严谨闸（AI 指纹）判它 12/100 通过——所以必须单独一道，且必须进通过条件。
            rc_a, out_a = run_gate("gzh_authority_check.py", path)
            gates = os.path.join(outdir, "gates.txt")
            open(gates, "w", encoding="utf-8").write(
                "# %s 模型初稿闸报告（席位 %s / %s）\n\n## 结构闸 rc=%d\n%s\n"
                "## 严谨闸 rc=%d\n%s\n## 权威闸 rc=%d\n%s\n"
                % (d, SEAT, seat_model, rc_s, out_s, rc_r, out_r, rc_a, out_a))
            man = {"date": d, "slug": slug or "main",
                   "week": week["week"], "week_theme": week["主题"],
                   "topic": topic, "quadrant": quadrant, "kind": kind,
                   "writer": "%s/%s" % (SEAT, seat_model), "attempt": i,
                   "chars": len(text),
                   "gate_rc": {"struct": rc_s, "rigor": rc_r, "authority": rc_a},
                   # 模型初稿最高只能到 NEEDS-HUMAN：闸不判好坏，人判
                   "status": "NEEDS-HUMAN",
                   "draft": os.path.relpath(path, ROOT),
                   "gates": os.path.relpath(gates, ROOT)}
            json.dump(man, open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            ok = (rc_s == 0 and rc_r == 0 and rc_a == 0)
            log("[稿] %s ｜ %d 字 ｜ 结构闸 %s ｜ 严谨闸 %s ｜ 权威闸 %s"
                % (man["draft"], len(text), "过" if rc_s == 0 else "未过",
                   "过" if rc_r == 0 else "未过", "过" if rc_a == 0 else "未过"))
            if ok:
                return 0, man
            last = man
            log("[模型] 第 %d 次未过闸，带上命中项重写" % i)
            prompt = build_prompt(week, None, topic, quadrant, kind) + (
                "\n\n【上一版被闸拦下的原因，重写时逐条改掉】\n"
                + (out_s + out_r + out_a)[-1400:])
        return 2, last or {"why": "未出稿"}
    finally:
        gpu_lease.release("gzh")


BOLD_LINE = re.compile(r"^\*\*(.{2,40}?)\*\*\s*$")
HEAD_ANY = re.compile(r"^(#{3,6})\s+(.*)$")


def fix_title(text, topic=None):
    """标题字数不合规时，若给定题目在 16-32 字内就用它。

    2026-11-28 实锚：给定题目 24 字，模型写成 14 字（「同一块屏，字重与行高的生死账」），
    闸判「标题 14 字，不在 16-32」。题目是我们自己定的，比模型临时缩的标题更可靠。
    """
    lines = (text or "").splitlines()
    if not lines or not lines[0].startswith("# "):
        return text
    cur = lines[0][2:].strip()
    if 16 <= len(cur) <= 32:
        return text
    if topic and 16 <= len(topic) <= 32:
        lines[0] = "# " + topic.strip()
        return "\n".join(lines)
    return text


def polish_markdown(text):
    """把模型稿的格式修成闸能认的形态，不改内容。

    2026-11-28 实锚：9B 的小标题写成**加粗行**而不是 `##`，闸数出 0 个小标题；
    段落中位 143 字，一段塞三四个判断。这两条都是格式，不是文采问题——
    所以可以机械修，修完闸才有资格评内容。

    只做四件：①加粗整行→二级小标题 ②###→## ③超长段按句号切成 ≤110 字 ④只留一个 H1。
    """
    lines = (text or "").splitlines()
    out, seen_h1 = [], False
    for ln in lines:
        t = ln.rstrip()
        m = HEAD_ANY.match(t)
        if m:
            t = "## " + m.group(2).strip()
        m2 = BOLD_LINE.match(t.strip())
        if m2 and len(out) > 2:
            t = "## " + m2.group(1).strip()
        if t.startswith("# "):
            if seen_h1:
                t = "## " + t[2:].strip()
            else:
                seen_h1 = True
        out.append(t)

    # 小标题上限 3：超出的把标题降成普通段（正文一字不少，只是不再分节）。
    # 实测模型稳定写 5-6 节。**上限必须取短评门槛（1-3）而不是长文门槛（3-4）**：
    # 2026-11-28 实锚——这里原来写 4，短评模式要求 ≤3，于是每篇短稿都必红，
    # 而 3 同时满足长文 3-4，所以取 3 是唯一两边都不误杀的值。
    keep, out2 = 0, []
    for ln in out:
        if ln.startswith("## "):
            keep += 1
            if keep > 3:
                out2.append(ln[3:].strip())
                out2.append("")
                continue
        out2.append(ln)
    out = out2

    # 超长段按句切开（保留标点），每块尽量 ≤110 字
    res = []
    for ln in out:
        t = ln.strip()
        if not t or t.startswith("#") or len(re.sub(r"\s", "", t)) <= 110:
            # 阈值必须与闸一致：闸的红线是「段 > 110 字」，这里原来写 120，
            # 于是 111-120 字的段落被原样放过，闸照样判红（2026-11-28 实锚：残留一段 132 字）。
            res.append(ln)
            continue
        parts = re.split(r"(?<=[。！？])", t)
        buf = ""
        for part in parts:
            if not part:
                continue
            if len(re.sub(r"\s", "", buf + part)) > 110 and buf:
                res.append(buf.strip())
                res.append("")
                buf = part
            else:
                buf += part
        if buf.strip():
            res.append(buf.strip())
    return "\n".join(res).strip() + "\n"


def expand_one(path, target=1800, budget_s=300, log=print):
    """定向扩写：只补小节，不重写已有内容。

    2026-11-28 实测：9B 自然篇幅 1000-1300 字，离深稿 1500 字门槛总差一截；
    整篇重写三轮也上不去。所以改成"在已有的骨架上补两节"——原文不动，
    只追加 1-2 个符合本周主题的新小节，写完再打磨+过闸。
    """
    import gpu_lease
    import llm_client as L
    f = os.path.join(path, "draft.md")
    body = open(f, encoding="utf-8").read()
    if len(re.sub(r"\s", "", body)) >= target:
        return True, "已够长"
    got, why = gpu_lease.acquire("gzh", ttl_s=900, wait_s=300)
    if not got:
        return False, "算力让路：" + why
    try:
        heads = [ln[3:].strip() for ln in body.splitlines() if ln.startswith("## ")]
        if len(heads) >= 4:
            return False, "小标题已满 4 个，再加会超上限"
        prompt = (
            "下面是一篇公众号文章（汽车 HMI 视觉设计方向）。请**只追加一个小节**，"
            "不要改动已有内容，不要重写标题。\n"
            "要求：\n"
            "1. 新小节用 `## ` 开头，句式与已有小标题一致（断言式短句，禁止疑问句）。\n"
            "2. 每个小节 200-320 字，段落 60-100 字。\n"
            "3. 必须给可核验的细节（比例/尺寸/色值/条款），数字带口径。\n"
            "4. 不许编造实测与项目经历；**不许写任何标准编号**（ISO/SAE/ECE/GB 都不行）。\n"
            "5. 直接输出新小节，不要任何解释。\n\n"
            "已有小标题：%s\n\n正文：\n%s\n" % ("｜".join(heads), body[-3000:]))
        r = L.generate(prompt, cls=SEAT, keep_alive="2m", num_predict=1600,
                       timeout=max(120, budget_s), think=False)
        if not r.get("ok"):
            return False, r.get("why") or "模型失败"
        add = polish_markdown(r.get("text") or "")
        add = "\n".join(ln for ln in add.splitlines() if not ln.startswith("# "))
        if len(re.sub(r"\s", "", add)) < 150:
            return False, "补写太短"
        open(f, "w", encoding="utf-8").write(body.rstrip() + "\n\n" + add.strip() + "\n")
        log("[扩写] %s → %d 字" % (os.path.basename(path), len(re.sub(r"\s", "", open(f, encoding='utf-8').read()))))
        return True, "已扩写"
    finally:
        gpu_lease.release("gzh")

def polish_dir(path):
    """打磨一篇稿：就地改写 draft.md 并重跑三闸。返回 (rc_struct, rc_rigor, rc_auth)。"""
    f = os.path.join(path, "draft.md")
    raw = open(f, encoding="utf-8").read()
    topic = None
    try:
        man = json.load(open(os.path.join(path, "manifest.json"), encoding="utf-8"))
        topic = man.get("topic")
    except Exception:
        pass
    fixed = polish_markdown(fix_title(raw, topic))
    if fixed != raw:
        open(f, "w", encoding="utf-8").write(fixed)
    mode = "long" if len(fixed) > 1500 else "short"
    rc_s, out_s = run_gate("gzh_article_check.py", f, "--mode", mode)
    rc_r, out_r = run_gate("gzh_rigor_check.py", f)
    rc_a, out_a = run_gate("gzh_authority_check.py", f)
    # 2026-11-28 实锚：打磨后重跑了闸，但**没有把报告写回盘**，于是 gates.txt 里留着
    # 打磨前的数字（811 字 / 0 小标题），而 draft.md 已经是 1175 字 / 4 小标题——
    # 面板上"结构闸未过"描述的根本不是交付出去的那一版。判据必须跟落盘稿一致。
    try:
        gp = os.path.join(path, "gates.txt")
        with open(gp, "w", encoding="utf-8") as fh:
            fh.write("# %s 模型初稿闸报告（打磨后重跑）\n\n" % os.path.basename(path))
            fh.write("## 结构闸 rc=%d\n%s\n## 严谨闸 rc=%d\n%s\n## 权威闸 rc=%d\n%s\n"
                     % (rc_s, out_s, rc_r, out_r, rc_a, out_a))
        mj = os.path.join(path, "manifest.json")
        man = json.load(open(mj, encoding="utf-8"))
        man["gate_rc"] = {"struct": rc_s, "rigor": rc_r, "authority": rc_a}
        man["chars"] = len(re.sub(r"\s", "", fixed))
        man["polished"] = True
        man["gate_mode"] = mode
        json.dump(man, open(mj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:
        log("[闸] 报告回写失败（%s）——但结论已返回，不回退" % str(e)[:40])
    return rc_s, rc_r, rc_a

def self_test():
    import gzh_week
    fails = []

    # 1 提示词必须带本周主题（脱离主题就退回重写，这是 CEO 令的落点）
    w = gzh_week.for_date(date.fromisoformat("2026-12-02"))
    if not w:
        fails.append("自检取不到 W1——周表坏了")
    else:
        p = build_prompt(w, None, "测试题", "硬核", "long")
        if w["主题"] not in p:
            fails.append("提示词没带本周主题")
        if "疑问句" not in p:
            fails.append("提示词没禁疑问式小标题")

    # 2 席位必须解析到 9B（分算力的落点，解析成 4B 等于没分）
    import llm_client as L
    if L._model_for(SEAT) != "qwen3.5:9b-mlx":
        fails.append("席位 %s 没落到 9B（现在是 %s）" % (SEAT, L._model_for(SEAT)))

    # 3 负控：空产出不许被当成出稿成功
    if _looks_done("   "):
        fails.append("负控失效：空白产出被判成出稿")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 3/3（带主题/席位落9B/空白负控）")
    return 0


def _looks_done(text):
    return len((text or "").strip()) >= 400


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default=None)
    ap.add_argument("--quadrant", default=None)
    ap.add_argument("--kind", default="long", choices=["long", "short"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--budget-s", type=int, default=420, help="单篇总预算（写+重写）")
    ap.add_argument("--expand", action="store_true",
                    help="配合 --polish：篇幅不足的深稿先定向扩写再打磨")
    ap.add_argument("--polish", default=None,
                    help="打磨已有库存：给一个 drafts 下的日期目录或单篇目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.polish:
        base = a.polish
        jobs = []
        if os.path.basename(os.path.normpath(base)) == "draft.md":
            jobs = [os.path.dirname(base)]
        else:
            for root, _d, files in os.walk(base):
                if "draft.md" in files:
                    jobs.append(root)
        ok = fix = 0
        for j in sorted(jobs):
            if a.expand:
                f = os.path.join(j, "draft.md")
                n = len(re.sub(r"\s", "", open(f, encoding="utf-8").read()))
                if n < 1500:
                    expand_one(j, target=1800, log=print)
            rs, rr, ra = polish_dir(j)
            ok += 1 if (rs == 0 and rr == 0 and ra == 0) else 0
            fix += 0 if (rs == 0 and rr == 0 and ra == 0) else 1
            print("  %-46s 结构 %s 严谨 %s 权威 %s"
                  % (os.path.relpath(j, os.path.dirname(os.path.dirname(j)))[:46],
                     "过" if rs == 0 else "未过", "过" if rr == 0 else "未过",
                     "过" if ra == 0 else "未过"))
        print("打磨 %d 篇：三闸全过 %d 篇，待修 %d 篇" % (len(jobs), ok, fix))
        return 0

    import gzh_week
    day = date.fromisoformat(a.date) if a.date else date.today()
    week = gzh_week.for_date(day)
    if not week:
        print("%s 不在任何一周里——先排周主题，不许无主题写稿。" % day)
        return 1

    topic, quadrant = a.topic, a.quadrant
    if not topic:
        first = (week.get("篇") or [{}])[0]
        topic, quadrant = first.get("topic"), quadrant or first.get("quadrant")
    if not topic:
        print("本周没有篇目，也没有给 --topic——不知道写什么就不写。")
        return 1

    print("本周 %s「%s」｜类型 %s｜题：%s" % (week["week"], week["主题"], quadrant, topic))
    rc, info = write_one(week, topic, quadrant, a.kind, a.attempts, a.budget_s)
    if rc == 3:
        print("算力没拿到：%s（这不算失败，下一拍再试）" % info.get("why"))
    elif rc in (0, 2):
        print("稿子：%s" % info.get("draft"))
        print("状态：NEEDS-HUMAN —— 模型初稿，必须人看完才能改 READY")
    else:
        print("未出稿：%s" % (info or {}).get("why"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
