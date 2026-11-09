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
    ("hb", ["Tools/fleet/fleet_hb.py", "--node", NODE, "--root", ROOT], 60, {0, 2}, False),
    # rc=2 = LOKAL-ONLY（hub 不可达，心跳没发出去）：这是链路告警不是工具坏，
    # 计入 ok_rc 才不会每轮被当成阶段故障（2026-11-07 实测 hub 长期不可达）。
    # 产物回传（2026-11-04）：基础设施动作按节拍跑，不进抢车道的队列排序。
    # 非 Windows 直接跳过；Windows 一天一次，产物落 cph4/fleet/artifacts/<node>/PUSHED.jsonl。
    ("artifact_push", ["Tools/fleet/artifact_push_stage.py"], 3600, {0, 1, 3}, False),
    # 执行器守护（2026-11-06 夜实测）：bm-c 被执行器被本机机制禁回 Disabled 后，机队静默停产，
    # 而主控侧没有角色负责"发现被禁并重新启用"，只能靠人记得 poke。这里每 60s 幂等检查一次：
    # 只处理 roster.enable_tasks 明示的任务、CEO 让路态整机跳过、只调既有 /poke 入口。
    ("executor_guard", ["Tools/fleet/executor_guard.py"], 60, {0, 2}, True),
    # ↑ 降频（2026-11-07 实测 29s/轮）：它守的是"任务被禁"这种缓变状态，
    # 探三台远端 /status 是纯网络开销，每轮跑等于把 20-30s 的节拍交给 tailnet。
    # 改 slow=True（每 5 分钟）后单轮省 ~20s，禁用恢复的最坏延迟仍是 5 分钟。
    # 状态面推送（2026-11-07）：队列/回执在独立 worktree 提交推送，绕开主工作树的手改/分叉。
    # 没有这一腿，卡永远不在 origin 翻面，车道会把同一张卡一遍遍重跑（实测连跑 3 次）。
    # 2026-11-09: state push moved to statesync (60s); this 82s stage removed
    # 报审台账（2026-11-07）：从盘上事实重建 50 款产品的四件套状态，产品级隐私政策缺了就补齐。
    # 一天一次足够；确定性、零 token，产物是可交付的台账而不是报告。
    # submit_ledger 已于 2026-11-07 删除：它调用的 Tools/fleet/submit_ledger_fill.py
    # 全仓不存在（唯一引用就是这里），每轮 rc=2 空转——悬空引用的活例。
    # 真要补隐私台账时先写工具再接线，不许先挂一个不存在的路径。
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
    # 开源风向雷达（2026-11-04 CEO 令「经常去 GitHub 看上升快/潜力大的开源，学习并储备」）：
    # 原 radar-daily-sweep.ps1 只扫不上电，实际是人想起来才跑；这里按日期闸每天跑一次，
    # 产出 cph4/fleet/oss/{STOCKPILE.json,OSS-RADAR.md} 随 git 分发；rc=2 表示本轮有 API 异常。
    ("ossradar", ["Tools/fleet/oss_radar.py", "scan"], 120, {0, 2}, True),
    # 标准六问体检（2026-11-04 CEO 令「标准和方法都要严谨和科学」）：
    # 扫全部 LAW/SPEC/QC 文档，缺"标定依据/负控/能力边界/唯一判据/失效条件/验证记录"就点名。
    # rc=2 是"这份标准还答不出六问之一"，属告警不是工具坏，所以计入 ok_rc。
    ("gate_rigor", ["Tools/gate_rigor_check.py", "--all",
                    "--json", "cph4/fleet/state/gate-rigor.json"], 60, {0, 2}, True),
    # 工序表结构错（悬空依赖/成环/缺 accept）会让整条线静默停摆，rc=2 是"表坏了"的告警。
    ("line_plan", ["Tools/fleet/line_plan.py"], 60, {0, 2}, False),
    # 队列完整性闸（2026-11-04）：实测两张队列里出现过 12+4 行 git 冲突标记，而读队列的每个
    # 脚本都 try/except 跳过坏行 → 主控静默少看 21 张卡、没有一处报错。放在所有读写队列的
    # 阶段之前，快批每轮跑（14 个文件、约 0.1s）。rc=2 = 账本已脏，先修文件再派单。
    ("qcheck", ["Tools/fleet/queue_integrity.py", "--reconcile"], 60, {0, 2}, False),
    ("night_fill", ["Tools/fleet/night_fill.py", "--target", "6"], 90, {0}, False),
    # 银行自动补料（2026-11-03，曾被并行会话的 STAGES 整表重写静默丢掉一次——重加并留痕）：
    # workgen 只认 bank 里现成的卡片，bank 空了机器就空转；本阶段按机器能力补体检活，
    # 并销掉"产物已在盘却仍标 pending"的僵尸条目。必须在 workgen 之前。
    ("bank_autofill", ["Tools/fleet/bank_autofill.py", "--root", ROOT], 60, {0}, False),
    ("workgen", ["Tools/fleet/workgen.py", "--root", ROOT], 180, {0}, False),
    ("promote_ready", ["Tools/fleet/promote_ready.py"], 60, {0}, False),
    ("master", ["Tools/fleet/master_agent.py", "--node", NODE, "--root", ROOT], 240, {0}, False),
    ("lane", ["Tools/fleet/lane_agent.py", "--node", NODE, "--root", ROOT, "--no-fetch"], 120, {0}, False),
    # 执行者复活（2026-11-08）：三台 Windows 的 /status 全部 wakes=[]，FleetLink 活着
    # 但没有任何任务被唤醒 -> 队列有卡也跑不动，一下午 DONE 只前进 9 张。巡检以前只报
    # 不修，靠会话发现再让 CEO 转命令给操作员。这里改成脉自己动手：
    # 唤醒失败就 poke 显式启用（tasks 取 roster.enable_tasks 白名单，reason 含 enable-tasks），
    # 拉取报 :fail（分叉）就发一张自包含收口卡。rc=1 表示本轮做了动作（不是失败）。
    ("executor_revive", ["Tools/fleet/executor_revive.py", "--apply"], 120, {0, 1, 2}, False),
    # 验收（CEO 2026-11-05「监督、派单、验收」）：DONE 只代表执行结束，不代表做对——
    # 盘上那件东西可能是 0 字节、坏 JSON、BLOCKED 说明，或上一次留下的旧件。
    # 2026-11-07 校验器报 W-STAGE 才补的接线：表里登记了这条，脉里从来没跑（纸面验收）。
    # 只报告不改卡状态（改状态是 closer 的权）。rc 恒 0，缺口看重不重 rc。
    ("verify_done", ["Tools/fleet/verify_done.py", "--hours", "24"], 180, {0}, False),
    # inventory exits 1 to say "a lane is STARVED"; that is an alert, not a tool failure.
    ("inventory", ["Tools/fleet/inventory_guard.py"], 120, {0, 1}, True),
    # 事实层（2026-11-02 FLUX OS v2）：先把磁盘事实与结构断言跑一遍，再谈派单。
    # census 写 state/lines.json（I14 与 metrics 都依赖它），因此放在慢批串行最前。
    ("census", ["Tools/fleet/census.py"], 180, {0}, True),
    # 指挥一屏（CEO 2026-11-06「常驻本地模型列好高频自动化任务，代替我做各个指挥工作」）：
    # 节奏表=COMMAND-CADENCE-v1.json，本阶段只做规则汇总（零 token），产出 COMMAND-BOARD.md。
    # 必须排在 census 之后：它读 state/lines.json 的产出年龄，绝不自己算产出。
    ("commander", ["Tools/fleet/commander.py"], 180, {0}, False),
    # 以下六阶段按 COMMAND-CADENCE-v2.json 补接线（2026-11-06 校验器报 W-STAGE 才补的）：
    # 之前表里写了、脉里没跑，等于纸上自动化。每条的周期与表一致，改表必须同步改这里，
    # cadence.py --check 会把不一致报出来（不许两处各写一套还互相以为在跑）。
    # 卡契约 lint：cmd 里的 --out 必须等于 deliverable；缺 accept/deliverable 点名。
    ("card_contract_check", ["Tools/fleet/card_contract_check.py"], 180, {0, 1, 2}, True),
    # 自改：码龄不重载/空壳卡/缺依赖，本机自己修（回执固定路径，主控按盘验）。
    ("self_improve", ["Tools/fleet/self_improve.py", "--node", NODE, "--apply",
                      "--out", "cph4/fleet/queue-receipts/self-improve-%s-latest.json" % NODE],
     300, {0, 1}, False),
    # 分叉诊断：只报 ahead/behind 与真实文件数，绝不自动 reset（含真产物的分叉必须人判）。
    ("fork_close", ["Tools/fleet/fork_close.py"], 600, {0, 1}, True),
    # 常驻工具完整性：launchd/任务指向的脚本没了当场报警（实锚：load_watch.py 已删仍被调）。
    ("tool_watch", ["Tools/fleet/tool_watch.py"], 600, {0, 1, 2}, True),
    # 算力占用归因：占着 CPU/GPU 却没有产出，--seconds 压低避免与生产抢 IO。
    ("useful_load", ["Tools/fleet/useful_load.py", "--seconds", "8"], 3600, {0, 1}, True),
    # 每日只交 CEO 三件（规则排优先级，模型只写一句）。
    ("ceo_three", ["Tools/fleet/ceo_three.py"], 86400, {0}, False),
    # 需求总账核验（CEO 2026-11-07「纵览所有命令，把自动化做到极致」）：31 条需求
    # 逐条机检；rc=1 表示有缺口（告警，不是工具故障），缺口可 --dispatch 变卡。
    ("demand_audit", ["Tools/fleet/demand_audit.py"], 86400, {0, 1}, True),
    # 带做器（CEO 2026-11-07「带我去做，高频科学的频次」）：六源合一打分，30 分钟重算，
    # 只有换题才更新正文（同题标「仍等你」），避免高频=刷屏。产出 CEO-NEXT.md。
    ("ceo_pilot", ["Tools/fleet/ceo_pilot.py"], 1800, {0}, False),
    # 情报审查（2026-11-07）：雷达自标「星数超 10 万需人工核实」却没人核 = 假情报源头。
    # 每日把越界条目拿去 GitHub API 对一遍，差异超 10% 判 STALE；无网一律 UNVERIFIED，不判假。
    ("fact_check", ["Tools/fleet/fact_check.py"], 86400, {0, 1}, True),
    # 模型排班体检（2026-11-07 实测三模型 10.4GB 事故后立）：核对驻留是否超预算、
    # 矩阵里的模型名是否都在单一源、P0 是否有降级路径。rc=1 是告警不是故障。
    ("model_plan", ["Tools/fleet/model_plan.py"], 3600, {0, 1}, True),
    # 根因复验（CEO 2026-11-07「倒查所有问题，根本上统筹解决」）：6 条根因每日复验，
    # 判「已修」只认这台机器的输出；任一条复发就点名，不许用文档声明代替。
    ("root_cause", ["Tools/fleet/root_cause_audit.py"], 86400, {0, 1}, True),
    # 运营度量（2026-11-07 维度盘点后补）：错误预算/燃尽、产物质量 rubric、成本归因。
    # 过去只有二元绿，看不出「四条服务都在超支、同步 0%」。rc=1 表示有服务超预算。
    ("ops_metrics", ["Tools/fleet/ops_metrics.py"], 3600, {0, 1}, True),
    # 复盘席（CEO 2026-11-07「也要复盘总结并推广经验的智能体」）：从失败/撤销簇里
    # 抽经验，并核验每条经验的落点是否真的存在。没有落点的不算已推广（rc=1 挂着），
    # 声称有落点却核验不到=假绿（rc=2）。12 小时一次，不占节拍。
    ("retro", ["Tools/fleet/retro.py", "--apply"], 43200, {0, 1, 2}, True),
    # 回归用例集（2026-11-07）：把踩过的每个坑变成断言，改码后自动跑，防越修越乱。
    ("regression", ["Tools/fleet/regression.py"], 21600, {0}, True),
    # 安全与供应链台账：凭据泄漏/越权动作/许可传染/素材授权，红线变每日计数。
    ("security", ["Tools/fleet/security_ledger.py"], 86400, {0}, True),
    # 灾难恢复体检：备份新鲜度/关键文件在不在 git/接管六步，RTO 30min·RPO 24h。
    ("dr_check", ["Tools/fleet/dr_check.py"], 86400, {0}, True),
    # 三层产出审核 + 入档入库（CEO 2026-11-07）：DONE 只表示执行结束，不代表合格。
    ("review_artifacts", ["Tools/fleet/artifact_review.py", "--limit", "40", "--apply"], 21600, {0, 1}, True),
    # 有序巡查（CEO 2026-11-07「智能体巡查排序好，指挥好机队各个业务和自动化开展」）：
    # 把七八个报告面归并成一条按"断链→供给→执行→质量→方向"排序的清单，每条带责任人。
    # 10 分钟一次，纯规则零 token。
    ("patrol", ["Tools/fleet/patrol.py"], 180, {0}, False),
    # 验收监督（CEO 2026-11-08「验收只看产物和质量，流程文档不算数」）：脉里必须有这一环，
    # 否则"今天到底有没有产出"没人问；rc=1=窗口内零可验收产物，是真红不是噪音。
    ("acceptance", ["Tools/fleet/acceptance.py", "--window-hours", "24"], 300, {0, 1}, False),
    # 机器面监督：谁在线但不干活、谁拉不动仓库、谁名下有死卡。只看回执与 /status，不做推断。
    ("fleet_status", ["Tools/fleet/fleet_status.py"], 120, {0, 1}, False),
    # 堵/坏/卡点闭环（CEO 2026-11-08「堵点坏点卡点都要有相应的循环策略去检测和解决」）：
    # 八类问题各带判据/解法/复查周期/升级轮次；能自动解的当场解（补供给、修卡字段、
    # 补推同步、重跑超期阶段、派自证卡），解不了的按轮次升级。表=BLOCKER-TAXONOMY-v1.json。
    # 走快批（每轮都跑），由分类表里每类自己的 every_s 节流：否则 120s 的同步类
    # 被慢批 300s 卡住，频率表就是假承诺。没到期的类会直接跳过，成本可忽略。
    ("blocker_loop", ["Tools/fleet/blocker_loop.py", "--apply"], 240, {0, 1, 2}, False),

    # 常驻模型的机队决策席（CEO 2026-11-08「常驻大模型负责每天高频率管理机队和派发任务」）：
    # 规则算事实与候选，4B 只负责在候选里挑一件并给一句理由，动作由代码白名单执行。
    ("fleet_brain", ["Tools/fleet/fleet_brain.py", "--apply"], 300, {0}, False),
    # 回执名不匹配导致的永久 UNVERIFIED（实测堵死 4 条线）：按词干匹配回执并收口。
    # 宁可不判也不假绿——歧义/无证据一律交人。
    ("receipt_match", ["Tools/fleet/receipt_match.py", "--apply"], 180, {0}, False),
    # 内存护栏（CEO 2026-11-07「把本地算力完全赋能，但最好不要 swap 浪费硬盘」）：
    # 判据是换页速率不是 swap 总量；四档常驻 14.2GB 时实测 ≈1.8 页/分。rc=1 表示正在
    # 拿硬盘当内存用（真抖动），而不是"swap 账上还有历史占用"。
    ("mem_guard", ["Tools/fleet/mem_guard.py", "--window", "30"], 120, {0, 1}, True),
    # 分线质量席（CEO 2026-11-07「给各个业务和研发提升质量的智能体，要先进可靠」）：
    # 五条线（影片/图像/构建/回测/文档）21 条判据，每条自带反例、--selftest 自证闸有效，
    # 任一强制项不过即整体 FAIL（不许加权分把硬伤放过去）。4 小时一次，rc=2 表示闸失效。
    ("quality_agents", ["Tools/fleet/quality_agents.py", "--scan"], 300, {0, 2}, True),
    # 仓库分层体检（CEO 2026-11-07「git 也要好好分类分层」）：管住新文件落在哪一层，
    # 不搬旧文件（被脉/卡/文档引用，批量 mv 会断链）。rc=1 是告警。
    ("repo_layers", ["Tools/fleet/repo_layers.py"], 86400, {0, 1}, True),
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
    # 待裁件默认推进（2026-11-04）：CEO/EXTERNAL 卡点过去只写「等」，这里给问句+准备件+到期，
    # 方向类 48h 未裁按默认继续，只有对外/花钱/不可逆留给人。rc=2=有到期未裁的对外件。
    ("ceo_queue", ["Tools/fleet/ceo_default.py"], 30, {0, 2}, True),
    # 机队互报（CEO 2026-11-04：信息与产出及时互通，不要孤岛）。
    # 本机发今日简报（很小的 json 进 git），再把全队简报合成一屏 SYNC-BOARD.md。
    ("bulletin", ["Tools/fleet/bulletin.py", "--post", "--aggregate", "--node", NODE], 120, {0}, True),
    # 跨机依赖（2026-11-04）：SYNC-BOARD 缺「谁等谁的产物」列，这里把在办卡的 requires 与
    # 全队列 deliverable 对上，画出等待边并报环。rc=2=有等待环（结构病，必须改卡）。
    ("wait_map", ["Tools/fleet/wait_map.py"], 60, {0, 2}, True),
    # 供给目标（2026-11-04）：wait_map 只画"谁等谁"，这一站回答"等的那一头谁该产"。
    # rc=1 表示仍有产物无人生产（供给缺口告警，不是工具坏）。
    ("supply_target", ["Tools/fleet/supply_target.py"], 60, {0, 1}, True),
    # 集团雷达（CEO 2026-11-03 令：实验室与各研究席高频合理地扫网）。
    # 频率写在 Tools/fleet/radar.py 的 SOURCES 里（GitHub 20h / arXiv 150h），未到点自跳过；
    # 源挂了记 BLOCKED 不编候选（实测 HF 直连不通）。
    ("radar", ["Tools/fleet/radar.py"], 180, {0}, True),
    # 前瞻：每条线剩余弹药与卡点（CEO 2026-11-03「不许等机队没活了」）。
    # 只报告不阻断：runway<2 天会打 ALERT 行，告警由人看或后续接排队。
    ("forecast", ["Tools/fleet/forecast.py"], 60, {0, 2}, True),
    # 云端日预算闸（CEO 2026-11-05「按日预算放开，硬上限 ¥100/天」）：每轮报余额；
    # rc=1 = 今天已用完（告警不是工具坏，计入 ok_rc）。任何上云调用先问这一站。
    ("budget", ["Tools/fleet/cloud_budget.py", "check"], 30, {0, 1}, True),
    ("gate", ["Tools/fleet/gate_report.py"], 180, {0}, True),
    ("checkups", ["Tools/fleet/checkups.py"], 180, {0, 2}, True),
    # 2026-11-07 删掉重复的 ("metrics", ops_metrics.py, {0})：ops_metrics 上线后这里没撤，
    # 同一个工具每轮跑两遍，而且两处契约相反（此处只许 rc=0，那边许 {0,1}）——
    # 于是 ops_metrics 每轮报的「燃尽告警」被这条旧登记判成故障，blockers 永久亮 stage:metrics。
    # 事件日志（2026-11-03 S1 影子期）：先把本机 outbox 发到 JetStream，再拉本机未消费事件。
    # 走快批（每轮都跑）而不是慢批：慢批 300 秒节流会让事件积压成"五分钟前的事实"。
    # 只写不读——生产链路一次也不等它；rc=2 只表示总线不通，不影响派单。
    ("eventlog", ["Tools/fleet/flux_eventlog.py", "tick", "--node", NODE], 90, {0, 2}, False),
    # rc=2 = hub-unreachable（事件留在 outbox 待补发）：链路告警，不是阶段故障。
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
    # 资产打标（2026-11-04 移动盘到位后）：529 张素材在盘、实测 6.9s/张，是本机最实在的
    # GPU 活。慢批一轮 10 张（约 1 分钟），既压得动算力又不占满内存。rc=3=模型或目录不在。
    # 本机槽位农场（2026-11-04 CEO「利用好 32G 统一内存与 GPU/CPU」）：按实测内存余额开槽，
    # 模型槽/ASR 槽/编码槽可同时开；批量按预算定，避免被 kill 成"超时假故障"。
    # rc=1=有槽位软告警（质量门判次），rc=3=槽位表缺失。旧的 caption 单站已被它取代。
    ("mac_farm", ["Tools/fleet/mac_farm.py", "--budget", "240"], 420, {0, 1, 3}, True),
    ("asset_prompts", ["Tools/fleet/asset_prompts.py", "--limit", "10"], 600, {0, 1, 3}, True),
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
    # rc=3 = 资产卷未挂载（例如移动硬盘没插）：这是"不可判定"，不是"资产丢了"。
    # 旧口径把 651 条全报丢失，一次假红就没人再信这条。
    ("vault", ["Tools/fleet/vault.py", "verify"], 120, {0, 2, 3}, True),
    # 阶段自证（CEO 2026-11-07「我感觉还是不放心」）：拿 stage-last.json 对节奏表周期，
    # 逐个阶段判"最后一次真跑"是否超期。专治"登记在表、脉里不跑"这个盲区
    # （ops_metrics 被重复登记、verify_done 从未接线都是长在这个盲区里的）。
    ("stage_liveness", ["Tools/fleet/stage_liveness.py"], 3600, {0, 1, 2}, True),
    # 资产可达性（2026-11-04）：台账条数≠可达条数。盘不在就判 UNREACHABLE，
    # 禁止任何"已归集/已备份"的说法。rc=2=账面有、可达 0。
    ("asset_reach", ["Tools/fleet/asset_reach.py"], 60, {0, 2}, True),
    # DONE 卡交付物审计（2026-11-04）：回执≠产出。只把「仓内相对路径且文件真不在」的卡
    # 降级 UNVERIFIED；跨机/被 gitignore 的独立仓产物不改状态（主控本来就看不见）。
    ("done_audit", ["Tools/fleet/done_audit.py", "--apply"], 60, {0, 2}, True),
    ("handoff", ["Tools/fleet/handoff.py"], 60, {0}, True),
    ("chief", ["Tools/fleet/chief.py"], 120, {0}, True),
    ("health", ["Tools/fleet/fleet_health.py"], 90, {0}, True),
    ("contingency", ["Tools/fleet/fleet_contingency.py"], 120, {0}, True),
    # 裁决收敛环（2026-11-04）：local_judge 只收敛 OPEN 行，4B 判不了的 ESCALATED 之前无人处理
    # （实测 5 件挂 12–36h）。这里先按盘上事实结案，再让 local_judge 处理新题。rc=2=仍有待 CEO 项。
    # 本地模型任务层（2026-11-04 CEO：本地模型能力要持续赋能机队）：慢批每轮消化最多 3 件
    # 待办（分类/摘要/打分/抽取），一次一件、串行，避免和 judge 抢同一个模型的槽位。
    # rc=2=本批有失败（模型退化或题型不适配），rc=3=模型不可达。
    ("local_tasks", ["Tools/fleet/local_task.py", "drain", "--limit", "3", "--seed",
                     "--adaptive"], 300, {0, 2, 3}, True),
    ("decision_close", ["Tools/fleet/decision_close.py"], 60, {0, 2}, True),
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
    # 主控决策大脑（CEO 2026-11-05：规则大脑 + 四线四行）。它不是又一个报告：
    # 每轮给出四条 P0 线各自唯一的动作，并在 --act 下真的触发 closer/night_plan/workgen。
    # 放在 closer 之后，看到的是本轮的干净事实。
    ("master_loop", ["Tools/fleet/master_loop.py", "--act"], 180, {0}, True),
    # 分层决策路由（CEO 2026-11-05「不是每个都要到你这里决策」）：按 decision-chain §0/§8
    # 给待决事项定级 L0-L3/CEO，各层带时限与兜底；只有真保留域才上屏给 CEO。
    ("decision_router", ["Tools/fleet/decision_router.py"], 60, {0}, True),
    # 验收（CEO 2026-11-05「常驻智能体要监督/派单/验收」）：DONE≠做对。
    # 对近 24h 的 DONE 卡做机器验收（空文件/坏 JSON/0 时长/拒答文稿）。
    ("deadline", ["Tools/fleet/fleet_deadline.py"], 120, {0}, True),
    ("supervisor", ["Tools/fleet/fleet_supervisor.py"], 60, {0}, True),
    # One page that names the single decision that moves the fleet now, from disk facts
    # only (CEO 2026-11-01: 大脑要及时/准确/创新/严格). Read-only, so it cannot stall.
    # 2026-11-07 改名：这条与 brain_service 同名 "brain"，后一条把前一条的执行记录覆盖掉
    # （stages 是 dict），于是 brain_service 跑没跑、成没成在盘上都查不到。
    ("brain_brief", ["Tools/fleet/brain_brief.py", "--root", ROOT], 60, {0}, True),
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
        # 假脏归位（2026-11-07 实测解死锁）：HEAD 落后于 origin 时，工作区文件内容
        # 明明等于 origin，`git status` 仍报 M，于是脉把它当"手写改动"阻塞同步，
        # 而真正的手写改动一个都没有——同步整夜停摆、push 连续被拒，报表全绿。
        # 判据改成内容比较：与 origin 相同就 checkout 归位（零损失），不同才算手改。
        real_hand = []
        for p in hand:
            # 三个方向必须分开（2026-11-07 实测两次都栽在这里）：
            #   本地==origin        -> 假脏，放行走 autostash
            #   本地缺 origin 的内容 -> 只是落后，直接对齐 origin（安全）
            #   本地有 origin 没有的 -> 真手改，阻塞同步（绝不能 autostash，会藏起来）
            r = git(["diff", "--numstat", "origin/main", "--", p], timeout=30)
            parts = (r.stdout or "").split()
            added = int(parts[0]) if parts and parts[0].isdigit() else 0
            if added > 0:
                real_hand.append(p)
            elif parts:
                git(["checkout", "origin/main", "--", p], timeout=30)
        hand = real_hand
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


def _abort_stuck_rebase():
    """卡在中间的 rebase 是静默毒药，必须先清掉再谈同步。

    2026-11-04 实测：仓库卡在 98 步交互式 rebase 的中段（1 步已 pick、5 个文件 UU），
    工作区带着 <<<<<<< 冲突标记，而读队列的每个脚本都 try/except 跳过坏行 →
    队列少 21 行卡片、没有任何一处报错。脉冲自己还每轮试 rebase --continue 失败。
    """
    if not _rebase_in_progress():
        return False
    # 2026-11-05 事故（必须防）：rebase --abort 会把分支指回 rebase 开始前的 ref，
    # 于是 rebase 期间刚做的提交不在任何分支上 = 静默丢失。实测一次 abort 让主控当天
    # 6 个功能提交（AUTONOMY-CONFIG/master_loop/decision_router 等）全部掉链。
    # 规则：abort 之前先把 HEAD 钉到 rescue ref，丢分支指向可以，丢对象不行。
    try:
        head = (git(["rev-parse", "HEAD"], timeout=30).stdout or "").strip()
        if head:
            ref = "rescue/rebase-abort-%s" % time.strftime("%Y%m%dT%H%M%S")
            git(["branch", "-f", ref, head], timeout=60)
            log("rescue: HEAD %s -> %s (abort 前留底)" % (head[:8], ref))
    except Exception as e:
        log("rescue-failed: %s" % str(e)[:80])
    git(["rebase", "--abort"], timeout=90)
    return True


def _local_only_open_cards(paths):
    """合并前把本机独有的 OPEN/READY 卡留底，避免"取远端版本"把它们一起抹掉。"""
    keep = []
    for rel in paths:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("<<<<<<<") \
                            or line.startswith("=======") or line.startswith(">>>>>>>"):
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(r, dict) and r.get("id") \
                            and str(r.get("state") or "").upper() in ("OPEN", "READY"):
                        keep.append((rel, r))
        except FileNotFoundError:
            pass
    return keep


def _restore_local_only_cards(keep):
    """合并后把远端没有的本机卡补回（只补 OPEN/READY，绝不复活 CANCELLED/DONE）。"""
    restored = 0
    by_rel = {}
    for rel, r in keep:
        by_rel.setdefault(rel, []).append(r)
    for rel, rows in by_rel.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        have = set()
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        have.add(json.loads(line).get("id"))
                    except Exception:
                        continue
        except FileNotFoundError:
            continue
        add = [r for r in rows if r.get("id") not in have]
        if not add:
            continue
        with open(p, "a", encoding="utf-8") as f:
            for r in add:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        restored += len(add)
    return restored


def rebase_generated():
    """分叉收口：只对"生成态文件"取远端版本，代码一律不动。

    为什么需要（2026-11-02 实测）：多机同时 push 时 fast-forward 必然失败，
    主控脉报 DIVERGED/rejected，整夜同步停摆而报表还绿——就是"哑巴 8 小时"那类病。
    安全边界：一旦冲突落在 Tools/ 或文档（手写件），立即 abort，绝不替人做选择。

    2026-11-04 改（rebase → merge）：旧实现 rebase --autostash origin/main 会把本机
    几十个 pulse 快照逐个重放，每个都撞同一批队列/lane 冲突，于是 continue-failed →
    abort → 下一轮再来；实测把仓库卡在 98 步 rebase 里，工作区留冲突标记、队列被静默
    吞行。merge 不重写历史、不必逐个重放，同样能实现"生成态取远端"的口径。
    """
    stuck = _abort_stuck_rebase()
    if stuck:
        log("[git] aborted a stuck rebase before merging (2026-11-04 fix)")
    # 先把自己这半边的生成态快照提交，脏工作区不许挡住 merge
    tracked, untracked = tree_state()
    if tracked or untracked:
        commit_state(tracked, untracked)
    r = git(["fetch", "--prune", "origin"], timeout=120)
    if r.returncode != 0:
        return "fetch-failed"
    ahead = git(["rev-list", "--count", "origin/main..HEAD"], timeout=30)
    behind = git(["rev-list", "--count", "HEAD..origin/main"], timeout=30)
    if (ahead.stdout or "0").strip() in ("", "0"):
        return "ok (no local commits)"

    keep = _local_only_open_cards(
        ["cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl"])
    r = git(["merge", "--no-edit", "-m",
             "pulse: merge origin (generated files take remote)", "origin/main"], timeout=180)
    for _ in range(3):
        r = git(["diff", "--name-only", "--diff-filter=U"], timeout=30)
        if r.returncode != 0:
            git(["merge", "--abort"], timeout=60)
            return "status-failed"
        conflicts = [p for p in (r.stdout or "").split() if p]
        if not conflicts:
            break
        if any(not p.startswith(GENERATED) for p in conflicts):
            git(["merge", "--abort"], timeout=60)
            return "hand-edit-conflict:%s" % _one_line(",".join(conflicts), 80)
        for p in conflicts:
            git(["checkout", "--theirs", "--", p], timeout=30)
            # 2026-11-04 poison guard: a side that still carries conflict markers must
            # never be staged (five consecutive poisoned lanes shipped on 2026-11-04).
            try:
                with open(os.path.join(ROOT, p), encoding="utf-8", errors="replace") as _fh:
                    _t = _fh.read()
                if "<<<<<<<" in _t and ">>>>>>>" in _t:
                    log("POISON-GUARD: %s still carries conflict markers - abort rebase" % p)
                    git(["rebase", "--abort"], timeout=60)
                    return "poison-guard:%s" % p
            except Exception:
                pass
            git(["add", "--", p], timeout=30)
    else:
        git(["merge", "--abort"], timeout=60)
        return "loop-limit"
    if _rebase_in_progress():
        git(["merge", "--abort"], timeout=60)
        return "still-in-rebase"
    r = git(["diff", "--name-only", "--diff-filter=U"], timeout=30)
    if (r.stdout or "").strip():
        git(["merge", "--abort"], timeout=60)
        return "conflicts-left"
    if git(["rev-parse", "-q", "--verify", "MERGE_HEAD"], timeout=20).returncode == 0:
        r = git(["commit", "-q", "--no-edit"], timeout=90)
        if r.returncode != 0:
            git(["merge", "--abort"], timeout=60)
            return "merge-commit-failed"
    n = _restore_local_only_cards(keep)
    if n:
        git(["add", "--", "cph4/fleet/PRODUCTION-QUEUE.jsonl",
             "cph4/fleet/PRODUCTION-BACKLOG.jsonl"], timeout=30)
        git(["commit", "-q", "-m", "pulse: restore %d local-only cards after merge" % n],
            timeout=60)
        log("[git] restored %d local-only OPEN/READY cards after merge" % n)
    return "ok"


def _rebase_in_progress():
    return os.path.isdir(os.path.join(ROOT, ".git", "rebase-merge")) or \
        os.path.isdir(os.path.join(ROOT, ".git", "rebase-apply"))



GIT_HEALTH = os.path.join(ROOT, "cph4", "fleet", "state", "git-health.json")


def _git_health():
    try:
        return json.load(open(GIT_HEALTH, encoding="utf-8"))
    except Exception:
        return {}


def _git_quarantined():
    """连续失败后暂停 pull 30 分钟：宁可暂时不同步，也不让控制面每拍卡 2 分钟。"""
    h = _git_health()
    return time.time() < float(h.get("until") or 0)


def _git_fail(note):
    h = _git_health()
    now = time.time()
    fails = [x for x in (h.get("fails") or []) if now - x < 1800] + [now]
    if len(fails) >= 3:
        h["until"] = now + 1800
        h["why"] = note[:120]
        log("[git] quarantine 30min after %d failures: %s" % (len(fails), note[:80]))
    h["fails"] = fails
    h["ts"] = now
    try:
        os.makedirs(os.path.dirname(GIT_HEALTH), exist_ok=True)
        json.dump(h, open(GIT_HEALTH, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass


def _git_ok():
    h = _git_health()
    if h.get("fails") or h.get("until"):
        try:
            json.dump({"fails": [], "ts": time.time()},
                      open(GIT_HEALTH, "w", encoding="utf-8"))
        except Exception:
            pass


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
    # 大小写敏感曾让这段从未触发：git 报的是 "Diverging branches"，而这里比的是小写
    # "diverg"。必须先 lower 再比，否则分叉分支形同不存在（2026-11-07 实测）。
    if "not possible to fast-forward" in msg.lower() or "diverg" in msg.lower() \
            or "fetch first" in msg.lower() or "rejected" in msg.lower() \
            or "cannot" in msg.lower():
        # 分叉处理（2026-11-07 修死锁）：本脉每轮都提交自己的产物，所以永远 ahead>0，
        # 纯 ff-only 必然失败 → 永远拉不到远端。rebase 被 C-20261104 禁止，
        # 故改用「受控 merge」：--no-commit 先试，冲突立刻 abort 并如实报告，
        # 绝不留下冲突标记（那会让队列静默少看卡）。
        m = git(["merge", "--no-edit", "--no-commit", "origin/main"], timeout=120)
        if m.returncode != 0 and "would be overwritten" in (m.stderr or "").lower():
            # 脉自己刚写的生成态挡住了 merge。这些文件可重生成，先对齐 origin 再试一次；
            # 只处理 merge 点名的路径，绝不整树 checkout。
            import re as _re
            names = _re.findall(r"^\s+(\S+)\s*$", m.stderr or "", _re.M)
            if names:
                git(["checkout", "origin/main", "--"] + names, timeout=60)
                m = git(["merge", "--no-edit", "--no-commit", "origin/main"], timeout=120)
        if m.returncode == 0:
            git(["commit", "-q", "-m", "pulse: merge origin/main (divergence)"], timeout=60)
            return "ok(merged-divergence)"
        git(["merge", "--abort"], timeout=60)
        return "merge-conflict:%s" % _one_line(m.stderr or m.stdout, 100)
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
    # 精确白名单，不用同族前缀（2026-11-07 实测事故）：三个模型都叫 qwen3*，
    # 以 "qwen3" 前缀判同类 → 互相视为同类 → 一个都不卸，10.4GB 常驻。
    keep = {want}
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                  encoding="utf-8") as f:
            lp = (json.load(f).get("duties") or {})
        # 常驻白名单从策略读（2026-11-07 实锚）：早先这里手写三档，加了 big(8B) 却没加进
        # 白名单，于是每轮把刚加载的大模型卸掉 → 冷加载 20-40s、反复抖。名单必须跟着
        # budget.resident_set 走，不许再手写。
        _wl = []
        try:
            with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                      encoding="utf-8") as _lf:
                _wl = ((json.load(_lf).get("budget") or {}).get("resident_set") or [])
        except Exception:
            _wl = []
        for seat in (_wl or ["big", "resident", "embedding"]):
            m = ((lp.get(seat) or {}).get("model") or "").strip()
            if m:
                keep.add(m)
    except Exception:
        pass
    stray = [m.get("name") or m.get("model") for m in models
             if (m.get("name") or m.get("model")) not in keep]
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


MAX_RESIDENT_GB = 12.0   # 单模型上限：8B@8192 实测 5.9GB；12GB 容得下 14B 级


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
    """按**换页速率**判，不按 swap 账上总量。

    2026-11-07 修正（CEO「不要把 swap 浪费硬盘，但算力要用满」）：旧实现只要
    swap used > 2GB 就把除主力档以外全部卸掉。而 macOS 的 swap 用过就留账、不回落
    （本机长期 3.2GB），于是每一轮都在卸 8B/1.7B → 冷加载 20-40s，算力反而没用满。
    真正伤盘的是"现在还在往盘上写"，所以这里采两次 pageouts 求速率；超阈值才动手，
    动手顺序按矩阵 swap.order（先卸快车道，大档最后）。
    """
    p0 = pageouts()
    if p0 < 0:
        return "unknown"
    time.sleep(5)
    p1 = pageouts()
    per_min = (p1 - p0) * 12          # 5 秒窗口外推成每分钟
    limit = 120
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "MEM-GUARD-v1.json"),
                  encoding="utf-8") as f:
            limit = int((json.load(f) or {}).get("pageouts_max_per_min") or 120)
    except Exception:
        pass
    if per_min <= limit:
        return "ok(%.0f页/分, swap账 %.1fGB)" % (per_min, swap_used_gb())
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            models = json.load(r).get("models", [])
    except Exception:
        return "thrash(%.0f页/分) unload-unknown" % per_min
    # 只卸最容易再起来的档（快车道），大档留到最后
    keep_names = set()
    try:
        with open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                  encoding="utf-8") as f:
            du = (json.load(f).get("duties") or {})
        keep_names = {((du.get(k) or {}).get("model") or "") for k in ("big", "resident")}
    except Exception:
        pass
    dropped = []
    for m in models:
        name = m.get("name") or m.get("model") or ""
        if name in keep_names:
            continue
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
            dropped.append(name)
        except Exception:
            pass
    return "thrash(%.0f页/分)%s" % (per_min, (" unloaded:" + ",".join(dropped)) if dropped else "")


def swap_rate_limit():
    """换页速率上限只认 MEM-GUARD-v1.json（单一源）。脉里原来写的是"只要 pageouts 涨就红"，
    而 mem_guard 判的是页/分、阈 120——两处口径不一致的结果是脉常年挂着 swap 假红，
    真抖动反而麻木。取不到配置就退回 120。"""
    try:
        cfg = json.load(open(os.path.join(ROOT, "cph4", "fleet", "MEM-GUARD-v1.json"),
                             encoding="utf-8"))
        return float(cfg.get("pageouts_max_per_min") or 120)
    except Exception:
        return 120.0


def checks(prev: dict | None = None) -> list[dict]:
    out = []
    sw = relieve_swap()
    po = pageouts()
    prev_po = int((prev or {}).get("swap_pageouts") or 0)
    # 判据＝换页速率（页/分），与 mem_guard 同源；不再用"涨了就红"。
    try:
        prev_ts = datetime.strptime(str((prev or {}).get("ts"))[:19], "%Y-%m-%dT%H:%M:%S")
        mins = max((datetime.now() - prev_ts).total_seconds() / 60.0, 0.5)
    except Exception:
        mins = 1.0
    rate = ((po - prev_po) / mins) if (prev_po > 0 and po >= prev_po) else 0.0
    limit = swap_rate_limit()
    growing = rate > limit
    out.append({"name": "swap", "ok": not growing,
                "detail": "live swap %s, 换页 %.1f 页/分（上限 %.0f）%s"
                          % (sw, rate, limit, " THRASHING" if growing else "")})
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


def thermal_state():
    """读本机热压（2026-11-04 CEO「注意散热，毕竟是笔记本」）。

    口径：pmset -g therm 的 CPU_Scheduler_Limit / thermal warning level。
    有热警就返回等级；读不到按 0 处理（不因读不到就停活，那会变成另一种假红）。
    """
    if sys.platform != "darwin":
        return 0
    try:
        out = subprocess.run(["pmset", "-g", "therm"], capture_output=True,
                             text=True, timeout=10).stdout or ""
    except Exception:
        return 0
    m = re.search(r"CPU_Scheduler_Limit\s*=\s*(\d+)", out)
    if m:
        limit = int(m.group(1))
        if limit <= 60:
            return 2
        if limit <= 80:
            return 1
        return 0
    # 本机实测 pmset 不给限速值时（"No CPU power status has been recorded"），
    # 退回负载代理：load 逼近/超过核数就是持续满载，笔记本上这等于在积热。
    try:
        cores = os.cpu_count() or 8
        la = os.getloadavg()[0]
        if la >= cores * 1.2:
            return 2
        if la >= cores * 0.9:
            return 1
    except Exception:
        return 0
    return 0


# 吃 GPU/持续满载的阶段：热压 >=1 时跳过本轮（宁可少干活，不把笔记本烤了）
HEAT_GATED = {"mac_farm", "asset_prompts", "modelradar", "brain", "judge", "digest"}

# 轻重交替（2026-11-04 CEO「交替轻活重活，不要持续满载」）
HEAVY_STAGES = {"mac_farm", "asset_prompts", "modelradar"}
HEAVY_COOLDOWN_S = 600      # 重活之间至少隔 10 分钟（≈两轮慢批），中间只跑轻活
_LAST_HEAVY = 0.0


def run_stage(argv, timeout_s):
    t0 = time.time()
    global _LAST_HEAVY
    _name = os.path.basename(str(argv[0]))
    _stem = _name[:-3] if _name.endswith(".py") else _name
    if _stem in HEAVY_STAGES:
        gap = time.time() - _LAST_HEAVY
        if _LAST_HEAVY and gap < HEAVY_COOLDOWN_S:
            return 0, round(time.time() - t0, 1), \
                "duty-cycle: 距上次重活 %ds < %ds，本轮跑轻活" % (int(gap), HEAVY_COOLDOWN_S)
        _LAST_HEAVY = time.time()
    for k in HEAT_GATED:
        if _name == k + ".py" or (len(argv) > 1 and k in str(argv[1]) and _name.startswith("asset")):
            lvl = thermal_state()
            if lvl >= 1:
                return 0, round(time.time() - t0, 1), "thermal-deferral level=%d（热压偏高，本轮跳过）" % lvl
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
    no_pull = ("--no-pull" in sys.argv) or os.environ.get("PULSE_NO_PULL") == "1"
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
    if no_pull or _git_quarantined():
        git_note = "skipped" if no_pull else "quarantined"
    else:
        git_note = _one_line(pull_if_clean(last_snapshot_ts()), 120)
        if git_note.startswith(("merge-conflict", "timeout", "skipped:dirty", "commit-error")):
            _git_fail(git_note)
        else:
            _git_ok()

    global _LAST_HEAVY
    _LAST_HEAVY = float(prev.get("last_heavy_ts") or 0)
    stages, alerts, failed = {}, [], []

    # 周期开始就先落一次心跳（2026-11-03 实锚）：心跳原本只在串行段跑完后写，
    # 而串行段里 master 可以吃到 240s 超时，整段 >420s 时看门狗会在心跳落盘前
    # 把进程杀掉 → 重启 → 又超时 → 永远跑不完一个周期（PULSE ts 冻在 17:55 两小时）。
    # 先写一次"这一轮开始了"，看门狗要判的是"多久没开新一轮"，而不是"多久没跑完"。
    try:
        _p0 = os.path.join(ROOT, STATE_REL.replace("/", os.sep))
        _t0 = "%s.%d.start" % (_p0, os.getpid())
        # 必须**合并**旧状态而不是覆盖：整份替换会把 slow_ts 抹掉，
        # 于是每轮都判"慢批到期"，慢批变成全速空转（2026-11-03 自造坑）。
        _keep = dict(prev or {})
        _keep.update({"ts": now(), "node": NODE, "phase": "cycle-start",
                      "git": git_note, "ok": True})
        _keep.setdefault("stages", {})
        with open(_t0, "w", encoding="utf-8") as f:
            json.dump(_keep, f, ensure_ascii=False, indent=1)
        os.replace(_t0, _p0)
    except Exception:
        pass

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
    SLOW_SERIAL = {"census", "inventory", "contingency", "solver", "line_agents",
                   # 2026-11-04 CEO「注意散热」：两类 GPU 重活必须串行，不许并发叠热
                   "mac_farm", "asset_prompts"}
    # 瘦身（CEO 2026-11-05「规则和流程空转」）：停掉没有消费者的纯报告阶段，
    # 自检降频。阈值在 AUTONOMY-CONFIG.pulse，代码不写死。
    try:
        _cfg = json.load(open(os.path.join(ROOT, "cph4", "fleet", "AUTONOMY-CONFIG.json"),
                              encoding="utf-8"))
    except Exception:
        _cfg = {}
    _pol = _cfg.get("pulse") or {}
    _off = set(_pol.get("disabled_stages") or [])
    if "canary" in {s[0] for s in STAGES}:
        _every = int(_pol.get("canary_every_cycles") or 1)
        _dir = os.path.join(ROOT, "cph4", "fleet", "state", "canary")
        try:
            _newest = max(os.path.getmtime(os.path.join(_dir, n)) for n in os.listdir(_dir))
            if _every > 1 and (time.time() - _newest) < _every * 18 * 60:
                _off.add("canary")
        except Exception:
            pass
    if _off:
        log("slim: skip %d stage(s): %s" % (len(_off), ",".join(sorted(_off))))
    _active = [s for s in STAGES if s[0] not in _off]
    serial = [s for s in _active if not s[4]]
    slow_serial = [s for s in _active if s[4] and s[0] in SLOW_SERIAL]
    parallel = [s for s in _active if s[4] and s[0] not in SLOW_SERIAL]
    # Two pools by resource, not by "more workers = faster":
    #   MODEL_STAGES share Ollama's 3 slots; giving them 6 threads only queues work.
    #   IO stages are pure python (files/git) and are cheap to run wide.
    MODEL_STAGES = {"judge", "brain", "brain_brief", "social", "biz", "autowork", "digest"}
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
        "last_heavy_ts": _LAST_HEAVY,
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

    # 每阶段最后一次「真跑」（rc 不是 None）的记录。慢批阶段每轮只跑一部分，
    # 而 PULSE.json 每轮被整份覆盖 —— 于是"这个阶段到底跑没跑过"无法回溯，
    # 只能靠翻 /tmp 日志。这份 stage-last.json 是给小屏自证用的唯一凭据。
    try:
        _sl_p = os.path.join(ROOT, "cph4", "fleet", "state", "stage-last.json")
        try:
            _sl = json.load(open(_sl_p, encoding="utf-8"))
        except Exception:
            _sl = {}
        _ts = now()
        # 已删除/改名的阶段会在 stage-last.json 里留成孤儿键，RG-21 会报
        # "记录里有脉里不存在的阶段"。脉是这份数据的唯一写者，孤儿只能由脉自己剪。
        _known = set(stages.keys()) | {s[0] for s in STAGES if s}
        for _k in [k for k in _sl if k not in _known]:
            _sl.pop(_k, None)
        for _n, _v in stages.items():
            if isinstance(_v, dict) and _v.get("rc") is not None:
                _sl[_n] = {"ts": _ts, "rc": _v.get("rc"), "sec": _v.get("sec")}
        os.makedirs(os.path.dirname(_sl_p), exist_ok=True)
        _t2 = "%s.%d.tmp" % (_sl_p, os.getpid())
        with open(_t2, "w", encoding="utf-8") as f:
            json.dump(_sl, f, ensure_ascii=False, indent=1)
        os.replace(_t2, _sl_p)
    except Exception as e:
        log("W-STAGE-LAST %s" % str(e)[:80])
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


    try:
        import json as _j
        _beat = os.path.join(ROOT, "cph4", "fleet", "state", "agent-beat.json")
        _dec = {}
        try:
            with open(os.path.join(ROOT, "cph4", "fleet", "state", "master-decision.json"),
                      encoding="utf-8") as _df:
                _dec = _j.load(_df)
        except Exception:
            _dec = {}
        with open(_beat, "w", encoding="utf-8") as _bf:
            _j.dump({"ts": fl_now() if "fl_now" in globals() else time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "stages": len(stages),
                     "failed": failed,
                     "alerts": alerts[:6],
                     "top": _dec.get("top"),
                     "did": _dec.get("did") or [],
                     "order_new": (lambda: (_j.load(open(os.path.join(
                         ROOT, "cph4/fleet/state/orders-new.json"), encoding="utf-8"))
                         .get("new_count", 0)) if os.path.exists(os.path.join(
                         ROOT, "cph4/fleet/state/orders-new.json")) else 0)()},
                    _bf, ensure_ascii=False, indent=1)
    except Exception as _e:
        log("beat-failed: %s" % str(_e)[:80])

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