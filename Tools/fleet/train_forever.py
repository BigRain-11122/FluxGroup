#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_forever.py — 7×24 连续训练循环（按段轮转，有料就训，没料就报没料）。

CEO 2026-11-19「你确保能7x24不断的训练，颗粒度做细做全，要有人味」。
三句话对应三条硬设计：

1 **不断**：每轮只训一个段，训完立刻回到队列；队列空了不是"没活"，
   而是要明确判"无料可训"并去补料——绝不用空转冒充产能。
2 **颗粒度按段×切片**：一段一卡（seg + min_human 切片 + 迭代数），
   每卡独立留档（行数/val 最低点/段内基座对比/人味分/判词）。
3 **人味**：留档判据不是总分，而是"段内均分 +5 且 PASS 不降 且 人味(human) 不降 2"。
   总分可以被语感与格式刷上去，人味掉了就是 AI 腔回来了——这种一律不采用。

跟其它组件的关系：
- 训练本身仍走 `train_run.sh`（独占锁、让路、切档、恢复都在它里面）；
- 被否的段写进 `.codely-cli/state/seg-rejects.json`，只有语料涨 ≥15% 才重训；
- 权重归档到 `~/.fluxgroup/lora-archive/`，不进 git（仓库只留卡与账）。

用法：
  python3 Tools/fleet/train_forever.py --once      # 跑一轮（launchd 每 5 分钟一次）
  python3 Tools/fleet/train_forever.py --dry       # 只判队列，不训
  python3 Tools/fleet/train_forever.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import threading
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TRAIN = os.path.join(SOCIAL, "train")
RUNS = os.path.join(TRAIN, "RUNS")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOOP_STATE = os.path.join(TRAIN, "LOOP-STATE.json")
LEDGER = os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl")
BOARD = os.path.join(SOCIAL, "TRAIN-LOOP.md")
REJECTS = os.path.join(STATE, "seg-rejects.json")
QUALITY = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
ARCHIVE = os.path.join(os.path.expanduser("~"), ".fluxgroup", "lora-archive")
PY = "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"

try:
    import train_build as _tb
    RECIPE_V = getattr(_tb, "RECIPE", "v1")
except Exception:
    RECIPE_V = "v1"

GENERIC = "__all__"     # 全量语料卡：段都进冷却时用它顶上，吃的是"所有段的合集 + 新采数据"
GENERIC_COOLDOWN_S = 8 * 3600
GENERIC_MIN_ROWS = 1000
GENERIC_EVAL_SEGS = ("tech_nerd", "music_seeker")   # 全量件在两组代表段上验，任一段退步就不采用

MIN_ROWS = 200          # 段内可用语料下限：低于这个数只学会抄碎片
MIN_BUILD = 180         # 造集后训练样本下限
COOLDOWN_S = 6 * 3600   # 同段冷却：一天最多训 4 次，避免对着同一批语料反复过拟合
GROWTH_GATE = 1.15      # 被否过的段，语料要涨 15% 才重训
# 单次训练的墙钟上限：正常 40-50 分钟；给到 2 小时是留足慢盘/降速余量。
# 超过就整组杀掉——租约 TTL 是 4 小时，没有这道闸，一次死锁会白占一整晚。
TRAIN_MAX_S = 2 * 3600
# 天花板闸：基座分已经这么高的段，训 LoRA 只会把它拉低，不该再烧 GPU。
# 2026-11-27 实锚：craft_learner 基座 81.4（n=30 测量），训完掉到 68-75，连续三轮都是负分；
# 它本来就是"带技术细节"的段，基座已经写得很好，缺的不是风格而是内容。
CEILING_SKIP = 80.0
# 反复被否的段：累计被否这么多次之后，只有"语料翻倍"才值得再试一次。
# 2026-11-27 实锚：craft_learner 17 次、feeler 16 次、shallow 15 次被否，
# 而 15% 增长门槛让它们每隔几小时就回来烧一轮——这不是探索，是重复同一个失败。
HARD_REJECT_N = 10
HARD_GROWTH = 2.0
KEEP_GAIN = 5.0         # 段内均分要比基座高这么多
KEEP_HUMAN_DROP = 2.0   # 人味允许波动；掉超过 2 分即判退步


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def segment_rows():
    """每段可用行数：优先读烘焙产物（BAKED-v1.jsonl，带 seg/verdict），
    读不到才退回 QUALITY-PASS 现场分类，再退回 personas 快照。

    2026-11-20 实锚：QUALITY-PASS.jsonl 自 16:11 起全仓无人再写，而真实产物是
    own_collected → corpus_bake → BAKED-v1.jsonl。读旧文件会把 shallow 从 2294 行
    报成 720 行，于是"语料未涨 10%"永远成立 → 该段永远排不上 → GPU 空转两小时。
    """
    sys.path.insert(0, HERE)
    try:
        import segments as sgm
        spec = sgm.load_spec()
    except Exception:
        spec = None
    rows = {}
    baked = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
    if os.path.isfile(baked):
        for line in open(baked, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("verdict") or "PASS") != "PASS":
                continue
            seg = r.get("seg") or "generic"
            if seg != "generic":
                rows[seg] = rows.get(seg, 0) + 1
        return rows
    if spec and os.path.isfile(QUALITY):
        for line in open(QUALITY, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line).get("text") or ""
            except Exception:
                continue
            c = sgm.classify(t, spec) if t else None
            seg = (c or {}).get("primary")
            if seg and seg != "generic":
                rows[seg] = rows.get(seg, 0) + 1
    if not rows:
        personas = _load(os.path.join(SOCIAL, "SEGMENT-PERSONAS-v1.json"), {}) or {}
        for k, v in (personas.get("segments") or {}).items():
            if k != "generic":
                rows[k] = int(v.get("n") or 0)
    return rows


def eligible(seg, rows, st, rejects, now=None):
    """这一段现在该不该训？返回 (bool, 原因)。

    纯函数，自检直接打这三条判据：语料下限 / 冷却 / 被否后的增长闸。
    """
    now = now or time.time()
    rec = (st.get("segments") or {}).get(seg) or {}
    n = int(rows.get(seg, 0))
    if n < MIN_ROWS:
        return False, "语料 %d < %d" % (n, MIN_ROWS)
    last = rec.get("last_ts") or 0
    last_rows = int(rec.get("rows") or 0)
    # 训练节奏跟着**数据**走，不跟时钟走：语料涨够 10% 就是新的一课，
    # 比"每 6 小时再来一遍同样的数据"科学（那只会过拟合）。
    grown = last_rows and n >= last_rows * 1.10
    # 冷却必须先于"配方更新"判定：否则状态里一旦缺 recipe（重建/历史台账没有这个字段），
    # 每轮都判"配方更新"直接放行，6 小时冷却形同不存在。
    # 2026-11-26 实锚：shallow 00:15 与 03:49 两次训出同一指纹，17 次 run 只 7 个模型。
    if last and now - last < COOLDOWN_S and not grown:
        return False, "冷却中（%.1fh 前刚训过，语料 %d→%d 未涨 10%%）" % (
            (now - last) / 3600.0, last_rows, n)
    # 配方变了（话语配比/开头配额）也是重训理由：同一批语料换个喂法就是新的一课
    rj0 = rejects.get(seg) or {}
    # 状态里没有 recipe 字段 = 无法证明这件是用当前配方训的（状态丢失/重建都会这样）。
    # 这种情况按"配方更新"处理：宁可多训一轮，也不要拿状态缺失当"已经训过了"永久空转。
    if (not rec.get("recipe")) or (rec["recipe"] != RECIPE_V and not (
            int(rj0.get("n") or 0) >= 3 and n < int(rj0.get("rows") or 0) * GROWTH_GATE)):
        return True, "配方更新 %s（%d 行）" % (RECIPE_V, n)
    rj = rejects.get(seg) or {}
    # 被否太多次的段：门槛从 15% 提到"翻倍"。只有在数据形态真的大变时才值得再试。
    if rj and int(rj.get("n") or 0) >= HARD_REJECT_N:
        if n < int(rj.get("rows") or 0) * HARD_GROWTH:
            return False, "已被否 %d 次，语料 %d 未到 %.1f 倍（%d），不再重复同一个失败" % (
                int(rj.get("n") or 0), n, HARD_GROWTH, int(int(rj.get("rows") or 0) * HARD_GROWTH))
    if rj and n < int(rj.get("rows") or 0) * GROWTH_GATE:
        return False, "上次被否（%d 行）且语料只到 %d，未涨 %.0f%%" % (
            int(rj.get("rows") or 0), n, (GROWTH_GATE - 1) * 100)
    return True, "可训（%d 行）" % n


def _ledger_rows():
    """读台账原始行（给实验矩阵判"这个变体跑过没"）。读不到就返回空表：
    空表只会让矩阵多开一次实验，不会让闸误判"已跑过"。"""
    rows = []
    try:
        for ln in open(LEDGER, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        return []
    return rows


def dataset_fp(ds):
    """训练集指纹：train.jsonl 的 sha256 前 16 位。文件不存在返回 ""。

    为什么用文件而不是行数：行数相同内容可能不同（换了一批等长的句子），
    行数不同内容也可能等价（顺序变了）。真正决定权重的就是这份文件本身。
    """
    p = os.path.join(ds, "train.jsonl")
    try:
        import hashlib
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return ""


def weight_sha(ckpt_dir):
    """适配器权重的 sha256 前 12 位。拿不到返回 ""。"""
    try:
        import hashlib
        p = os.path.join(ckpt_dir, "adapters.safetensors")
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:12]
    except Exception:
        return ""


def seen_weight_sha(exclude_dir=None):
    """已归档过的全部权重指纹集合（用来发现"这次训出来的是同一份权重"）。"""
    out = {}
    try:
        for name in os.listdir(ARCHIVE):
            d = os.path.join(ARCHIVE, name)
            if not os.path.isdir(d):
                continue
            h = weight_sha(d)
            if h:
                out.setdefault(h, []).append(name)
    except Exception:
        pass
    return out


def built_map(path=None):
    """每段最近一次"烘焙后可用行数"（台账里的 built）。

    为什么不用 rows 排序（2026-11-23 实证 R2）：烘焙平均只剩 68%（最低 16.7%），
    rows 会高估可用语料，导致"看着最多的段"其实没料。
    """
    m = {}
    try:
        with open(path or LEDGER, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                seg, b = r.get("seg"), r.get("built")
                if seg and b:
                    m[seg] = int(b)
    except Exception:
        pass
    return m



def pick(rows, st, rejects, now=None, built=None):
    """队列排序：最久没训的优先，同档按**烘焙后可用语料**多的优先。"""
    built = built if built is not None else built_map()
    now = now or time.time()
    cands = []
    for seg in sorted(rows):
        ok, why = eligible(seg, rows, st, rejects, now)
        if ok:
            last = ((st.get("segments") or {}).get(seg) or {}).get("last_ts") or 0
            eff = built.get(seg) or rows[seg]      # 没烘过的段没有 built，回退原始行数
            cands.append((last, -eff, seg, why))
    if not cands:
        g = (st.get("segments") or {}).get(GENERIC) or {}
        total = sum(int(v) for k, v in rows.items() if k != "generic")
        if total >= GENERIC_MIN_ROWS and now - (g.get("last_ts") or 0) > GENERIC_COOLDOWN_S:
            return ({"seg": GENERIC, "rows": total,
                     "why": "全量 %d 行（各段都在冷却）" % total}, [])
        return None, []
    cands.sort()
    last, negn, seg, why = cands[0]
    return {"seg": seg, "rows": -negn, "why": why}, cands


# 少于这个条数，判词是在评噪声不是评权重。
# 2026-11-27 由 8 提到 30：memer 同一提示 n=10 判 KEEP(+9.7)、n=30 判 REJECT(-4.4)，
# 说明 8-10 条的判决不可信；30 条把标准误压到 ~5 分以内，配合 noise_se 才能下结论。
MIN_EVAL_N = 30


def ceiling_of(seg, min_n=None):
    """该段基座的天花板（历史里 n≥MIN_EVAL_N 的最大 base_avg）。没有可信测量返回 None。

    只用 n≥30 的记录：n=10 的基座分本身就在 ±5 抖，拿它设天花板会把好段误停。
    """
    min_n = MIN_EVAL_N if min_n is None else int(min_n)
    best = None
    for r in _ledger_rows():
        if r.get("seg") != seg:
            continue
        if int(r.get("eval_n") or 0) < min_n:
            continue
        try:
            b = float(r.get("base_avg"))
        except Exception:
            continue
        best = b if best is None else max(best, b)
    return best


def noise_se(base, lora):
    """两组均分之差的标准误（近似，不假设配对）：sqrt(sd_b²/n_b + sd_l²/n_l)。

    2026-11-27 实锚：同一提示 memer n=10 得 +9.7（KEEP），加到 n=30 变成 -4.4（REJECT）；
    tech_nerd +4.6 差 0.4 分不及格。说明 5 分门槛落在噪声里，判词全凭运气。
    有了 se，"这条改进比噪声大不大"才是可算的。任一侧缺 sd 时返回 None（不启用该闸）。
    """
    try:
        nb, nl = int(base.get("n") or 0), int(lora.get("n") or 0)
        sb, sl = float(base.get("sd")), float(lora.get("sd"))
    except Exception:
        return None
    if nb <= 1 or nl <= 1:
        return None
    return (sb * sb / nb + sl * sl / nl) ** 0.5


def judge_keep(base, lora):
    """留档判据：均分 +5、PASS 不降、人味不降 2，且改进必须大于噪声。样本不足时一律不判。"""
    if not base or not lora:
        return False, "缺评测数据"
    n = min(int(base.get("n") or 0), int(lora.get("n") or 0))
    if n < MIN_EVAL_N:
        return False, "样本不足（n=%d < %d），不判" % (n, MIN_EVAL_N)
    gain = float(lora.get("avg") or 0) - float(base.get("avg") or 0)
    if gain < KEEP_GAIN:
        return False, "均分只 %+.1f（需 ≥%.1f）" % (gain, KEEP_GAIN)
    se = noise_se(base, lora)
    if se is not None and gain <= se:
        return False, "均分 %+.1f 未超过噪声（±%.1f，n=%d）" % (gain, se, n)
    if float(lora.get("pass_rate") or 0) < float(base.get("pass_rate") or 0):
        return False, "PASS %d%% < 基座 %d%%" % (lora.get("pass_rate") or 0,
                                                 base.get("pass_rate") or 0)
    dh = float(lora.get("avg_human") or 0) - float(base.get("avg_human") or 0)
    if dh < -KEEP_HUMAN_DROP:
        return False, "人味退步 %.1f（总分靠语感刷上去不算变好）" % dh
    # se=None 表示没量到（缺 sd），要如实写"噪声未知"，不许显示成 ±0.0 让人以为量过。
    _noise = "噪声未知" if se is None else "噪声 ±%.1f" % se
    return True, "均分 %+.1f（%s）/ 人味 %+.1f" % (gain, _noise, dh)


def sh(cmd, timeout=7200):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def val_min_step(run_dir):
    """最低 val 对应的步数。步距读 RUN.json 里的 --steps-per-eval（默认 50），
    不能像老代码那样写死 100——本循环用的就是 50，写死会把 400 步报成 800。"""
    info = _load(os.path.join(run_dir, "RUN.json"), {}) or {}
    vals = info.get("val_loss_all") or []
    if not vals:
        return None, None
    argv = info.get("argv") or []
    step = 50
    if "--steps-per-eval" in argv:
        try:
            step = int(argv[argv.index("--steps-per-eval") + 1])
        except Exception:
            pass
    i = min(range(len(vals)), key=lambda k: vals[k])
    return (i + 1) * step, vals[i]


def saved_steps(run_dir):
    out = []
    d = os.path.join(run_dir, "adapter")
    try:
        for fn in os.listdir(d):
            m = re.match(r"^0*(\d+)_adapters\.safetensors$", fn)
            if m:
                out.append(int(m.group(1)))
    except Exception:
        pass
    return sorted(out)


def ckpt_dir(run_dir, step):
    """把"val 最低那一步"吸附到真实存在的权重点，并返回 (目录, 实际步数)。

    mlx 每 100 步才落一次权重，而 val 每 50 步一测：最低点可能落在 250 步，
    但没有 0000250 这个文件。此时必须取最近的已存点（优先更早的那一步），
    并且把"实际用的是哪一步"写进台账——拿 300 步的权重谎称 250 步就是不诚实。
    """
    steps = saved_steps(run_dir)
    if not steps:
        return None, None
    lower = [x for x in steps if x <= int(step)]
    real = lower[-1] if lower else steps[0]
    dst = os.path.join(run_dir, "ckpt%d" % real)
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(run_dir, "adapter", "%07d_adapters.safetensors" % real)
    if not os.path.exists(src):
        return None, None
    import shutil as _sh
    _sh.copy(src, os.path.join(dst, "adapters.safetensors"))
    cfg = os.path.join(run_dir, "adapter", "adapter_config.json")
    if os.path.exists(cfg):
        _sh.copy(cfg, os.path.join(dst, "adapter_config.json"))
    return dst, real


def board(st, rows, rejects):
    lines = ["# 7×24 训练循环（%s）" % now_iso(), ""]
    # 定时器自己也要露出来：看不见调度器，"7×24"就只是一句话。
    try:
        out = subprocess.run(["launchctl", "print", "gui/%d/com.fluxgroup.trainloop" % os.getuid()],
                             capture_output=True, text=True, timeout=10).stdout
        state = re.search(r"state = (\w+)", out)
        lines.append("> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 %s" % (
            state.group(1) if state else "未知"))
    except Exception:
        lines.append("> 调度：未检测到 launchd 任务（手工运行时正常）")
    lines.append("")
    q = []
    for seg in sorted(rows):
        ok, why = eligible(seg, rows, st, rejects)
        q.append((seg, rows[seg], ok, why))
    q.sort(key=lambda x: (not x[2], -x[1]))
    lines += ["## 队列", "", "| 段 | 可用行数 | 可训 | 判据 |", "|---|---|---|---|"]
    for seg, n, ok, why in q:
        lines.append("| %s | %d | %s | %s |" % (seg, n, "是" if ok else "否", why))
    # 没料时不能说"没活"：把缺口列成补料清单，训练线的瓶颈才看得见。
    short = [(seg, n) for seg, n in rows.items() if n < MIN_ROWS]
    short.sort(key=lambda x: -x[1])
    if short:
        need = sum(MIN_ROWS - n for _, n in short)
        lines += ["", "## 补料清单（训练线的真实瓶颈）", "",
                  "有 %d 个段低于 %d 行，合计还差 **%d 行**才够开训：" % (
                      len(short), MIN_ROWS, need), "",
                  "| 段 | 现有 | 差 |", "|---|---|---|"]
        for seg, n in short[:8]:
            lines.append("| %s | %d | %d |" % (seg, n, MIN_ROWS - n))

    runs = st.get("runs") or []
    lines += ["", "## 最近 10 轮", "",
              "| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs[-10:]:
        n = r.get("eval_n")
        # 3 条判出来的结论是噪声（实测同一权重差 30 分）：必须在板上标出来，
        # 否则读板的人会把"KEEP"当真。
        tag = r.get("verdict") or ""
        if n is None:
            tag += "（旧口径 n=3，不可当真）"
        elif int(n) < 8:
            tag += "（样本不足）"
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            (r.get("ts") or "")[5:16], r.get("seg"), n if n is not None else "-",
            r.get("rows"), r.get("val_min"), r.get("step"), r.get("base_avg"),
            r.get("lora_avg"), r.get("human_delta"), tag))
    lines += ["", "> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；"
                  "同段冷却 6h；被否段语料需涨 15% 才重训。"]
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    open(BOARD, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def busy_holder():
    """训练锁的持有者 pid（活着才算）。launchd 每 5 分钟起一次本脚本，
    这层前置判断让"已经有训练在跑"的实例立刻退出，不去重复造集/抢内存。"""
    lock = os.path.join(STATE, "TRAIN-RUNLOCK", "pid")
    try:
        pid = int(open(lock, encoding="utf-8").read().strip())
    except Exception:
        return None
    try:
        os.kill(pid, 0)
        return pid
    except Exception:
        return None


def reconcile(st):
    """状态文件以**台账**为准重建：台账是追加写的事实，状态只是缓存。

    2026-11-19 实锚：两个实例（launchd + 手动）各自读旧状态、各自写回，
    tech_nerd 的 KEEP 被一次陈旧写覆盖成 REJECT，还顺带把它挡进"需补语料"。
    根因不是谁写错，而是"多处读改写同一个文件"。所以每次进循环先按台账重建。
    """
    rows = []
    try:
        for line in open(LEDGER, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except Exception:
        return st
    segs = {}
    for r in rows:
        seg = r.get("seg")
        if not seg:
            continue
        # 让路（BLOCKED）不是训练事件：没占 GPU、没动数据、没产出模型。
        # 2026-11-26 实锚：把它当训练记录会刷新 last_ts，冷却时钟被自己的重试推着走，
        # 于是同一段每 1-2 分钟重新排队（21:06→21:25 共 7 次）。
        if r.get("no_progress") or r.get("verdict") == "BLOCKED":
            d = segs.setdefault(seg, {})
            d["last_blocked_ts"] = r.get("ts") and time.mktime(
                time.strptime(r["ts"][:19], "%Y-%m-%dT%H:%M:%S")) or time.time()
            continue
        # 复验（re_verify）是**评测**，不是训练：它没造集、没训权重，只是拿旧 adapter
        # 重新打了一次分。2026-11-26 实锚：social_loop 写进来的复验行只有
        # run/verdict/adapter，没有 recipe 与 built——一旦让它覆盖段状态，
        # 该段的配方与烘焙记录就被抹成 None，冷却闸静默失效；
        # 而且它还会推进 last_ts，等于一次复验白给该段加 6 小时冷却。
        # 所以只记 last_verify_ts / last_verify_rc，不碰训练时钟。
        if r.get("re_verify"):
            d = segs.setdefault(seg, {})
            d["last_verify_ts"] = r.get("ts") and time.mktime(
                time.strptime(r["ts"][:19], "%Y-%m-%dT%H:%M:%S")) or time.time()
            d["last_verify_rc"] = r.get("verdict")
            d["last_verify_adapter"] = r.get("adapter")
            continue
        prev = segs.get(seg) or {}
        segs[seg] = {"last_ts": r.get("ts") and time.mktime(
                         time.strptime(r["ts"][:19], "%Y-%m-%dT%H:%M:%S")) or time.time(),
                     "last_rc": r.get("verdict"), "rows": r.get("rows"),
                     # built/recipe 缺了就沿用上一次已知值：台账里任何一条"没有这两个
                     # 字段"的记录（外部工具写的）都不许把它们抹成空，否则依赖它们的闸
                     # （同款重训闸、冷却闸）会静默放行。
                     "built": r.get("built") if r.get("built") is not None else prev.get("built"),
                     "run": r.get("run"), "step": r.get("step"),
                     "val_min": r.get("val_min"),
                     # recipe 必须一起重建：少了它，eligible() 会判"配方更新"
                     # 而永远放行，冷却与被否后的 15% 增长闸全部失效。
                     # 2026-11-26 实锚：8 个段里 7 个 recipe=None，同一段 3.5 小时
                     # 就重训一次、17 次 run 只出 7 个不同模型（feeler 0/14 还在烧）。
                     "recipe": r.get("recipe") if r.get("recipe") is not None else prev.get("recipe")}
        if prev.get("last_verify_ts"):
            segs[seg]["last_verify_ts"] = prev["last_verify_ts"]
            segs[seg]["last_verify_rc"] = prev.get("last_verify_rc")
    st["segments"] = segs
    st["runs"] = rows[-40:]
    return st


def _lane(phase, **meta):
    """写本线状态件（lane-train.json）。失败一律吞掉——状态件坏了不许拖垮训练。

    为什么要这层包装：lane_state 是"每线一个件、互不干扰"的落点（CEO 2026-11-26
    「经常更新，但不要互相影响」）。它只是旁证，不能成为训练的前置条件。
    """
    try:
        import lane_state as ls
        ls.put("train", phase, **meta)
    except Exception:
        pass


def prune_runs(keep_hours=6, dry=False):
    """清掉非在用训练 run，防止磁盘被 186MB/run 堆满。

    为什么要有（2026-11-27 实锚）：trainloop 每 300s 就可能开一个 run，两天堆出 54 个、
    15.1GB，磁盘从 191G 掉到 171G 只用两天——之前没有任何清理逻辑。

    2026-11-27 二次实锚：窗口原设 48h，而实际一天就产 72 个 run（12G），48h 等于
    稳态 26G 且**一个都不会被清**（全部落在窗口内）。收紧到 6h。
    但压缩窗口会碰到一个更硬的约束：路由是按**增益最大**挑件、不是挑"最后一次 KEEP"
    （peer_pro 实锚：87.3 与 73.6 两件都判 KEEP，删掉高的那件＝线上静默降级），
    所以"当前在线件"必须单独保护，不能只靠台账。

    保守判据（缺一条就保留）：
      1) 路由器的当前在线件（best_adapters → 增益最大且 n≥30）→ 留
      2) 台账里每段最后一次 KEEP → 留
      3) LOOP-STATE 里每段最后一次 → 留
      4) 修改时间在 keep_hours 内 → 留
    返回 (删除数, 释放MB)。
    """
    import glob
    runs_dir = os.path.join(TRAIN, "RUNS")
    if not os.path.isdir(runs_dir):
        return 0, 0
    keep = set()
    # 每段最后一次 KEEP（不是所有 KEEP：同段多轮采用时旧件只是历史，留着纯占 186MB）
    last_keep = {}
    try:
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("verdict") == "KEEP" and r.get("run"):
                    seg = r.get("seg") or ""
                    ts = r.get("ts") or ""
                    if seg not in last_keep or ts > last_keep[seg][0]:
                        last_keep[seg] = (ts, r["run"])
    except FileNotFoundError:
        pass
    keep.update(run for _ts, run in last_keep.values())
    # 在线件：路由算不出来就退回"所有 KEEP 都留"，宁可少清不可降级
    try:
        import adapter_router as _ar
        for _seg, _v in (_ar.best_adapters() or {}).items():
            for part in str(_v.get("adapter") or "").split("/"):
                if len(part) > 9 and part[:8].isdigit() and "-" in part:
                    keep.add(part)
                    break
    except Exception:
        try:
            with open(LEDGER, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip() or "{}")
                    except Exception:
                        continue
                    if r.get("verdict") == "KEEP" and r.get("run"):
                        keep.add(r["run"])
        except Exception:
            pass
    try:
        st = _load(LOOP_STATE, {}) or {}
        for _seg, rec in (st.get("segments") or {}).items():
            if rec.get("run"):
                keep.add(rec["run"])
    except Exception:
        pass
    now, n, freed = time.time(), 0, 0
    for d in sorted(glob.glob(os.path.join(runs_dir, "*"))):
        name = os.path.basename(d)
        if not os.path.isdir(d) or name in keep:
            continue
        # 龄期必须取目录名里的产出时刻，不能取 mtime：git checkout/rebase/restore
        # 会把 RUNS 下被跟踪文件的 mtime 全刷成"刚刚"（2026-11-27 实锚：22 个
        # 20-32 小时前的 run 全被 mtime 判成"6 小时内"，清理永远不生效）。
        age_h = None
        try:
            age_h = (datetime.now()
                     - datetime.strptime(name, "%Y%m%d-%H%M%S")).total_seconds() / 3600.0
        except Exception:
            age_h = (now - os.path.getmtime(d)) / 3600.0
        if age_h <= keep_hours:
            continue
        try:
            mb = int(sum(os.path.getsize(os.path.join(r, f))
                         for r, _ds, fs in os.walk(d) for f in fs) / 1048576)
        except Exception:
            mb = 0
        if dry:
            n += 1
            freed += mb
            continue
        try:
            shutil.rmtree(d)
            n += 1
            freed += mb
        except Exception:
            continue
    if n and not dry:
        print("[prune] 清掉 %d 个非在用 run，释放 %dMB（保留 KEEP/每段最新/%dh 内）"
              % (n, freed, keep_hours))
    return n, freed


def record_fail(seg, rows, kind, why, built=0):
    """失败也要进台账：状态是从台账重建的，不写台账等于"这次失败不存在"，
    于是同一段会被无限重试（2026-11-20 实锚：memer 连续两次被选中）。

    2026-11-26 实锚：本函数原来不写 recipe，而 reconcile 是从台账重建状态的——
    每一条 BLOCKED/TRAIN-FAIL 都把该段的 recipe 抹成 None，下一轮 eligible() 就判
    "配方更新"直接放行。结果 21:06→21:25 同一段被重排 7 次，每 1-2 分钟一次。
    所以 recipe 必须一起落盘；BLOCKED（让路）还要标 no_progress —— 它没占 GPU、
    没动数据，不该刷新冷却时钟。
    """
    rec = {"ts": now_iso(), "seg": seg, "rows": rows, "built": built,
           "eval_n": 0, "verdict": kind, "why": why, "adapter": None,
           "recipe": RECIPE_V}
    if kind == "BLOCKED":
        rec["no_progress"] = True
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def social_session_active():
    """现在是否在"刷 B 站"的会话里。会话里出稿要用 GPU，
    训练这时候开跑会把生成从 26 tok/s 压到 2 tok/s（2026-11-20 实测 12 倍），
    两边都做不好——所以短的让长的没有意义，应该按时间片轮流独占。
    """
    # 2026-11-20：两个号改由 agent_daemon 驱动，不再走 social_session 的时间窗。
    # 所以除了旧判据，还要看 agent 会话哨兵（state/AGENT-SESSION-<alias>）。
    try:
        sd = os.path.join(ROOT, ".codely-cli", "state")
        for f in os.listdir(sd):
            if f.startswith("AGENT-SESSION-"):
                pth = os.path.join(sd, f)
                age = time.time() - os.path.getmtime(pth)
                if age < 3 * 3600:      # 3 小时内的哨兵算活跃；防止崩溃留下的僵尸哨兵永久拦训
                    return True
    except Exception:
        pass
    try:
        import social_session as ss
        return bool(ss.current())
    except Exception:
        return False


_TICK_LOCK = {}


def _claim_tick():
    """本轮 tick 的单实例锁：抢不到就说明另一拍正在跑，直接退出。

    2026-11-27 实锚：轮询从 300s 压到 60s 之后，造集阶段（还没拿 GPU 租约）出现窗口，
    两次调用会各自造一遍集、各打印一次「选中段 memer / 变体 v0-base」——GPU 有租约把关
    不会真的并行训练，但白造一次集、日志也会让人以为起了两个训练。
    """
    import fcntl
    path = os.path.join(STATE, "train-tick.lock")
    try:
        os.makedirs(STATE, exist_ok=True)
        fh = open(path, "a+")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _TICK_LOCK["fh"] = fh
        return True
    except Exception:
        return False


def run_one(a):
    if not _claim_tick():
        print("[loop] 另一拍正在跑（tick 锁），本次跳过")
        return 0
    holder = busy_holder()
    if holder:
        print("[loop] 训练进行中（pid %d），本次跳过" % holder)
        _lane("inflight", holder=holder)
        return 0
    if social_session_active() and os.environ.get("FLUX_TRAIN_FORCE") != "1":
        print("[loop] 会话时段（养号出稿用 GPU），训练让路 5 分钟后再看")
        return 0
    rows = segment_rows()
    st = reconcile(_load(LOOP_STATE, {"segments": {}, "runs": []}))
    rejects = _load(REJECTS, {})
    st.setdefault("segments", {})
    st.setdefault("runs", [])
    if a.seg:
        n_rows = (sum(int(v) for k, v in rows.items() if k != "generic")
                  if a.seg == GENERIC else int(rows.get(a.seg, 0)))
        task, _cands = ({"seg": a.seg, "rows": n_rows, "why": "手动指定"}, [])
    else:
        task, _cands = pick(rows, st, rejects)
    if not task:
        # 轮询已压到 60 秒：队列空时不要每分钟刷一遍日志与看板。
        # 用自己写的状态件当"刚判过空"的证据，10 分钟内只记一次。
        try:
            import lane_state as _ls
            _d = _ls.get("train") or {}
            if (_d.get("phase") == "idle-no-task"
                    and time.time() - float(_d.get("ts") or 0) < 600):
                return 0
        except Exception:
            pass
        board(st, rows, rejects)
        why_not = []
        for seg in sorted(rows, key=lambda x: -rows[x])[:4]:
            _ok, w = eligible(seg, rows, st, rejects)
            why_not.append("%s(%s)" % (seg, w))
        print("[loop] 无料可训：%s" % "；".join(why_not))
        # 留痕：夜班早上要看得出"是没活可干"还是"循环停了"。
        # 只看进程活着的判据救不了这个——队列空也是一种状态，必须写进状态件。
        _lane("idle-no-task", why="；".join(why_not)[:120])
        return 0
    seg = task["seg"]
    # 天花板闸（手动 --seg 不拦，那是显式指令）：基座已经 ≥80 分的段，训 LoRA 只会拉低。
    # 2026-11-27 实锚：craft_learner 基座 81.4 → 连训三轮 68.5/75.0/68.4，全是负分。
    if not a.seg:
        _ceil = ceiling_of(seg)
        if _ceil is not None and _ceil >= CEILING_SKIP:
            print("[loop] 跳过 %s：基座已 %.1f 分（≥%.0f 天花板），训了只会拉低" % (
                seg, _ceil, CEILING_SKIP))
            record_fail(seg, task["rows"], "CEILING",
                        "基座 %.1f 已达天花板 %.0f" % (_ceil, CEILING_SKIP))
            st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                       last_rc="CEILING")
            _save(LOOP_STATE, st)
            _lane("skip-ceiling", seg=seg, ceiling=round(_ceil, 1))
            board(st, rows, rejects)
            return 0
    ok_power, why_power = power_ok()
    if not ok_power:
        print("[loop] 暂停开训：%s" % why_power)
        st["segments"].setdefault(seg, {})["last_rc"] = "POWER"
        _save(LOOP_STATE, st)
        return 0
    ok_mem, seq_len, why_mem = mem_verdict(5.0)
    if not ok_mem:
        print("[loop] 暂停开训：%s" % why_mem)
        st["segments"].setdefault(seg, {})["last_rc"] = "MEM"
        _save(LOOP_STATE, st)
        return 0
    if why_mem:
        print("[loop] 内存闸降档：%s" % why_mem)
    print("[loop] 选中段 %s（%d 行）" % (seg, task["rows"]), flush=True)
    if a.dry:
        board(st, rows, rejects)
        return 0

    try:
        before_runs = set(os.listdir(RUNS))
        before_latest = sorted(x for x in before_runs if re.match(r"^\d{8}-\d{6}$", x))[-1]
    except Exception:
        before_runs, before_latest = set(), None

    ds = os.path.join(SOCIAL, "train-%s" % seg)
    build_cmd = [PY, os.path.join(HERE, "train_build.py"), "--out", ds,
                 # 人味下限：默认 5（现行）。可命令行覆盖，用于"语料可利用率"对照实验——
                 # 抽样实测当前训练集 PASS 56/60、taste<45 为 0 条，说明这道闸把
                 # RISKY 里 40-49 分那 1.8 万条全挡在外面了，值不值得放进来必须实测。
                 "--min-human", str(getattr(a, "min_human", 5)),
                 # 2026-11-21：硬阈值会把段砍成零头（shallow 4396→293），回填到 1200 条
                 # 再训——278 条训 LoRA 等于没训，这是在浪费 50 分钟 GPU。
                 "--target-rows", "1200"]
    if seg != GENERIC:
        build_cmd += ["--seg", seg]
    rc, out = sh(build_cmd, timeout=1200)
    m = re.search(r"train\.jsonl (\d+) 条", out)
    built = int(m.group(1)) if m else 0
    # 训练文件指纹：判"这一课跟上一课是不是同一课"只能靠**真正喂进去的文件**。
    # 2026-11-26 踩坑：先写的版本拿 built_map() 与段状态里的 built 比，两者同源
    # （都来自台账自己的 built 字段），等于自己跟自己比，恒判"未变"——于是所有段
    # 一次性全被挡住。指纹必须来自磁盘上的 train.jsonl。
    fp = dataset_fp(ds)
    if rc != 0 or built < MIN_BUILD:
        print("[loop] 造集不足（rc=%d, %d 条）：%s" % (rc, built, out.strip()[-160:]))
        record_fail(seg, task["rows"], "SUPPLY", "造集不足 %d 条" % built, built)
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="SUPPLY", built=built, fp=fp)
        _save(LOOP_STATE, st)
        board(st, rows, rejects)
        return 0

    # 无人值守也要有"每次只换一个变量"的纪律：同一批数据 + 同一配置重训，产出的是
    # 同一个模型（实锚：music_seeker built 305 三次 KEEP、adapter SHA 完全相同）。
    # 所以由实验矩阵决定这次跑哪个变体；变体跑尽了就如实停手等新语料，
    # 而不是硬跑一份已知结果骗"GPU 没闲着"。
    vid, vwhy, veff = None, "实验矩阵不可用", None
    try:
        import exp_matrix as xm
        vid, vwhy = xm.next_variant(seg, fp, _ledger_rows())
        veff = xm.effective(vid) if vid else None
    except Exception as _e:
        vid, vwhy, veff = None, "实验矩阵不可用：%s" % str(_e)[:60], None
    if not vid:
        print("[loop] 跳过训练：%s（%s，fp=%s）" % (seg, vwhy, fp))
        record_fail(seg, task["rows"], "SAME-DATASET", "%s（fp=%s）" % (vwhy, fp), built)
        st["segments"][seg] = dict(st["segments"].get(seg) or {},
                                   last_rc="SAME-DATASET", built=built, fp=fp)
        _save(LOOP_STATE, st)
        _lane("skip-no-variant", seg=seg, fp=fp, why=str(vwhy)[:60])
        board(st, rows, rejects)
        return 0
    # 手动 --iters 显式覆盖时才认命令行，否则以变体为准
    iters = a.iters if a.iters != 400 else int(veff.get("iters") or a.iters)
    n_layers = int(veff.get("num_layers") or 16)
    seval = int(veff.get("steps_per_eval") or 50)
    lr = veff.get("learning_rate")          # None = 用 train_lora 的默认 1e-5
    bs = veff.get("batch_size")             # None = 默认 1（默认不开大，免得顶 swap）
    print("[loop] 变体 %s：%s" % (vid, vwhy), flush=True)

    # 出稿优先（COMPUTE-SCHEDULE.json lanes.publish priority=1）：
    # 训练一轮 40–50 分钟会连续占住 GPU，而出稿每 30 分钟才要 60 秒。
    # 所以开训前看一眼"出稿是不是快到期了"：到期就先让这一 tick，让它先跑。
    try:
        import practice_due as _pd
        _due, _why = _pd.due(within_s=600, mark=True)
    except Exception:
        _due, _why = False, ""
    if _due:
        print("[loop] 让路：出稿到期（%s），本 tick 不开训" % _why)
        record_fail(seg, task["rows"], "BLOCKED", "让路出稿：" + _why)
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="YIELD-PUBLISH")
        _save(LOOP_STATE, st)
        _lane("yield-publish", seg=seg, why=str(_why)[:80])
        return 0

    # 2026-11-22「快点弄好」：白天训练不许抢出稿。判据两条——
    #   ①有会话在进行（AGENT-SESSION-*）②近 20 分钟有出稿动作。
    # 满足任一条就本轮跳过训练（不是故障），把 GPU 留给"像人一样快"的那条线。
    try:
        from datetime import datetime as _dt
        _h = _dt.now().hour
        # 2026-11-23 CEO「训练为主、实战为否」：运维显式让训练优先时跳过白天让路
        if 9 <= _h < 23 and os.environ.get("FLUX_TRAIN_FORCE") != "1":
            sd = os.path.join(ROOT, ".codely-cli", "state")
            busy = any(f.startswith("AGENT-SESSION-") for f in os.listdir(sd))
            import practice_due as _pd2
            _age = (time.time() - (_pd2.last_activity_ts() or 0)) / 60
            if busy or _age < 20:
                st["segments"][seg] = dict(st["segments"].get(seg) or {},
                                           last_ts=time.time(), last_rc="YIELD-DAY")
                _save(LOOP_STATE, st)
                print("[loop] 白天让路出稿（会话=%s，距上次动作 %.0f 分钟）" % (busy, _age))
                return 0
    except Exception:
        pass

    # 一块 GPU 一把租约：2026-11-21 实测三个消费者（训练/嵌入/自举）同抢，训练从
    # 10 步/分掉到 3.3 步/分，两小时变六小时。拿不到就不抢，写清让路原因，本轮返回 0。
    try:
        import gpu_lease as _gl
        # wait_s=90：原来不设等待＝零耐心，出稿（正常 5 秒）一占就立刻放弃，
        # 而出稿每 12 分钟一次，训练于是长期抢不到窗口（2026-11-26 实锚：
        # 连续三次「让路：publish（已 71s/131s）」）。等 90 秒足够跨过一次出稿。
        _got, _why = _gl.acquire("train", ttl_s=4 * 3600, wait_s=200)
    except Exception as _e:
        _got, _why = True, "租约不可用（%s），不拦" % str(_e)[:40]
    if not _got:
        print("[loop] 让路：%s" % _why)
        record_fail(seg, task["rows"], "BLOCKED", "GPU 让路：" + _why)
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="GPU-BUSY")
        _save(LOOP_STATE, st)
        _lane("yield-gpu", seg=seg, why=str(_why)[:80])
        return 0
    _lane("training", seg=seg, rows=task.get("rows"), iters=iters, variant=vid)
    # 2026-11-22 CEO「太慢了，真人不会这样」：一轮训练 25–45 分钟独占租约，
    # 出稿只能等轮间——白天一整天发不出一条。改成**轮内让路**：训练照跑（GPU 时间片，
    # 不 SIGSTOP），但每 30 秒看一次"出稿是否到期"；到期就把租约让出去最多 3 分钟，
    # 让 publish 拿到锁去生成，然后拿回来。只有在内存余量够（≥4GB）时才让，
    # 否则宁可让 publish 等——不许为了快把机器顶进 swap。
    ystats = {"yields": 0, "blocked": 0, "waited_s": 0.0}

    try:
        cmd = ["/bin/bash", os.path.join(HERE, "train_run.sh"),
               "--data", ds, "--iters", str(iters), "--num-layers", str(n_layers),
               "--max-seq-length", str(seq_len), "--steps-per-eval", str(seval),
               "--grad-checkpoint"]
        if lr:
            cmd += ["--learning-rate", str(lr)]
        if bs:
            cmd += ["--batch-size", str(bs)]
        _p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, cwd=ROOT, start_new_session=True)
        _buf = []

        def _reader(pipe):
            for ln in pipe:
                _buf.append(ln)
                if len(_buf) > 400:
                    del _buf[:-200]

        _th = threading.Thread(target=_reader, args=(_p.stdout,), daemon=True)
        _th.start()
        _last = 0.0
        _t0 = time.time()
        _killed_for_age = False
        while _p.poll() is None:
            # 墙钟上限（2026-11-27 夜班）：一次训练正常 40-50 分钟，租约 TTL 却是 4 小时。
            # 没有这道闸，MLX 一旦死锁，整整 4 小时没人动它——夜里就废了。
            # 超时就整组杀掉并记 TRAIN-TIMEOUT，让下一拍去试别的段/变体。
            if time.time() - _t0 > TRAIN_MAX_S:
                _killed_for_age = True
                print("[loop] 训练超时（%.0f 分钟 > 上限 %.0f），杀进程组" % (
                    (time.time() - _t0) / 60, TRAIN_MAX_S / 60), flush=True)
                try:
                    os.killpg(os.getpgid(_p.pid), 15)
                except Exception:
                    try:
                        _p.terminate()
                    except Exception:
                        pass
                time.sleep(20)
                if _p.poll() is None:
                    try:
                        os.killpg(os.getpgid(_p.pid), 9)
                    except Exception:
                        try:
                            _p.kill()
                        except Exception:
                            pass
                break
            if time.time() - _last >= 30:      # 每 30 秒看一次"出稿是否到期"
                try:
                    import practice_due as _pd
                    import mem_probe as _mp
                    yield_for_publish(_p, _gl, lambda: _pd.due(within_s=600),
                                      _mp.sample, os.path.join(ROOT, ".codely-cli",
                                                               "state", "TRAIN-EXCLUSIVE"),
                                      ystats)
                except Exception:
                    pass
                _last = time.time()
            time.sleep(2)
        _th.join(timeout=5)
        rc = _p.returncode
        if _killed_for_age:
            rc = rc or 124              # 124 = 超时退出码，与 task 失败的 rc 语义一致
            out = "".join(_buf) + "\nTRAIN-TIMEOUT %.0f 分钟" % ((time.time() - _t0) / 60)
            _lane("timeout", seg=seg, minutes=round((time.time() - _t0) / 60))
        if ystats["yields"]:
            print("[loop] 训练期间让路出稿 %d 次（共等 %.0fs，内存不足跳过 %d 次）"
                  % (ystats["yields"], ystats["waited_s"], ystats["blocked"]))
    finally:
        try:
            _gl.release("train")
        except Exception:
            pass
    if rc != 0:
        skip = "SKIP-ALREADY-TRAINING" in out
        print("[loop] 训练%s（rc=%d）：%s" % ("被让路" if skip else "失败", rc,
                                             out.strip().splitlines()[-1][:160] if out.strip() else ""))
        kind = "BLOCKED" if skip else "TRAIN-FAIL"
        record_fail(seg, task["rows"], kind,
                    "被让路" if skip else (out.strip().splitlines()[-1][:120] if out.strip() else "rc=%d" % rc))
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc=kind)
        _save(LOOP_STATE, st)
        _lane("fail", seg=seg, kind=kind, why=str(out.strip().splitlines()[-1][:80]) if out.strip() else "rc=%d" % rc)
        board(st, rows, rejects)
        return 0 if skip else 1

    fresh = [x for x in os.listdir(RUNS)
             if re.match(r"^\d{8}-\d{6}$", x) and x not in before_runs]
    run_name = sorted(fresh)[-1] if fresh else before_latest
    run = os.path.join(RUNS, run_name) if run_name else None
    step, val = val_min_step(run) if run else (None, None)
    print("[loop] 训练完成 %s · val 最低 %s @%s 步" % (os.path.basename(run), val, step), flush=True)
    ck, real_step = ckpt_dir(run, step) if step else (None, None)
    if real_step and step and real_step != step:
        print("[loop] val 最低在 %s 步，权重实际取最近已存点 %s 步" % (step, real_step))
    base = lora = {}
    if ck:
        segs = list(GENERIC_EVAL_SEGS) if seg == GENERIC else [seg]
        rc, out = sh([PY, os.path.join(HERE, "train_eval.py"), "--run", run,
                      "--per-segment", "--segs", ",".join(segs),
                      "--samples", str(a.samples), "--adapter", ck], timeout=3600)
        ev = _load(os.path.join(TRAIN, "SEGMENT-EVAL.json"), {}) or {}
        bs = ev.get("base") or []
        ls = ev.get("lora") or []
        if not bs or not ls:
            base, lora = {}, {}
        else:
            # 全量卡：取各段的均值；任一段掉超过 2 分就在 judge 里被否（human_delta 记最差段）
            base = {"n": min(int(x.get("n") or 0) for x in bs),
                    "avg": round(sum(float(x.get("avg") or 0) for x in bs) / len(bs), 1),
                    "pass_rate": round(sum(int(x.get("pass_rate") or 0) for x in bs) / len(bs)),
                    "avg_human": round(sum(float(x.get("avg_human") or 0) for x in bs) / len(bs), 1)}
            lora = {"n": min(int(x.get("n") or 0) for x in ls),
                    "avg": round(sum(float(x.get("avg") or 0) for x in ls) / len(ls), 1),
                    "pass_rate": round(sum(int(x.get("pass_rate") or 0) for x in ls) / len(ls)),
                    "avg_human": round(sum(float(x.get("avg_human") or 0) for x in ls) / len(ls), 1)}
            if seg == GENERIC:
                worst = min((float(l.get("avg") or 0) - float(b.get("avg") or 0))
                            for b, l in zip(bs, ls))
                if worst < -2:
                    base["avg"] = lora["avg"] + KEEP_GAIN + 1   # 强制判否：任一段明显退步

    if not ck or not base or not lora:
        # 评测没跑成本身是工具故障，不是"模型不行"：不许写进被否记忆去堵这个段。
        print("[loop] 评测缺失（ck=%s base=%s lora=%s）→ 记 EVAL-MISSING，不动被否记忆"
              % (bool(ck), bool(base), bool(lora)))
        rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built,
               "run": os.path.basename(run), "step": real_step, "val_step": step,
               "val_min": val, "eval_n": 0,
               "verdict": "EVAL-MISSING", "why": "找不到 checkpoint 或评测没产出",
               "adapter": os.path.relpath(ck, ROOT) if ck else None}
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="EVAL-MISSING", run=rec["run"], step=real_step,
                                   val_min=val)
        st["runs"].append(rec)
        _save(LOOP_STATE, st)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        board(st, rows, rejects)
        return 1

    keep, why = judge_keep(base, lora)
    human_delta = round(float(lora.get("avg_human") or 0) - float(base.get("avg_human") or 0), 1)
    eval_n = min(int(base.get("n") or 0), int(lora.get("n") or 0))
    verdict = ("INSUFFICIENT" if eval_n < MIN_EVAL_N
               else ("KEEP" if keep else "REJECT"))
    if eval_n < MIN_EVAL_N:
        keep = False
    rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built, "eval_n": eval_n,
           "run": os.path.basename(run), "step": real_step, "val_step": step,
           "val_min": val, "recipe": RECIPE_V,
           # fp+variant 是实验矩阵的唯一性键：没有它们，下一轮无法判断
           # "这批数据的这个配置是不是已经问过"（缺了就会重复跑同一课）。
           "fp": fp, "variant": vid, "iters": iters, "num_layers": n_layers,
           "steps_per_eval": seval, "learning_rate": lr, "batch_size": bs,
           "base_avg": base.get("avg"), "lora_avg": lora.get("avg"),
           "base_human": base.get("avg_human"), "lora_human": lora.get("avg_human"),
           "human_delta": human_delta, "verdict": "KEEP" if keep else "REJECT",
           "why": why, "adapter": os.path.relpath(ck, ROOT) if ck else None}
    st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                               last_rc=verdict, recipe=RECIPE_V, rows=task["rows"],
                               built=built, fp=fp, run=rec["run"], step=real_step, val_min=val)
    st["runs"].append(rec)
    _save(LOOP_STATE, st)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _lane("done", seg=seg, verdict=("KEEP" if keep else "REJECT"),
          built=built, lora_avg=lora.get("avg"), base_avg=base.get("avg"))

    # 边训练边总结经验：每落一卡就把台账重算成"可被推翻的断言"（幂等；失败不影响训练）
    try:
        subprocess.run([sys.executable, os.path.join(HERE, "train_lessons.py"), "--write"],
                       capture_output=True, timeout=60)
    except Exception:
        pass

    if verdict == "INSUFFICIENT":
        print("[loop] 段 %s 样本不足（n=%d），既不归档也不记被否——先加大评测条数" % (seg, eval_n))
    elif keep and ck:
        # 权重去重（2026-11-27）：变体虽然不同，最终选中的 checkpoint 可能是同一步，
        # 于是落出**完全相同的权重**（实锚：今天 9 个归档里有 2 对 SHA 相同）。
        # 同款权重再存一份等于把库存和"产量"都注水，所以不入档、判词降为 DUPLICATE。
        _sha = weight_sha(ck)
        _dup = seen_weight_sha().get(_sha)
        if _sha and _dup:
            print("[loop] 段 %s 训出的权重与已有件完全相同（%s），不重复入档" % (seg, _sha))
            _lane("duplicate-weight", seg=seg, sha=_sha, same=_dup[:2])
            return 0
        dst = os.path.join(ARCHIVE, "%s-%s-ckpt%s" % (time.strftime("%Y%m%d-%H%M%S"), seg, step))
        os.makedirs(dst, exist_ok=True)
        for fn in ("adapters.safetensors", "adapter_config.json"):
            src = os.path.join(ck, fn)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(dst, fn))
        print("[loop] 段 %s 留档 → %s（%s）" % (seg, dst, why))
    else:
        rejects[seg] = {"n": int((rejects.get(seg) or {}).get("n") or 0) + 1,
                        "rows": task["rows"], "ts": now_iso(), "why": why}
        _save(REJECTS, rejects)
        print("[loop] 段 %s 不采用（%s）→ 先补语料再训" % (seg, why))
    board(st, rows, rejects)
    # 跑完一卡顺手做一次保守清理（判据见 prune_runs；失败不影响训练）
    try:
        prune_runs(keep_hours=6)
    except Exception:
        pass
    return 0


def self_test():
    global LEDGER
    cases = []
    # tick 锁：同进程第二次抢占必须失败（否则 60 秒轮询会重复造集）
    cases.append(("tick 锁：第二次抢占必须被挡", _claim_tick() and not _claim_tick()))
    # 数据集指纹：同内容必须同 fp、不同内容必须不同 fp、缺失必须为空。
    # 这条闸曾经写成"拿台账里的 built 跟台账里的 built 比"（同源自比，恒判未变），
    # 结果所有段一次性全被挡住——所以指纹必须来自磁盘文件，且要能被负控抓出来。
    import tempfile as _tf
    _d = _tf.mkdtemp(prefix="fp-")
    try:
        _p = os.path.join(_d, "train.jsonl")
        open(_p, "w").write('{"text":"甲"}\n')
        fp1 = dataset_fp(_d)
        fp1b = dataset_fp(_d)
        open(_p, "w").write('{"text":"乙"}\n')
        fp2 = dataset_fp(_d)
        cases.append(("指纹：同内容同 fp、不同内容不同 fp", fp1 and fp1 == fp1b and fp1 != fp2))
        cases.append(("指纹：文件不存在返回空（不许瞎比）", dataset_fp(os.path.join(_d, "nope")) == ""))
    finally:
        import shutil as _sh
        _sh.rmtree(_d, ignore_errors=True)
    rows = {"a": 300, "b": 50}
    st = {}
    rj = {}
    ok, _ = eligible("a", rows, st, rj)
    cases.append(("语料够且没训过 → 可训", ok))
    ok2, why2 = eligible("b", rows, st, rj)
    cases.append(("语料不足 → 不可训", not ok2 and "200" in why2))
    st2 = {"segments": {"a": {"last_ts": time.time() - 600, "recipe": RECIPE_V}}}
    ok3, why3 = eligible("a", rows, st2, rj)
    cases.append(("冷却中 → 不可训", not ok3 and "冷却" in why3))
    # 负控 2026-11-26：状态缺 recipe（历史台账没字段）且刚训过 → 必须仍被冷却挡住，
    # 不许因为"配方不明"就立刻重训（实锚：同一段 3.5h 重训一次，指纹完全相同）。
    st2b = {"segments": {"a": {"last_ts": time.time() - 600}}}
    ok3b, why3b = eligible("a", rows, st2b, rj)
    cases.append(("缺 recipe 但在冷却内 → 不可训", not ok3b and "冷却" in why3b))
    st3 = {"segments": {"a": {"last_ts": 0, "recipe": RECIPE_V}}}
    rj2 = {"a": {"rows": 300}}
    ok4, why4 = eligible("a", rows, st3, rj2)
    cases.append(("被否且语料未涨 15% → 不可训", not ok4 and "未涨" in why4))
    # 反复被否的段：累计 ≥10 次后只有"翻倍"才放行（负控：涨 15% 不够）
    rj_hard = {"a": {"n": HARD_REJECT_N, "rows": 300}}
    okh, whyh = eligible("a", {"a": 400}, st3, rj_hard)
    cases.append(("被否10次后：涨15% 不够 → 不可训", (not okh) and "不再重复" in whyh))
    oky, _ = eligible("a", {"a": 650}, st3, rj_hard)
    cases.append(("被否10次后：语料翻倍 → 可训", oky))
    rows2 = {"a": 400}
    ok5, _ = eligible("a", rows2, st3, rj2)
    cases.append(("被否但语料涨够 → 可训", ok5))
    # 选段排序：同档（都没训过）时按烘焙后可用语料，而不是原始 rows。
    # 负控 2026-11-23：a 的 rows 更大但 built 更小，必须选 b。
    rows_c = {"a": 900, "b": 500}
    task, _ = pick(rows_c, {}, {}, time.time(), built={"a": 120, "b": 480})
    cases.append(("同档按 built 排序（rows 大但烘焙少的不优先）",
                  task is not None and task["seg"] == "b"))
    # 反向负控：把 built 反过来，必须选回 a（否则等于排序没生效）
    task2, _ = pick(rows_c, {}, {}, time.time(), built={"a": 480, "b": 120})
    cases.append(("built 反过来后应选 a（排序真的在起作用）",
                  task2 is not None and task2["seg"] == "a"))
    # 无 built 历史 → 回退 original rows（不许因为缺数据就什么都不选）
    task3, _ = pick(rows_c, {}, {}, time.time(), built={})
    cases.append(("无 built 历史时回退 rows", task3 is not None and task3["seg"] == "a"))
    B = {"n": 30, "avg": 50, "sd": 12, "pass_rate": 60, "avg_human": 20}
    keep, _ = judge_keep(B, {"n": 30, "avg": 56, "sd": 12, "pass_rate": 60, "avg_human": 20})
    cases.append(("均分 +6 且人味不退 → KEEP", keep))
    # 负控 2026-11-27：改进没超过噪声就不许 KEEP（实锚 tech_nerd +4.6 被判不及格）
    # 过 5 分线但没超过噪声（sd=30、n=30 → se≈7.8，gain=6）——典型"看着涨了其实是抖"
    nk, nwhy = judge_keep({"n": 30, "avg": 54.0, "sd": 30, "pass_rate": 50, "avg_human": 20},
                          {"n": 30, "avg": 60.0, "sd": 30, "pass_rate": 55, "avg_human": 20})
    cases.append(("改进未超过噪声 → 不许 KEEP", (not nk) and "噪声" in nwhy))
    # 负控：n<30 一律不判（memer n=10 假 KEEP 的根治手段）
    small, swhy = judge_keep({"n": 10, "avg": 38.7, "sd": 9, "pass_rate": 40, "avg_human": 15},
                             {"n": 10, "avg": 48.4, "sd": 9, "pass_rate": 50, "avg_human": 18})
    cases.append(("n=10 不判（哪怕看着 +9.7）", (not small) and "样本不足" in swhy))
    keep2, why6 = judge_keep(B, {"n": 30, "avg": 60, "sd": 12, "pass_rate": 60, "avg_human": 17})
    cases.append(("总分涨但人味掉 3 → 不采用", (not keep2) and "人味" in why6))
    keep3, _ = judge_keep(B, {"n": 30, "avg": 52, "sd": 12, "pass_rate": 70, "avg_human": 20})
    cases.append(("均分只 +2 → 不采用", not keep3))
    # 天花板闸：n≥30 的基座高分要能读到；n=10 的记录不许拿来设天花板（本身就是抖）
    import tempfile as _tf2
    _saved2 = LEDGER
    _fd2, _tmp2 = _tf2.mkstemp()
    os.close(_fd2)
    try:
        with open(_tmp2, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2026-11-27T00:00:00", "seg": "hi",
                                "eval_n": 30, "base_avg": 85.5}) + "\n")
            f.write(json.dumps({"ts": "2026-11-27T00:10:00", "seg": "lo",
                                "eval_n": 10, "base_avg": 90.0}) + "\n")
        LEDGER = _tmp2
        cases.append(("天花板：n≥30 的基座高分能读到", ceiling_of("hi") == 85.5))
        cases.append(("天花板：n=10 的记录不许设天花板", ceiling_of("lo") is None))
    finally:
        LEDGER = _saved2
    keep4, why7 = judge_keep({"n": 3, "avg": 30, "pass_rate": 0, "avg_human": 0},
                             {"n": 3, "avg": 90, "pass_rate": 100, "avg_human": 30})
    cases.append(("只有 3 条样本 → 不判（噪声 ±30 分）",
                  (not keep4) and "样本不足" in why7))
    # 负控 2026-11-26：reconcile 重建状态时必须保住 recipe。
    # 丢了它，eligible() 就永远判「配方更新」放行，冷却与被否后的 15% 增长闸静默失效
    # （实锚：8 段里 7 段 recipe=None，同一段 3.5h 重训一次，17 次 run 只出 7 个模型）。
    import tempfile
    _saved_ledger = LEDGER
    _tmp = None
    try:
        _fd, _tmp = tempfile.mkstemp()
        os.close(_fd)
        with open(_tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2026-11-26T00:00:00", "seg": "a", "rows": 300,
                                "verdict": "REJECT", "recipe": RECIPE_V}) + "\n")
        LEDGER = _tmp
        st_r = reconcile({"segments": {}, "runs": []})
        cases.append(("reconcile 保住 recipe（否则冷却闸失效）",
                      st_r["segments"]["a"].get("recipe") == RECIPE_V))
        with open(_tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2026-11-26T00:00:00", "seg": "b", "rows": 300,
                                "verdict": "REJECT"}) + "\n")
        st_r2 = reconcile({"segments": {}, "runs": []})
        cases.append(("台账里没有 recipe 时如实为空（不编造）",
                      st_r2["segments"]["b"].get("recipe") is None))
        # 负控 2026-11-26 坏卡循环：BLOCKED（让路）不得推进冷却时钟。
        # 实锚：21:06→21:25 同一段被重排 7 次、每次 built=0，因为让路记录刷新了 last_ts
        # 且抹掉了 recipe，eligible() 每轮都判「配方更新」放行。
        with open(_tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2026-11-26T00:00:00", "seg": "c", "rows": 300,
                                "verdict": "KEEP", "recipe": RECIPE_V, "step": 400}) + "\n")
            f.write(json.dumps({"ts": "2026-11-26T00:05:00", "seg": "c", "rows": 300,
                                "verdict": "BLOCKED", "recipe": RECIPE_V,
                                "no_progress": True}) + "\n")
        st_r3 = reconcile({"segments": {}, "runs": []})
        lag = st_r3["segments"]["c"].get("last_ts") or 0
        cases.append(("BLOCKED 不推进冷却时钟（坏卡循环根治）",
                      abs(lag - time.mktime(time.strptime("2026-11-26T00:00:00",
                                                          "%Y-%m-%dT%H:%M:%S"))) < 2
                      and st_r3["segments"]["c"].get("last_blocked_ts")))
        # 负控：让路记录也必须带 recipe（否则下一次读台账又丢配方）
        with open(_tmp, "w", encoding="utf-8") as f:
            pass
        LEDGER = _tmp
        record_fail("d", 300, "BLOCKED", "被让路")
        rec_d = [json.loads(x) for x in open(_tmp, encoding="utf-8") if x.strip()][-1]
        cases.append(("record_fail 必须写 recipe 且标 no_progress",
                      rec_d.get("recipe") == RECIPE_V and rec_d.get("no_progress") is True))
        # 负控 2026-11-26：复验行（social_loop 写的，只有 run/verdict/adapter）
        # 不许推进训练时钟，也不许把已有 built/recipe 抹成空。
        with open(_tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2026-11-26T10:00:00", "seg": "e", "rows": 400,
                                "built": 320, "verdict": "KEEP",
                                "recipe": RECIPE_V, "step": 400}) + "\n")
            f.write(json.dumps({"ts": "2026-11-26T12:00:00", "seg": "e", "verdict": "REJECT",
                                "why": "均分只 -8.9（需 ≥5.0）", "run": "x",
                                "re_verify": True, "adapter": "a"}) + "\n")
        st_r4 = reconcile({"segments": {}, "runs": []})
        e = st_r4["segments"]["e"]
        t10 = time.mktime(time.strptime("2026-11-26T10:00:00", "%Y-%m-%dT%H:%M:%S"))
        cases.append(("复验不推进训练时钟（否则白给 6h 冷却）",
                      abs((e.get("last_ts") or 0) - t10) < 2))
        cases.append(("复验缺 built/recipe 时不抹掉已有关（同款闸不许失效）",
                      e.get("built") == 320 and e.get("recipe") == RECIPE_V))
        cases.append(("复验仍留下 last_verify_rc（判决可查）",
                      e.get("last_verify_rc") == "REJECT"))
    finally:
        LEDGER = _saved_ledger
        if _tmp:
            try:
                os.remove(_tmp)
            except Exception:
                pass

    okc = 0
    cases.append(("电池供电→拒绝开训", power_verdict(False, False)[0] is False))
    cases.append(("低功耗模式→拒绝开训", power_verdict(True, True)[0] is False))
    cases.append(("接电且非低功耗→放行", power_verdict(True, False)[0] is True))
    for name, cond in cases:
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
        okc += 1 if cond else 0
    print("[self-test] %d/%d" % (okc, len(cases)))
    return 0 if okc == len(cases) else 1


def _swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=10).stdout
        m = re.search(r"used = ([0-9.]+)M", out)
        return float(m.group(1)) if m else None
    except Exception:
        return None


def mem_verdict(need_gb=5.0, sample_s=5):
    """开训前的内存闸：**看增长，不看存量**。

    CEO 的要求是"不要触发 swap"，判据就必须是"训练期间 swap 是否在涨"。
    拿历史存量当判据会让机器永久降档——本机 swap 已累积 3.4GB（多为白天办公留下的），
    但它稳定不涨时开训并不会新增换页。所以：
      · 采样 sample_s 秒的 swap 增量换速率：>50MB/min = 正在换页 → 不开训（WAIT）
      · 10~50MB/min = 有压力 → 降序列到 256（DOWNGRADE）
      · 否则按 mem_gate 的绝对预算兜底（可用内存装不下 5GB 才降/拒）
    """
    a = _swap_mb()
    time.sleep(sample_s)
    b = _swap_mb()
    if a is not None and b is not None:
        rate = (b - a) / float(sample_s) * 60.0
        if rate > 50:
            return False, 320, "swap 正在增长 %.0fMB/min（%0.0f→%0.0fMB），开训就是硬扛换页" % (
                rate, a, b)
        if rate > 10:
            return True, 256, "swap 有增长 %.0fMB/min（%0.0f→%0.0fMB）→ 序列 320 降到 256" % (
                rate, a, b)
    try:
        sys.path.insert(0, HERE)
        import mem_gate
        d = mem_gate.decide(need_gb)
        if (d.get("model_max_gb") or 0) < 3.3:
            return True, 256, "可用内存只剩 %.1fGB（swap 存量 %.1fGB 稳定）→ 序列降到 256" % (
                d.get("model_max_gb") or 0, d.get("swap_used_gb") or 0)
    except Exception:
        pass
    return True, 320, ""


def power_verdict(on_ac, lowpowermode):
    """能不能开训（纯函数，可自检）。

    2026-11-20 实锚：电池 + 低功耗模式下同一段训练实测 **18.6 秒/步**，
    接电时 4 秒/步 —— GPU 被系统限速近 5 倍，而且电量一小时见底，
    跑到一半断电等于整轮白烧。这不是"保守"，是硬件上限。
    """
    if not on_ac:
        return False, "电池供电：GPU 被限速（实测 18.6s/步 vs 接电 4s/步），且会在一小时内耗尽电量"
    if lowpowermode:
        return False, "低功耗模式开着：GPU 被限速，等关掉再训"
    return True, ""


def power_ok():
    try:
        batt = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True,
                              timeout=10).stdout
        cfg = subprocess.run(["pmset", "-g"], capture_output=True, text=True, timeout=10).stdout
        on_ac = "AC Power" in batt
        low = re.search(r"lowpowermode\s+(\d)", cfg)
        return power_verdict(on_ac, bool(low and low.group(1) == "1"))
    except Exception:
        return True, ""    # 读不到就别拦，避免把"读不到"当"不能训"


def yield_for_publish(proc, gl, due_fn, mem_fn, sentinel, ystats, cap_s=180, sleep_fn=time.sleep):
    """出稿到期时暂停训练（SIGSTOP 进程组），松租约与哨兵，发完 SIGCONT 续训。

    抽成模块级是为了能被自检直接调用：真起一个子进程、真发信号，断言它确实被停过又续上。
    返回 True 表示让过路。禁止事项：只暂停不杀；内存余量 <4GB 不动；最长 cap_s 秒。
    """
    owed, _why = due_fn()
    if not owed:
        return False
    s = mem_fn()
    if (s.get("headroom_gb") or 0) < 4.0:
        ystats["blocked"] += 1
        return False
    import signal as _sig
    try:
        os.killpg(os.getpgid(proc.pid), _sig.SIGSTOP)
    except Exception:
        return False
    try:
        gl.release("train")
    except Exception:
        pass
    stashed = sentinel + ".yielded"
    if os.path.exists(sentinel):
        try:
            os.rename(sentinel, stashed)
        except Exception:
            pass
    ystats["yields"] += 1
    t0 = time.time()
    while time.time() - t0 < cap_s:
        ok, _w2 = due_fn()
        req = os.path.join(ROOT, ".codely-cli", "state", "PUBLISH-REQUEST")
        if not ok or not os.path.exists(req):
            break
        sleep_fn(10)
    ystats["waited_s"] += round(time.time() - t0, 1)
    try:
        if os.path.exists(stashed):
            os.rename(stashed, sentinel)
    except Exception:
        pass
    try:
        os.killpg(os.getpgid(proc.pid), _sig.SIGCONT)
    except Exception:
        pass
    gl.acquire("train", ttl_s=4 * 3600, wait_s=180)
    return True


def _self_test_yield():
    """真起一个子进程，验证：到期→SIGSTOP→哨兵挪走→发完→SIGCONT→哨兵还原。

    负控三件：①不到期不许停；②内存余量 <4GB 不许停；③停过之后进程必须还活着。
    """
    import subprocess, tempfile, signal
    d = tempfile.mkdtemp(prefix="yield-")
    sent = os.path.join(d, "TRAIN-EXCLUSIVE")
    open(sent, "w").write("x")
    p = subprocess.Popen(["/bin/bash", "-c", "for i in $(seq 1 300); do echo $i; sleep 0.1; done"],
                         stdout=subprocess.DEVNULL, start_new_session=True)

    class _GL:
        def __init__(self):
            self.released = self.acquired = 0

        def release(self, n):
            self.released += 1

        def acquire(self, n, ttl_s=0, wait_s=0):
            self.acquired += 1
            return True, ""

    cases = {}
    st = {"yields": 0, "blocked": 0, "waited_s": 0.0}
    gl = _GL()
    # 负控①：不到期
    r1 = yield_for_publish(p, gl, lambda: (False, "未到期"), lambda: {"headroom_gb": 10},
                           sent, st, cap_s=1, sleep_fn=lambda s: None)
    cases["不到期不停"] = (r1 is False and gl.released == 0)
    # 负控②：内存不足
    r2 = yield_for_publish(p, gl, lambda: (True, "到期"), lambda: {"headroom_gb": 2},
                           sent, st, cap_s=1, sleep_fn=lambda s: None)
    cases["内存不足不停"] = (r2 is False and st["blocked"] == 1 and gl.released == 0)
    # 正控：到期 → 停 → 挪哨兵 → 发完 → 续 → 还原
    due_calls = {"n": 0}

    def _due():
        due_calls["n"] += 1
        return (due_calls["n"] <= 2, "到期")      # 第三次调用时已发出去

    r3 = yield_for_publish(p, gl, _due, lambda: {"headroom_gb": 10}, sent, st,
                           cap_s=30, sleep_fn=lambda s: None)
    stat = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(p.pid)],
                          capture_output=True, text=True).stdout.strip()
    cases["正控：让路并还原"] = (r3 is True and gl.released == 1 and gl.acquired == 1
                               and os.path.exists(sent) and "T" not in stat)
    cases["进程仍存活"] = stat != "" and "Z" not in stat
    p.kill()
    ok = all(cases.values())
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "cases": cases},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    # 2026-11-21 CEO「加快频率训练」：500→400 步，一轮从约 55 分钟压到约 45 分钟，
    # 一天能多跑 4–5 轮。代价是 epoch 从 1.1 降到 0.9——比"训得慢但只学一遍"更亏的是
    # "一天只训几遍"，所以先换频率；数据量涨上来（自举/更多真实语料）再回调步数。
    ap.add_argument("--iters", type=int, default=400)
    ap.add_argument("--min-human", type=int, default=5, dest="min_human",
                    help="造集的人味下限（默认 5；调低用于验证是否值得吃进更多语料）")
    ap.add_argument("--self-test-yield", action="store_true")
    ap.add_argument("--samples", type=int, default=30,
                    help="每段评测条数；3 条时同一权重两次评测得 +46.7 与 +16.6（噪声 ±30）")
    ap.add_argument("--seg", default=None,
                    help="手动指定这一段（跳过队列与冷却，运维复核用；仍照常落台账）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if getattr(a, "self_test_yield", False):
        return _self_test_yield()
    if a.self_test:
        return self_test()
    return run_one(a)


if __name__ == "__main__":
    sys.exit(main())
