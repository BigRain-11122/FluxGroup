#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""master_pulse.py - the single pulse of the bm-m control plane.

Why this exists (2026-10-30 measured, not guessed):
  * three schedulers fired the same tick (member 60s, master 120s, dashboard 20s), so
    two writers raced on the same state files and the contingency engine died with
    FileNotFoundError on its temp rename;
  * a master_agent run could hang indefinitely, holding the pulse silent while launchd
    kept "succeeding";
  * `git pull --rebase --autostash` swallowed uncommitted hand edits into a stash.

Design:
  one lock (nothing runs twice), pull only on a clean tree, every stage bounded by a
  timeout, and PULSE.json as a heartbeat any other program can read to prove liveness.

Cadence: dispatch-critical stages run every pulse (60s); the heavier maintenance stages
(health/contingency/inventory/judge/brain) run at most once per SLOW_EVERY seconds, so a
slow disk or a busy model can never make the 60s tick overlap with itself.

Usage:
  python3 Tools/fleet/master_pulse.py            # one pulse
  python3 Tools/fleet/master_pulse.py --no-pull  # skip git
  python3 Tools/fleet/master_pulse.py --force-slow  # run maintenance stages now
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NODE = os.environ.get("NODE", "bm-m")
PY = sys.executable or "/usr/bin/python3"
LOCK = "/tmp/fluxgroup-pulse.lock"
LOG = "/tmp/fluxgroup-pulse.log"
STATE_REL = "cph4/fleet/dispatcher/PULSE.json"
SLOW_EVERY = 300
STATE_SNAPSHOT_S = 1800   # 报告类状态每 30 分钟快照一次（此前每 60 秒，占全部提交 44%）
HOT_PREFIXES = ("cph4/fleet/lanes/", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
                "cph4/fleet/PRODUCTION-BACKLOG.jsonl", "cph4/fleet/dispatcher/MASTER-STATE.json",
                "cph4/fleet/dispatcher/MASTER-TICK.json")   # maintenance batch runs in parallel now, so 5 min is affordable

# (name, argv, timeout_s, ok_rc, slow)
STAGES = [
    ("hb", ["Tools/fleet/fleet_hb.py", "--node", NODE, "--root", ROOT], 60, {0}, False),
    # SUPPLY FIRST (CEO 2026-11-01: 不许因为是"没人宣告"就闲置). Both declare-work seats
    # existed since 10-31 but were never wired into the pulse, so they only ran when a
    # human remembered - boxes idled with an empty backlog while the generators sat idle.
    # They are queue writers, so they run serially before the dispatcher reads the queue.
    ("night_plan", ["Tools/fleet/night_plan.py"], 120, {0}, False),
    # 工序推进（2026-11-03）：把 ri/*/lines/*.json 的工序表变成真生产卡（READY），
    # 必须先于 night_fill，否则补料侧永远只有"体检卡"可提。
    # 两道门（2026-11-03 CEO：务必有质量验收与市场调研，不产出垃圾）：
    # 市场门=简报五要素+新鲜度；质量门=交付必须有闸回执。rc=2 是"有缺口"的告警。
    ("market", ["Tools/fleet/market_brief.py", "check", "--all"], 30, {0, 2}, True),
    ("quality", ["Tools/fleet/quality_gate.py", "--all", "--json"], 60, {0, 2}, True),
    # 工序表结构错（悬空依赖/成环/缺 accept）会让整条线静默停摆，rc=2 是"表坏了"的告警。
    ("line_plan", ["Tools/fleet/line_plan.py"], 60, {0, 2}, False),
    ("night_fill", ["Tools/fleet/night_fill.py", "--target", "6"], 90, {0}, False),
    # 银行自动补料（2026-11-03，曾被并行会话的 STAGES 整表重写静默丢掉一次——重加并留痕）：
    # workgen 只认 bank 里现成的卡片，bank 空了机器就空转；本阶段按机器能力补体检活，
    # 并销掉"产物已在盘却仍标 pending"的僵尸条目。必须在 workgen 之前。
    ("bank_autofill", ["Tools/fleet/bank_autofill.py", "--root", ROOT], 60, {0}, False),
    ("workgen", ["Tools/fleet/workgen.py", "--root", ROOT], 180, {0}, False),
    ("master", ["Tools/fleet/master_agent.py", "--node", NODE, "--root", ROOT], 240, {0}, False),
    ("lane", ["Tools/fleet/lane_agent.py", "--node", NODE, "--root", ROOT, "--no-fetch"], 300, {0}, False),
    # inventory exits 1 to say "a lane is STARVED"; that is an alert, not a tool failure.
    ("inventory", ["Tools/fleet/inventory_guard.py"], 120, {0, 1}, True),
    # 事实层（2026-11-02 FLUX OS v2）：先把磁盘事实与结构断言跑一遍，再谈派单。
    # census 写 state/lines.json（I14 与 metrics 都依赖它），因此放在慢批串行最前。
    ("census", ["Tools/fleet/census.py"], 180, {0}, True),
    # 研究创新席（2026-11-02 CEO 令）：体检四席的边界与空转，顺手刷新 PROPOSALS.json
    # 供派单方择取。rc=2 是有违规的告警，不是工具坏，所以计入 ok_rc。
    ("ri", ["Tools/fleet/ri_dept.py", "check"], 60, {0, 2}, True),
    # 认知基座校验（2026-11-03 CEO「对这条业务线进行全面的认知改造」）：文档说的和工序跑的
    # 必须是同一套——基座在位/必填段落齐/≤90 天/工序表段 id 能在基座里找到。rc=2 = 认知漂移。
    ("canon", ["Tools/fleet/line_canon.py", "--all"], 60, {0, 2}, True),
    # 城市面清单（2026-11-03 CEO「梳理硅基城市元宇宙的顶层设计与工作流」）：12 面逐项核对
    # 盘上证据，自称在役但证据不可见自动降级为受阻（假绿比空白更糟）。rc=1=有受阻/空白，告警不阻断。
    ("city", ["Tools/fleet/city_state.py", "--out", "cph4/fleet/state/city-state.json"], 60, {0, 1}, True),
    # 技能库质量闸（2026-11-03）：45 件逐条判结构/触发词/自检/死指针，落 state/skills-check.json。
    # 只报告不阻断（默认非 --strict），因为 30 件早期导入件仍是口号型，阻断会变成常驻红灯。
    ("skills", ["Tools/fleet/skill_check.py"], 60, {0}, True),
    # 技能升级 agent（2026-11-03 CEO「你做不到就写个 agent 来做」）：把技能正文已点名的真工具
    # 跑一遍 --help，只把"实测跑过"的命令写回技能，绝不编内容；幂等，每轮最多升 2 件。
    ("skill_promote", ["Tools/fleet/skill_promote.py", "--limit", "2"], 120, {0}, True),
    # 端到端自检（2026-11-02 CEO 质问后的唯一验收口径）：每轮投一张真卡，
    # 走 pick→claim→run→receipt→state→artifact，断在哪一环就指名。rc=2 = 链断。
    ("canary", ["Tools/fleet/canary.py"], 120, {0}, True),
    # 冷备（2026-11-02 实测：脚本从来没人调度，备份仓落后 341 个提交而报表全绿）。
    # 盘不在会写 state/backup.json 的 UNMOUNTED，并 rc=0 退出，不让掉盘拖红主控脉。
    ("backup", ["Tools/fleet/backup_sync.sh"], 300, {0}, True),
    # 一屏：所有业务的最下一步（CEO 2026-11-03「随时能给出下一步任务」）。
    ("next_actions", ["Tools/fleet/next_actions.py"], 60, {0, 2}, True),
    # 前瞻：每条线剩余弹药与卡点（CEO 2026-11-03「不许等机队没活了」）。
    # 只报告不阻断：runway<2 天会打 ALERT 行，告警由人看或后续接排队。
    ("forecast", ["Tools/fleet/forecast.py"], 60, {0, 2}, True),
    ("gate", ["Tools/fleet/gate_report.py"], 180, {0}, True),
    ("checkups", ["Tools/fleet/checkups.py"], 180, {0, 2}, True),
    ("metrics", ["Tools/fleet/ops_metrics.py"], 90, {0}, True),
    # 事件日志（2026-11-03 S1 影子期）：先把本机 outbox 发到 JetStream，再拉本机未消费事件。
    # 走快批（每轮都跑）而不是慢批：慢批 300 秒节流会让事件积压成"五分钟前的事实"。
    # 只写不读——生产链路一次也不等它；rc=2 只表示总线不通，不影响派单。
    ("eventlog", ["Tools/fleet/flux_eventlog.py", "tick", "--node", NODE], 90, {0}, False),
    # 本地模型雷达（2026-11-03 CEO：每天扫描并测试是否有更新）：脚本自带"一天只跑一次"闸，
    # 放慢批即可；rc=2 只表示"上游有新版本待裁定"，不是故障。
    ("modelradar", ["Tools/fleet/model_radar.py", "run"], 900, {0, 2}, True),
    # 字幕自动来源（2026-11-03 CEO「可以 你自动化推进下去」）：成片没有 SRT 就用本机 GPU ASR 补一份，
    # 落到 drama-dept-v1/subs/，判据 7 从此有链上一手产出，而不是靠人给或靠装配器自己申报。
    # 吃 GPU 但自带"一天只跑一次"日期闸，放慢批；rc=3 只表示后端没装/目录不在，不算故障。
    ("asr_subs", ["Tools/fleet/subs_asr.py", "--sync-dir", "media/drama-out",
                  "--subs-dir", "cph4/fleet/drama-dept-v1/subs", "--days", "7"], 900, {0, 1, 3}, True),
    # 审片副本（2026-11-03 CEO「好好利用本地算力」）：硬件编码出 720p，一次最多 6 条，幂等。
    # 目的=CEO 点开就能看，不用等下 12MB 的 1080p 原片；Mac 的正当用法（只做交付，不做创作）。
    ("review_proxy", ["Tools/fleet/review_proxy.py", "--src", "media/drama-out",
                      "--out", "media/review-720p", "--max", "6"], 300, {0, 3}, True),
    # 资产生产规格（2026-11-03 CEO「Mac 利用率很低」）：本机常驻 4B 批量写 P0 资产规格，
    # 幂等可续跑，一轮最多 20 件。实测 GPU 99%、CPU 仍 83% 空闲——低利用率的表象是
    # "只看 CPU"，真因是没喂本机吃得下的活。rc=3=模型服务不在。
    ("asset_prompts", ["Tools/fleet/asset_prompts.py", "--limit", "20"], 600, {0, 1, 3}, True),
    # 本机推理栈体检（2026-11-03）：端口归属/服务环境/速度/向量层，一天一次。
    # 只是体检，不改配置；rc=2=有 GAPS 待修。
    ("inference_audit", ["Tools/fleet/local_inference_audit.py", "--node", NODE, "--daily"], 300, {0, 2}, True),
    # 全域优化面日报（2026-11-03 CEO「你要考虑的比我全面和科学」）：把 9 域 42 项里
    # 还没做的条目每轮摆出来，避免只做被点名的那一处。日报，不是闸，永远 rc=0。
    ("surface", ["Tools/fleet/surface_status.py"], 60, {0}, True),
    # 九家公司顶层设计的缺项体检（2026-11-03 CEO「梳理每个子公司/实验室的公司级顶层设计」）：
    # 设计文档的风险是写完就烂，这里每轮点名"哪家还没写、哪家标 DONE 却缺哪一问"。rc=2=有缺项。
    ("orgs", ["Tools/fleet/org_design_check.py", "--out", "cph4/fleet/state/org-design.json"], 30, {0, 2}, True),
    # 凌晨记忆归纳总闸（2026-11-03 CEO：每项目记忆都要归纳清理、控膨胀省 token）：
    # 工具自带 02:00-05:00 时间窗，窗外直接跳过；超预算才调 house 闸下沉（快照零删除）。
    ("memory_nightly", ["Tools/fleet/memory_nightly.py"], 900, {0, 2}, True),
    ("showcase", ["Tools/fleet/showcase.py"], 60, {0}, True),
    ("vault", ["Tools/fleet/vault.py", "verify"], 120, {0, 2}, True),
    ("handoff", ["Tools/fleet/handoff.py"], 60, {0}, True),
    ("chief", ["Tools/fleet/chief.py"], 120, {0}, True),
    ("health", ["Tools/fleet/fleet_health.py"], 90, {0}, True),
    ("contingency", ["Tools/fleet/fleet_contingency.py"], 120, {0}, True),
    ("judge", ["Tools/fleet/local_judge.py"], 180, {0}, True),
    ("brain", ["Tools/fleet/brain_service.py"], 240, {0}, True),
    # Business production (2026-10-31 CEO: 本地 AI 赋能业务). Biz drafts one deliverable per
    # job per day; social only drafts replies (never posts); supervisor writes the one-screen
    # verdict. All are maintenance cadence so they cannot delay dispatch.
    ("social", ["Tools/fleet/social_drafts.py"], 180, {0}, True),
    ("biz", ["Tools/fleet/local_ai_business.py", "--due-only"], 600, {0, 1}, True),
    # Output timeliness + direction alignment, computed on git receipts/globs (the only
    # surface the Mac can always see), then the supervisor's one-screen verdict.
    # Unified-memory budget: decide, every cycle, whether a heavier local model may load at
    # all. 32GB is shared with the CEO's apps; the answer must be measured, not assumed.
    ("mem", ["Tools/fleet/mem_gate.py", "--need-gb", "22"], 30, {0}, True),
    # 常驻模型保活（2026-11-03 CEO「内存有余量，能不能加载常驻模型处理轻量需求」）：
    # 实测本机 ollama 同一时刻只能跑一个模型（4B 常驻时 /api/embed 挂死 60s），
    # 所以只保活 resident 一个档；空闲 <25% 时不保活，把内存让给办公与主控脉。
    ("warm", ["Tools/fleet/warm_models.py", "--out", "cph4/fleet/state/warm-models.json"], 120, {0, 1}, True),
    # 压榨度体检（2026-11-03 CEO「所有本地算力都要科学压榨到位，留余量别卡死」）：
    # 逐机算 余量→可再派件数，并戳穿"账上有库存、实际派不出去"的假库存。
    # rc=1=有余量但没活（供给缺口），告警不阻断。
    ("squeeze", ["Tools/fleet/squeeze.py", "--out", "cph4/fleet/state/squeeze.json"], 60, {0, 1}, True),
    # 决策层（2026-11-03 CEO「你科学决策优化 并落地执行」）：只判定不写状态（状态唯一写入口仍是
    # ops_metrics），每轮回答"哪条线该加算力、哪条该停、哪条标了在役但证据在本机看不见"。rc=2=有假绿。
    ("decide", ["Tools/fleet/org_decide.py", "--apply", "--out", "cph4/fleet/state/org-decide.json"],
     60, {0, 2}, True),
    ("autowork", ["Tools/fleet/autowork.py"], 240, {0}, True),
    ("closer", ["Tools/fleet/closer.py"], 60, {0}, True),
    ("deadline", ["Tools/fleet/fleet_deadline.py"], 120, {0}, True),
    ("supervisor", ["Tools/fleet/fleet_supervisor.py"], 60, {0}, True),
    # One page that names the single decision that moves the fleet now, from disk facts
    # only (CEO 2026-11-01: 大脑要及时/准确/创新/严格). Read-only, so it cannot stall.
    ("brain", ["Tools/fleet/brain_brief.py", "--root", ROOT], 60, {0}, True),
    # Aggregator: turns receipts+queue+verdicts into one screen for the CEO.
    ("digest", ["Tools/fleet/digest_agent.py"], 200, {0}, True),
    # Solve leg: requeues failed cards (capped), warns on starvation, and coordinates the
    # only remote channel we have. Serial with the other queue writers.
    ("solver", ["Tools/fleet/master_solver.py"], 120, {0}, True),
    ("line_agents", ["Tools/fleet/line_agents.py"], 120, {0}, True),
]


def log(line: str) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def _one_line(s: str, limit: int = 140) -> str:
    # git errors arrive multi-line; a newline in the log/state breaks every reader.
    return " ".join(str(s or "").split())[:limit]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_state() -> dict:
    try:
        with open(os.path.join(ROOT, STATE_REL.replace("/", os.sep)), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def git(args, timeout=90):
    return subprocess.run(["git", "-C", ROOT] + args, capture_output=True, text=True, timeout=timeout)


# Files the pulse commits itself so a rebase never has to stash them. CODELY.md and the
# memory folder belong here: agents append memory constantly, and while that file stayed
# dirty the pulse skipped every pull and every push ("non-fast-forward" for hours), so the
# plane kept ticking while the fleet could not see it - the 2026-11-02 overnight vacuum.
# Memory writes are append-only facts, safe to snapshot; hand edits under Tools/ are not.
# 2026-11-02: CODELY.md / 记忆目录**不**由主控自动提交。多个班的会话同时在维护记忆，主控再自动签入就必然撞冲突（本轮连撞四次，写出冲突标记）。记忆由写它的会话自己提交，主控只碰派单通道。
STATE_PREFIXES = ("cph4/fleet/", "fleet-console.html")
# 不许挡住 git 同步的路径（运行时配置，不是手写代码）。2026-11-03 实测：这类文件一脏就
# skipped，整夜不同步、落后 635 个提交而报表全绿。判据只能有一处定义——此前 commit_state
# 与 pull_if_clean 各写一份，只修了后者，同步仍照样停摆。
NONBLOCKING = ("cph4/fleet/", "CODELY.md", ".codely-cli/", "fleet-console.html")
# 手写脏件挡住 git 超过这么久就不再算「可以容忍的迟到」，而是主控故障（需人/会话处理）。
GIT_SKIP_ALERT_MIN = 30


def tree_state() -> tuple[list[str], list[str]]:
    """Return (tracked_dirty, untracked). Rebases only ever choke on tracked edits, but
    untracked state files (PULSE.json, brain receipts) should still ride along so the repo
    stays one coherent snapshot."""
    r = git(["status", "--porcelain"])
    tracked, untracked = [], []
    for ln in (r.stdout or "").splitlines():
        if not ln.strip():
            continue
        if ln.startswith("??"):
            untracked.append(ln[3:].strip())
        else:
            tracked.append(ln[3:].strip())
    return tracked, untracked


def last_snapshot_ts() -> float:
    """Wall-clock time of the last commit that touched a cold state file.

    Used to throttle report snapshots. Reading it from git (rather than trusting a field in
    PULSE.json) keeps the throttle honest even after a restart or a reset.
    """
    try:
        r = git(["log", "-1", "--format=%at", "--",
                 "cph4/fleet/dispatcher/PULSE.json"], timeout=20)
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def commit_state(tracked: list[str], untracked: list[str], force=False, last_ts=0.0) -> str:
    """Commit the plane's own state files, with hot/cold separation.

    Structure fix (2026-11-02): git was being used as a 60-second message bus. 44% of all
    commits were state snapshots, 54% of cycles could not sync because some file was dirty,
    and every second scheduler writing the same files produced rebase conflicts. Git now
    carries (a) the dispatch channel and (b) reports - and reports are snapshotted at most
    every STATE_SNAPSHOT_S, because nobody needs a SUPERVISOR.md per minute in history.
    """
    # 记忆是追加型事实：任何会话随时在写 CODELY.md。把它当成"手写代码"会让同步永久停摆
    # （2026-11-02 实测 322/386 轮因此跳过同步）。记忆单独定向提交，不与派单混在一起。
    MEMORY_PATHS = ("CODELY.md", ".codely-cli/memory/")
    mem = [p for p in tracked if p.startswith(MEMORY_PATHS)]
    if mem:
        try:
            git(["add", "--"] + mem)
            git(["commit", "-q", "-m", "memory: autosave [via %s]"
                 % os.environ.get("NODE", "bm-m")])
        except Exception:
            pass
        tracked = [p for p in tracked if p not in mem]
    hand = [p for p in tracked if not p.startswith(NONBLOCKING)]
    if hand:
        return "skipped:dirty(hand-edit %s)" % _one_line(hand[0], 60)
    # Only the dispatch channel is committed from now on. Reports (PULSE/SUPERVISOR/
    # BRAIN/DIGEST...) are gitignored runtime files: they are rewritten every cycle, and a
    # permanently dirty worktree is what blocked every pull (54% of cycles, 2026-11-02).
    todo = [p for p in tracked + untracked
            if p.startswith(STATE_PREFIXES) and any(p.startswith(h) for h in HOT_PREFIXES)]
    if not todo:
        return "ok (no state changes)"
    git(["add", "--"] + todo)
    kind = "dispatch"
    r = git(["commit", "-q", "-m", "pulse: %s snapshot [via bm-m]" % kind])
    return "ok" if r.returncode == 0 else "commit-failed:%s" % _one_line(r.stderr, 80)


GENERATED = ("cph4/fleet/dispatcher/", "cph4/fleet/lanes/", "cph4/fleet/queue-receipts/",
             "cph4/fleet/chief/", "cph4/fleet/social/", "cph4/fleet/plans/",
             "cph4/fleet/state/", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
             "cph4/fleet/PRODUCTION-BACKLOG.jsonl", "cph4/fleet/SHOWCASE.md",
             "cph4/fleet/HANDOFF.md", "cph4/fleet/ri/PROPOSALS.json",
             "cph4/fleet/vault/index.jsonl")


def rebase_generated():
    """分叉收口：只对"生成态文件"取远端版本，代码一律不rebase。

    为什么需要（2026-11-02 实测）：多机同时 push 时 fast-forward 必然失败，
    主控脉报 DIVERGED/rejected，整夜同步停摆而报表还绿——就是"哑巴 8 小时"那类病。
    安全边界：一旦冲突落在 Tools/ 或文档（手写件），立即 abort，绝不替人做选择。
    """
    r = git(["fetch", "--prune", "origin"], timeout=120)
    if r.returncode != 0:
        return "fetch-failed"
    r = git(["rebase", "--autostash", "origin/main"], timeout=180)
    for _ in range(3):
        r = git(["diff", "--name-only", "--diff-filter=U"], timeout=30)
        conflicts = [p for p in (r.stdout or "").split() if p]
        if r.returncode != 0:
            return "status-failed"
        if not conflicts:
            if _rebase_in_progress():
                r2 = git(["-c", "core.editor=true", "rebase", "--continue"], timeout=120)
                if r2.returncode != 0:
                    # rebase 可能已在最后一步自行收口（"no rebase in progress"），
                    # 只要不再处于 rebase 且无冲突，就算成功，不 abort 掉已完成的成果。
                    if not _rebase_in_progress():
                        return "ok"
                    git(["rebase", "--abort"], timeout=60)
                    return "continue-failed"
                continue
            return "ok"
        if any(not p.startswith(GENERATED) for p in conflicts):
            git(["rebase", "--abort"], timeout=60)
            return "hand-edit-conflict:%s" % _one_line(",".join(conflicts), 80)
        for p in conflicts:
            git(["checkout", "--theirs", "--", p], timeout=30)
            git(["add", "--", p], timeout=30)
    git(["rebase", "--abort"], timeout=60)
    return "loop-limit"


def _rebase_in_progress():
    return os.path.isdir(os.path.join(ROOT, ".git", "rebase-merge")) or \
        os.path.isdir(os.path.join(ROOT, ".git", "rebase-apply"))


def pull_if_clean(last_ts=0.0) -> str:
    """Sync without ever letting a dirty worktree block the plane.

    Two hard-won rules (2026-11-02):
      * never rebase - a rebase over a shared worktree stalls and leaves UU conflicts;
      * generated state (everything under cph4/fleet/) is allowed to be autostashed, but a
        dirty HAND EDIT under Tools/ still blocks the pull, because autostash can silently
        swallow someone's uncommitted work.
    """
    tracked, untracked = tree_state()
    try:
        note = commit_state(tracked, untracked, last_ts=last_ts)
    except Exception as e:
        # A bug in state bookkeeping must never stop the plane from dispatching.
        note = "commit-error:%s" % str(e)[:80]
    if note.startswith("skipped"):
        return note
    tracked2, _ = tree_state()
    # 记忆文件是追加型事实，任何会话随时在写；.codely-cli/ 下的 settings/tmp 也是运行时
    # 配置（2026-11-03 实测：.codely-cli/settings.json 一脏就 skipped，整夜不同步、
    # 落后 635 个提交）。把这些算作「手写代码」会让同步永久停摆——那正是哑巴病的根。
    # 只有 Tools/ 等真代码脏才拒绝同步。
    IGNORABLE = NONBLOCKING
    hand = [p for p in tracked2 if not p.startswith(IGNORABLE)]
    if hand:
        return "skipped:dirty(hand-edit %s)" % _one_line(hand[0], 60)
    args = ["pull", "--ff-only", "--no-rebase", "origin", "main"]
    if tracked2:
        # only generated state is dirty: stash/restore around the fast-forward
        args = ["pull", "--ff-only", "--autostash", "origin", "main"]
    try:
        r = git(args, timeout=120)
    except subprocess.TimeoutExpired:
        return "timeout"
    if r.returncode == 0:
        return "ok"
    msg = _one_line(r.stderr or r.stdout, 120)
    # 任何"非快进"类失败都按分叉处理：远端文案随 git 版本变（有时只说
    # "Diverging branches can't be fast-forwarded"），不靠字符串猜，直接试收口。
    if "Not possible to fast-forward" in msg or "diverg" in msg or "fetch first" in msg \
            or "rejected" in msg or "cannot" in msg.lower():
        rb = rebase_generated()
        return "ok(divergence-resolved)" if rb == "ok" else "%s:%s" % (rb, msg)
    return "failed:%s" % msg


def push_if_ahead() -> str:
    """Other nodes read lanes from origin, so an unpushed dispatch is a silent no-op.
    Pushing does not need a clean tree (unlike rebase) - no stash, no loss."""
    try:
        r = git(["rev-list", "--count", "origin/main..HEAD"], timeout=20)
        ahead = int((r.stdout or "0").strip() or 0)
    except Exception:
        return "count-failed"
    if ahead == 0:
        return "up-to-date"
    try:
        r = git(["push", "origin", "HEAD:main"], timeout=90)
        if r.returncode != 0:
            # 多机同推：远端随时可能又前进。反复 fetch+收口+push，最多三次，
            # 每次只允许生成态冲突（rebase_generated），绝不替人改代码。
            for attempt in range(3):
                msg = _one_line(r.stderr, 120)
                if not ("fetch first" in msg or "rejected" in msg or "diverg" in msg):
                    return "failed:%s" % msg
                rb = rebase_generated()
                if rb != "ok":
                    return "rejected+%s" % rb
                r = git(["push", "origin", "HEAD:main"], timeout=90)
                if r.returncode == 0:
                    return "ok+%d(after-sync-%d)" % (ahead, attempt + 1)
            return "rejected(3-attempts):%s" % _one_line(r.stderr, 100)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "ok+%d" % ahead


def align_resident() -> str:
    """Keep exactly one brain resident: the policy model. A stray tag means the fleet is
    quietly running on something nobody configured (2026-11-01: policy qwen3.5:4b, resident
    qwen3:4b-instruct). Unload the stranger; never force-load (first caller loads it)."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "unknown"
    pol = {}
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            pol = json.load(f)
    except Exception:
        pass
    want = ((pol.get("lane_local_llm") or {}).get("model")) or ""
    if not want:
        return "no-policy"
    stray = [m.get("name") or m.get("model") for m in models
             if not (m.get("name") or m.get("model") or "").startswith(want.split(":")[0])]
    for name in stray:
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
        except Exception:
            pass
    return "ok" if not stray else "unloaded:" + ",".join(stray)


def ollama_ok() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


MAX_RESIDENT_GB = 8.0


def evict_heavy_models() -> str:
    """bm-m is the control plane (CEO 2026-10-31): resident models must stay light.
    A 22GB model here starves the 32GB box and swaps the whole machine."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "unknown"
    heavy = [(m.get("name") or m.get("model"), (m.get("size_vram") or 0) / 1e9)
             for m in models if (m.get("size_vram") or 0) / 1e9 > MAX_RESIDENT_GB]
    if not heavy:
        return "ok"
    for name, _ in heavy:
        try:
            body = json.dumps({"model": name, "keep_alive": 0}).encode()
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate", data=body,
                headers={"Content-Type": "application/json"}), timeout=30).read()
        except Exception:
            pass
    return "evicted:" + ",".join(n for n, _ in heavy)


def swap_used_gb() -> float:
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True,
                             timeout=10).stdout
        m = re.search(r"used = ([\d.]+)M", out)
        return round(float(m.group(1)) / 1024, 1) if m else -1.0
    except Exception:
        return -1.0


def pageouts() -> int:
    """Cumulative pageouts. Swap *usage* is sticky - it does not shrink when pressure
    goes away - so judging by the number alone would flag the box red for hours after a
    single spike. What matters is whether pages are still going to disk NOW."""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"Pageouts:\s+(\d+)", out)
        return int(m.group(1)) if m else -1
    except Exception:
        return -1


def relieve_swap() -> str:
    """CEO 2026-11-01: 不要频繁触发硬盘交换. Live swap means pages are already on disk;
    every extra resident model makes it worse. Above 2GB we drop everything except the
    policy seat and say so, instead of quietly paging during the CEO's work."""
    gb = swap_used_gb()
    if gb < 0:
        return "unknown"
    if gb < 2.0:
        return "ok(%.1fGB)" % gb
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "high(%.1fGB) unload-unknown" % gb
    keep = ""
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "MODEL-POLICY.json"), encoding="utf-8-sig") as f:
            pol = json.load(f)
        keep = ((pol.get("lane_local_llm") or {}).get("model")) or ""
    except Exception:
        pass
    dropped = []
    for m in models:
        name = m.get("name") or m.get("model") or ""
        if keep and name.startswith(keep.split(":")[0]):
            continue
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
            dropped.append(name)
        except Exception:
            pass
    return "high(%.1fGB)%s" % (gb, (" unloaded:" + ",".join(dropped)) if dropped else " no-extra-model")


def checks(prev: dict | None = None) -> list[dict]:
    out = []
    sw = relieve_swap()
    po = pageouts()
    prev_po = int((prev or {}).get("swap_pageouts") or 0)
    growing = prev_po > 0 and po > prev_po
    out.append({"name": "swap", "ok": not growing,
                "detail": "live swap %s%s (2GB line unloads extra models; red only while "
                          "pageouts still grow: %s->%s)"
                          % (sw, " GROWING" if growing else "",
                             prev_po or "-", po if po >= 0 else "-")})
    ev = evict_heavy_models()
    out.append({"name": "resident-model-size", "ok": ev in ("ok", "unknown"),
                "detail": "limit %.0fGB (control plane, not a production box): %s"
                          % (MAX_RESIDENT_GB, ev)})
    ok = ollama_ok()
    detail = "http://127.0.0.1:11434/api/tags"
    if not ok:
        # The judgement seat is dead if Ollama is down; repair it before reporting.
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/com.fluxgroup.ollama" % os.getuid()],
                       capture_output=True, text=True)
        for _ in range(20):
            time.sleep(1)
            if ollama_ok():
                ok, detail = True, "restarted by pulse after failing a health check"
                break
    out.append({"name": "ollama", "ok": ok, "detail": detail})

    caf = subprocess.run(["pgrep", "-f", "caffeinate"], capture_output=True, text=True)
    caf_ok = bool(caf.stdout.strip())
    if not caf_ok:
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/com.fluxgroup.caffeinate" % os.getuid()],
                       capture_output=True, text=True)
        time.sleep(2)
        caf = subprocess.run(["pgrep", "-f", "caffeinate"], capture_output=True, text=True)
        caf_ok = bool(caf.stdout.strip())
    out.append({"name": "caffeinate", "ok": caf_ok,
                "detail": "keeps the plane awake on AC power"})
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    for label in ("com.fluxgroup.pulse", "com.fluxgroup.dashboard", "com.fluxgroup.ollama"):
        line = next((ln for ln in r.stdout.splitlines() if ln.endswith(label)), "")
        parts = line.split()
        # A live PID in column 1 already proves the job is up. The status column is the
        # LAST exit code and keeps reporting a SIGTERM/previous failure after a deliberate
        # restart, which used to make a healthy plane look broken (2026-11-01).
        running = len(parts) >= 2 and parts[0].isdigit()
        clean_exit = len(parts) >= 2 and parts[1] == "0"
        out.append({"name": label, "ok": bool(line) and (running or clean_exit),
                    "detail": line.strip()})
    return out


def run_stage(argv, timeout_s):
    t0 = time.time()
    try:
        # 周期件禁云（CEO 2026-11-02）：给每个阶段打标记，router 见到就拒绝升云。
        _env = dict(os.environ, FLUX_AUTOMATION="1")
        # 阶段不都是 python（2026-11-02 实测：backup 传 /bin/bash 被当成
        # "python3 /bin/bash" → SyntaxError，备份阶段每轮红）。按扩展名选解释器。
        first = str(argv[0])
        if first.endswith(".sh"):
            cmd = ["/bin/bash"] + argv
        elif first.endswith(".ps1"):
            cmd = ["pwsh", "-NoProfile", "-File"] + argv
        else:
            cmd = [PY] + argv
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout_s, env=_env)
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        tail = (out.splitlines() or err.splitlines() or [""])[-1][:160]
        return r.returncode, round(time.time() - t0, 1), tail
    except subprocess.TimeoutExpired:
        return 124, round(time.time() - t0, 1), "timeout after %ss" % timeout_s


def main() -> int:
    no_pull = "--no-pull" in sys.argv
    force_slow = "--force-slow" in sys.argv

    lock_fd = open(LOCK, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("%s skip: previous pulse still running" % now())
        return 0

    started = time.time()
    resident_note = align_resident()
    prev = read_state()
    slow_due = force_slow or (time.time() - float(prev.get("slow_ts") or 0) > SLOW_EVERY)
    git_note = "skipped" if no_pull else _one_line(
        pull_if_clean(last_snapshot_ts()), 120)

    stages, alerts, failed = {}, [], []

    def record(name, rc, sec, tail, ok_rc):
        stages[name] = {"rc": rc, "sec": sec, "tail": tail}
        if rc not in ok_rc:
            failed.append(name)
        elif rc != 0:
            alerts.append("%s:%s" % (name, tail[-80:]))

    # Dispatch-critical stages stay serial and ordered; maintenance stages are independent
    # and are run concurrently (2026-10-31: 4B handles 3 parallel calls at ~41 tok/s each
    # with no extra memory, so the slow batch is latency-bound on nothing but serialisation).
    # Queue writers (master, contingency, inventory) must never run concurrently or they
    # clobber each other's rows; everything else is read-mostly and model-bound.
    SLOW_SERIAL = {"census", "inventory", "contingency", "solver", "line_agents"}
    serial = [s for s in STAGES if not s[4]]
    slow_serial = [s for s in STAGES if s[4] and s[0] in SLOW_SERIAL]
    parallel = [s for s in STAGES if s[4] and s[0] not in SLOW_SERIAL]
    # Two pools by resource, not by "more workers = faster":
    #   MODEL_STAGES share Ollama's 3 slots; giving them 6 threads only queues work.
    #   IO stages are pure python (files/git) and are cheap to run wide.
    MODEL_STAGES = {"judge", "brain", "social", "biz", "autowork", "digest"}
    pool_model = ThreadPoolExecutor(max_workers=3)
    pool_io = ThreadPoolExecutor(max_workers=8)
    pool = pool_model
    futs = {}
    if slow_due:
        # Start the read-mostly/model-bound batch BEFORE the dispatch trio: they do not read
        # queue state, so waiting for hb+master first would just serialise the whole cycle.
        futs = {}
        for name, argv, timeout_s, _, _ in parallel:
            target = pool_model if name in MODEL_STAGES else pool_io
            futs[name] = target.submit(run_stage, argv, timeout_s)

    for name, argv, timeout_s, ok_rc, _ in serial:
        rc, sec, tail = run_stage(argv, timeout_s)
        record(name, rc, sec, tail, ok_rc)

    # EARLY HEARTBEAT. The dispatch trio above is what liveness depends on; the maintenance
    # batch below can take minutes (autowork and digest both wait on the 4B). With a single
    # write at the very end, a 4-minute cycle looked like a dead plane from every other node
    # - that is how bm-a spent a whole night believing the master was vacuum and took over.
    try:
        _early = {"ts": now(), "node": NODE, "sec": round(time.time() - started, 1),
                  "git": git_note, "stages": dict(stages),
                  "slow": "running" if slow_due else "deferred", "phase": "dispatch-done"}
        _p = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
        _tmp = "%s.%d.early" % (_p, os.getpid())
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(_early, f, ensure_ascii=False, indent=1)
        os.replace(_tmp, _p)
    except Exception:
        pass

    if slow_due:
        for name, argv, timeout_s, ok_rc, _ in slow_serial:
            rc, sec, tail = run_stage(argv, timeout_s)
            record(name, rc, sec, tail, ok_rc)
        for name, _argv, _t, ok_rc, _ in parallel:
            rc, sec, tail = futs[name].result()
            record(name, rc, sec, tail, ok_rc)
        pool_model.shutdown()
        pool_io.shutdown()
    else:
        pool_model.shutdown()
        pool_io.shutdown()
        for name, _argv, _t, _ok, _ in slow_serial + parallel:
            stages[name] = {"rc": None, "sec": 0,
                            "tail": "deferred (runs every %ds)" % SLOW_EVERY}

    git_push = "skipped" if no_pull else push_if_ahead()
    chk = checks(prev)
    # 同步停摆必须可见（2026-11-02）：commit_state 遇手写脏件就整体跳过 git，
    # 而 PULSE 过去仍报 ok=true —— 与昨夜主控哑巴 8h 同一类「假绿」。
    skip_since = prev.get("git_skip_since")
    if str(git_note).startswith("skipped"):
        skip_since = skip_since or time.time()
        stuck_min = int((time.time() - float(skip_since)) / 60)
        chk.append({"name": "git-sync", "ok": stuck_min < GIT_SKIP_ALERT_MIN,
                    "detail": "%s; stuck %dmin (commit or clean it: uncommitted hand edits "
                              "stop fleet-wide sync)" % (_one_line(git_note, 90), stuck_min)})
    else:
        skip_since = None
        chk.append({"name": "git-sync", "ok": True, "detail": _one_line(git_note, 90)})
    blockers = [c["name"] for c in chk if not c["ok"]] + ["stage:" + n for n in failed]
    pulse = {
        "ts": now(),
        "node": NODE,
        "sec": round(time.time() - started, 1),
        "slow_ts": time.time() if slow_due else float(prev.get("slow_ts") or 0),
        "git": git_note,
        "git_skip_since": skip_since,
        "push": git_push,
        "stages": stages,
        "checks": chk,
        "swap_pageouts": pageouts(),
        "swap_used_gb": swap_used_gb(),
        "alerts": alerts,
        "blockers": blockers,
        "ok": not blockers,
    }
    pulse["resident"] = resident_note
    path = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pulse, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

    # Append-only event stream: every pulse leaves one immutable fact so dispatch/claim/
    # result can be replayed later instead of argued about.
    try:
        import collections
        qp = os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
        cnt = collections.Counter()
        if os.path.exists(qp):
            for ln in open(qp, encoding="utf-8"):
                ln = ln.strip()
                if ln:
                    try:
                        cnt[json.loads(ln).get("state")] += 1
                    except Exception:
                        pass
        ev = {"ts": now(), "node": NODE, "sec": pulse["sec"], "ok": pulse["ok"],
              "git": git_note, "push": git_push, "queue": dict(cnt),
              "blockers": blockers, "alerts": alerts}
        with open(os.path.join(ROOT, "cph4", "fleet", "dispatcher", "events.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


    summary = " ".join("%s=%s/%ss" % (k, v["rc"], v["sec"]) for k, v in stages.items()
                       if v.get("rc") is not None)
    log("%s pulse %s git=%s push=%s blockers=%s alerts=%s | %s"
        % (now(), "OK" if pulse["ok"] else "DEGRADED", git_note, git_push,
           ",".join(blockers) or "-", ",".join(alerts) or "-", summary))
    print("pulse %s git=%s blockers=%s%s"
          % ("OK" if pulse["ok"] else "DEGRADED", git_note,
             ",".join(blockers) or "-", (" alerts:" + ",".join(alerts)) if alerts else ""))
    return 0


if __name__ == "__main__":
    # --loop N = resident mode: launchd KeepAlive then keeps ONE process alive instead of
    # waking a new one every minute (the 12:21 stall was a missed wake-up, not a crash).
    if "--loop" in sys.argv:
        every = int(sys.argv[sys.argv.index("--loop") + 1])
        while True:
            try:
                main()
            except Exception as e:
                log("%s loop-error: %s" % (now(), str(e)[:160]))
            time.sleep(every)
    sys.exit(main())