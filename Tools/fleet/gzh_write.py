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

def build_prompt(week, season, topic, quadrant, kind):
    import llm_client as L
    spec = {
        "硬核": "2000-3500 字。给可复现的测量/计算方法，给改法，同行能拿去用。",
        "实操": "800-1500 字。步骤可照着做，每步说清在哪、点什么、做完会有什么区别。",
        "大众": "600-1200 字。给明确取舍，结尾写清什么人适用、什么人不适用。",
        "科技": "1500-2800 字。一个技术点讲透，落到用户能感知的差别。",
    }.get(quadrant, "1200-1800 字。")
    return (
        "你在给一个汽车 HMI 视觉设计师写公众号长文初稿。作者身份：专职做汽车座舱视觉设计，"
        "只看一块屏——层级、留白、配色、动效、字体、图标、质感。不聊动力、底盘、空间、油耗。\n\n"
        "【本周主题】%s（%s，%s → %s）\n"
        "【本周为什么写这个】%s\n"
        "【本周关键词】%s\n"
        "【这一篇的题目】%s\n"
        "【类型】%s，篇幅 %s\n\n"
        "%s\n\n"
        "【硬要求】\n"
        "1. 第一句不超过 30 字，落到一个具体场景或具体物，不铺垫、不写「随着…」。\n"
        "2. 3-4 个小标题，必须是断言式短句，禁止用疑问句。\n"
        "3. 每段 60-100 字，最长不超过 120 字。\n"
        "4. 每 300 字至少一个可核验细节（比例、尺寸、色值、条款、参数），数字必须带口径，"
        "写清是谁测的、什么条件。\n"
        "5. 至少一处「我自己的」经历或代价，但不许编造实测（不写我开了几万公里、我拆了车）。\n"
        "6. 必须写出最强反对意见，并说明你为什么不让步。\n"
        "7. 结尾给明确建议，写清什么人不该听你的。\n"
        "8. 全文至少一处自我代价（我原来错了/我为此多花了钱/这句话会得罪人）。\n"
        "9. 不要写「总而言之」「首先其次」「赋能」「助力」这类词，不要写口号结尾。\n"
        "10. 只输出文章本身：第一行是 Markdown 一级标题，不要任何解释、不要前后缀。\n"
        % (week["主题"], week["week"], week["from"], week["to"],
           week.get("为什么这周写这个") or "", "、".join(week.get("关键词") or []),
           topic, quadrant, spec, L.gzh_block())
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

def write_one(week, topic, quadrant, kind="long", attempts=2, budget_s=420, log=print):
    import gpu_lease
    import llm_client as L

    seat_model = L._model_for(SEAT)
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
            r = L.generate(prompt, cls=SEAT, keep_alive="20m", num_predict=4200,
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
            d = date.today().isoformat()
            outdir = os.path.join(DRAFTS, d)
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
            man = {"date": d, "week": week["week"], "week_theme": week["主题"],
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
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

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
