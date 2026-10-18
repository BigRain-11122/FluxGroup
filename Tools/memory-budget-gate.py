#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""memory-budget-gate.py v2 - memory-curator seat deterministic gate (zero LLM).
v1 2026-10-15 (O-20261015-1230, memory.md S10); v2 2026-10-18 (CEO order 2026-10-18
"research memory bloat control + dedicated agent" - first-run enforcement of the
memory-curator seat).

v2 fixes & upgrades (vs v1):
  FIX-1 path bug: v1 double-dirname wrote topics/snapshots to <home>\memory\
        instead of <home>\.codely-cli\memory\ (10-16..10-17 each run moved 203
        entries into the stray dir, 1.86MB accumulated). v2 writes the right place
        and de-duplicates topic appends.
  FIX-2 union-fight companion: the poke worker's L0 union/replace-down
        (fleet-memory-sync v2.1) restored the 375KB canonical on every poke while
        this gate trimmed every 4h (gate-log 10-16..10-17 proof). Worker block
        removed + canonical frozen (cph4/fleet/memory/archive/) on 2026-10-18;
        from now on this gate holds.
  UP-1 law auto-keep: LAW_MARKERS (CEO-verdict conventions) hit = standing law,
        never auto-moved (v1 pure whitelist could not keep up with new laws -
        structural flaw behind post-10-15 mis-routes).
  UP-2 keep-side dedup: same-topic version chains (normalized key = first 50 chars
        after stripping bracketed stamps; similarity quick_ratio >= 0.90) keep only
        the latest/longest version - mechanical cure for the "append new version,
        never update" disease.
  UP-3 two-pass enforcement: over exec budget -> move non-law entries; still over
        -> drop the fresh grace (non-law); still over -> CRIT flag + MERGE-QUEUE
        (laws are NEVER auto-truncated or auto-deleted - manual digest belongs to
        the memory-curator seat).
  UP-4 topic-append dedup, LEDGER auto-row, L1 face audit (report-only),
        curator flags dir (MERGE-QUEUE.md / CRIT-FLAG.txt / last-report.json).

Usage:
  python Tools/memory-budget-gate.py [--path <CODELY.md>] [--root <repo>]
       [--budget-bytes 51200] [--budget-entries 120] [--warn-bytes 35840]
       [--warn-entries 80] [--fresh-days 2] [--report] [--scheduled]
Defaults: exec line 50KB/120 items; warn line 35KB/80 items; fresh grace 2 days;
single-law cap 1.5KB (over = MERGE-QUEUE, never auto-cut).
Exit codes: 0 = within budget or enforcement done; 1 = guard mismatch/exception
(do not blind-retry; check the file tail first).
"""
import datetime
import difflib
import os
import re
import sys

SECTIONS = ("User", "Feedback", "Project", "Reference")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
TS_RE = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?")
PREFIX_STRIP_RE = re.compile(r"^(?:\s*-\s*)?(?:\[[^\]]*\]\s*)+")  # v2.1: strip leading "- [ts]" too, norm_key becomes content-based (same-topic chains dedup as designed)

# Standing-law whitelist (all substrings must appear). Per-machine identity rows
# are INTENTIONAL here: each deploying machine adds its own identity tuples
# (bm-a owns the three below; bm-b/bm-c add theirs at deploy time - skill SOP).
KEEP_RULES = [
    ("CEO 汇报语言裁决",), ("CEO 迭代式交付裁决",), ("创作三律",),
    ("CEO 交付地址直给裁决",), ("CEO 深研先行律+过目双闸",),
    ("CEO 呈审纪律总令",), ("CEO 音轨禁令",),
    ("CEO 常设授权令", "否决窗已废止"), ("CEO 三车道+零卡点双令",),
    ("CEO 机队 CPU 常设开放令",), ("CEO 常设工作律",), ("CEO 效率方法论令",),
    ("CEO 账号安全令",), ("CEO 令任务快车道令",),
    ("机队硬件档", "RTX 4070 SUPER 12GB+内存 94GB"), ("本机（C 机/bm-a）定位",),
    ("35B coder 常驻终态",),
    ("用户申斥实录（全自动化裁决律",), ("交互会话零窗口铁律",), ("不要给我弹窗",),
    ("CEO 用机让路律触发词",), ("会话分工定界",), ("用户规则（2026-09-19 重申",),
    ("大文件红线（U187",), ("物理件提醒面",),
    ("bm-a 记忆工具坑", "append_memory", "EEXIST"),
    ("bm-a 工具坑：rg 长多选 CJK pattern 假阴性",),
    ("命令查重律（2026-10-08 立",), ("立法观察期冻结",),
    ("记忆整理归档法",),
    ("云端 token 严管令",), ("活跃产线指针",), ("机队车道两修订",),
    ("游戏公司云道",), ("云端恢复律",),
    # v2.1 2026-10-18 记忆治理席补律：误路由真法条回归 L0（本窗修复批实弹）——新立常设法照 skill memory-curator §二落 KEEP_RULES
    ("调度体系合订",), ("认知更新律",), ("评审机制律合订",), ("资源律合订",),
    ("P0 坑律",), ("EEXIST",), ("并发写入竞态律",), ("静默三连反馈升级",),
    ("whisper 词级锚点误听",), ("死窗瘟疫根因定谳",), ("记忆治理席 memory-curator",),
]
# Standing-law markers (CEO-verdict conventions; a hit keeps the entry verbatim).
LAW_MARKERS = ["原话", "长期律", "长期法", "长期硬门", "常设", "铁律", "红线",
               "硬门", "硬规则", "最高优先"]
LAW_MAX_BYTES = 1500
# Derived/stale index lines - skipped entirely (rebuilt fresh each run).
SKIP_SUBSTRINGS = ["- [memory-gate]", "记忆分层主题索引", "分层重构快照",
                   "精简前全文快照", "被删/被精简条目全文查快照"]
# Other-machine identity rows that arrived via the retired union - move, not keep.
FOREIGN_USER_SKIP = [("机器B", "E:\\Minigame")]

TOPIC_RULES = [
    ("mv-production.md", ["mv0001", "mv-album", "jman", "krea", "h3", "seedance", "i2v", "镜头", "剧本",
                           "选角", "周杰伦", "星晴", "可爱女人", "邝盛", "方文山", "专辑", "mv ",
                           "导演工作流", "改编创作四律", "受众群", "角色设计", "男主", "女主", "whisper 锚点", "歌词"]),
    ("shortvideo-bili.md", ["meme", "短视频", "b站", "bili", "抖音", "切片", "慢慢踩", "法务部", "涨粉", "账号运营", "capcut", "剪映", "神评论"]),
    ("quant-backtest.md", ["回测", "bigmoney", "波链", "w20", "w2", "saturation", "冻结", "席位", "w17", "w18", "纸盘", "量化", "回撤"]),
    ("hardware-procurement.md", ["v100", "t10", "2680v2", "2695", "c602", "ddr", "水冷", "机架", "采购", "3090", "内存条", "散热", "服务器", "电费", "魔改"]),
    ("game-dev.md", ["u360", "吸嘟嘟", "软著", "关卡", "玩法", "steam", "提审", "metis", "tuanjie", "unity",
                     "gui-agent", "硅基", "可视化", "citywatch", "city3d", "minigame", "gimmeall", "游戏"]),
    ("fleet-dispatcher.md", ["fleet", "机队", "dispatcher", "patrol", "巡视", "poke", "tailnet", "心跳", "车道",
                             "fleetlink", "8090", "bm-b", "bm-c", "调度", "自领", "idlewatch", "主agent", "master-agent",
                             "业务法", "让路令", "排满", "满载"]),
    ("git-surgery.md", ["git", "worktree", "原子推", "commit", "push", "pathspec", "refs", "反转闸", "index.lock",
                        "checkout", "blob", "cherry-pick", "竞推", "丢行", "分支"]),
    ("governance-council.md", ["委员会", "council", "法熵", "治理", "正典", "law-registry", "机制总图", "梳理",
                               "否决窗", "cadence", "versioning", "sli", "主脑", "立法", "修法"]),
    ("tool-pitfalls.md", ["powershell", "ps5", "gbk", "编码", "bat", "python", "comfy", "ollama", "whisper", "rg ",
                          "bom", "curl", "下载", "msi", "sdk", "zip", "7z", "进程", "schtasks", "vbs", "工具坑",
                          "坑", "判例", "正法", "探测", "锁", "unity", "取证", "缓存", "音频"]),
]
MISC = "archive-misc.md"


def parse(text):
    sections = {s: [] for s in SECTIONS}
    cur = None
    entries = []
    pend = None
    for ln in text.split("\n"):
        if ln.startswith("### ") and ln[4:].strip() in sections:
            if pend:
                entries.append(pend)
                pend = None
            cur = ln[4:].strip()
            continue
        if ln.startswith("##") or ln.startswith("# "):
            if pend:
                entries.append(pend)
                pend = None
            continue
        if ln.startswith("- ["):
            if pend:
                entries.append(pend)
            pend = [cur, ln]
            continue
        if pend is not None:
            pend[1] += "\n" + ln
    if pend:
        entries.append(pend)
    return entries


def entry_date(body):
    m = DATE_RE.search(body)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def ts_of(body):
    m = TS_RE.match(body)
    if not m:
        return ("0000-00-00", "00:00")
    return (m.group(1), m.group(2) or "00:00")


def is_law(body):
    for rule in KEEP_RULES:
        if all(k in body for k in rule):
            return True
    return any(m in body for m in LAW_MARKERS)


def classify(sec, body, fresh_days, today=None):
    """returns tag: 'user' | 'law' | 'fresh' | 'move' | 'skip'"""
    today = today or datetime.date.today()
    if any(s in body for s in SKIP_SUBSTRINGS):
        return "skip"
    if sec == "User":
        for sub_rule in FOREIGN_USER_SKIP:
            if all(k in body for k in sub_rule):
                return "move"
        return "user"
    if is_law(body):
        return "law"
    d = entry_date(body)
    if d and (today - d).days <= fresh_days:
        return "fresh"
    return "move"


def norm_key(body):
    core = PREFIX_STRIP_RE.sub("", body)
    return re.sub(r"\s+", "", core)[:50]


def topic_of(body):
    low = body.lower()
    for tf, kws in TOPIC_RULES:
        if any(k in low or k in body for k in kws):
            return tf
    return MISC


def _log(msg):
    p = os.path.join(os.environ.get("USERPROFILE", ""), ".codely-cli", "memory", "gate-log.txt")
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write("%s | %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), msg))
    except OSError:
        pass


def _home_mem_dir():
    return os.path.join(os.environ.get("USERPROFILE", ""), ".codely-cli", "memory")


def dedup_keeps(keeps):
    """keeps = list of dicts {sec, body, idx}. Drops same-chain older versions
    (prefix key + quick_ratio >= 0.90); keeps & flags low-similarity same-key pairs.
    Returns (survivors, dropped_dupes, flagged_pairs)."""
    groups = {}
    for e in keeps:
        groups.setdefault(norm_key(e["body"]), []).append(e)
    survivors, dropped, flagged = [], [], []
    for key, members in groups.items():
        if len(members) == 1:
            survivors.extend(members)
            continue
        ranked = sorted(members, key=lambda e: (ts_of(e["body"]), len(e["body"].encode("utf-8")), e["idx"]))
        primary = ranked[-1]
        survivors.append(primary)
        for m in ranked[:-1]:
            ratio = difflib.SequenceMatcher(None, primary["body"], m["body"]).quick_ratio()
            if ratio >= 0.90:
                dropped.append(m)
            else:
                survivors.append(m)
                flagged.append((key, primary["idx"], m["idx"], round(ratio, 2)))
    return survivors, dropped, flagged


def append_topic(topics_dir, tf, body):
    """topic append with exact-line dedup (never re-accumulate a restored entry)."""
    path = os.path.join(topics_dir, tf)
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
    if body.strip() and body.strip() in existing:
        return False
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + body + "\n")
    return True


def write_flags(mem_dir, payload):
    cur_dir = os.path.join(mem_dir, "curator")
    os.makedirs(cur_dir, exist_ok=True)
    with open(os.path.join(cur_dir, "last-report.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(payload, f, ensure_ascii=True, indent=1)
    mq = ["# MERGE-QUEUE (memory-curator manual digest queue) - %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    if payload.get("oversize_laws"):
        mq.append("## OVERSIZE STANDING LAWS (> %dB, digest to <=1.5KB with canon pointer, NEVER delete the rule itself):" % LAW_MAX_BYTES)
        for b, n in payload["oversize_laws"]:
            mq.append("- [%dB] %s" % (n, b[:120]))
    if payload.get("low_sim_dup_groups"):
        mq.append("")
        mq.append("## LOW-SIMILARITY SAME-KEY PAIRS (merge manually, keep the operative law):")
        for key, i1, i2, r in payload["low_sim_dup_groups"]:
            mq.append("- key=%s idx %d vs %d ratio=%.2f" % (key, i1, i2, r))
    if payload.get("l1"):
        mq.append("")
        mq.append("## L1 FACE: %s (%dB, %d items) budget 40KB/60 - over = manual git surgery per L1 law" % (payload["l1"][0], payload["l1"][1], payload["l1"][2]))
    with open(os.path.join(cur_dir, "MERGE-QUEUE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(mq) + "\n")
    if payload.get("crit"):
        with open(os.path.join(cur_dir, "CRIT-FLAG.txt"), "w", encoding="utf-8") as f:
            f.write(payload["crit"] + "\n")
    else:
        try:
            os.remove(os.path.join(cur_dir, "CRIT-FLAG.txt"))
        except OSError:
            pass


def ledger_row(root, row):
    if not root:
        return
    p = os.path.join(root, "cph4", "fleet", "memory-slim", "LEDGER.md")
    if not os.path.exists(p):
        return
    try:
        with open(p, "a", encoding="utf-8", newline="") as f:
            f.write(row + "\n")
    except OSError:
        pass


def main():
    if sys.stdout is None:  # pythonw guard (10-14 lesson)
        sys.stdout = open(os.devnull, "w")
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.dirname(here)
    args = sys.argv[1:]
    home = os.environ.get("USERPROFILE", "")
    path = os.path.join(home, ".codely-cli", "CODELY.md")
    root = default_root
    budget_bytes, budget_entries = 51200, 120
    warn_bytes, warn_entries = 35840, 80
    fresh_days, report_only, scheduled = 2, False, False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--path":
            i += 1; path = args[i]
        elif a == "--root":
            i += 1; root = args[i]
        elif a == "--budget-bytes":
            i += 1; budget_bytes = int(args[i])
        elif a == "--budget-entries":
            i += 1; budget_entries = int(args[i])
        elif a == "--warn-bytes":
            i += 1; warn_bytes = int(args[i])
        elif a == "--warn-entries":
            i += 1; warn_entries = int(args[i])
        elif a == "--fresh-days":
            i += 1; fresh_days = int(args[i])
        elif a == "--report":
            report_only = True
        elif a == "--scheduled":
            scheduled = True
        i += 1

    mem_dir = _home_mem_dir()
    topics_dir = os.path.join(mem_dir, "topics")

    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    norm = text.replace("\r\n", "\n")
    entries = parse(norm)
    n_in = len(entries)
    today = datetime.date.today()

    l1_path = os.path.join(root, "CODELY.md")
    l1_info = (l1_path, os.path.getsize(l1_path), sum(1 for l in open(l1_path, encoding="utf-8-sig", errors="replace") if l.startswith("- [") if True)) if os.path.exists(l1_path) else None

    # classify
    tagged = []
    for idx, (sec, body) in enumerate(entries):
        sec = sec or "Reference"
        body_s = body.strip()
        if not body_s:
            continue
        tagged.append({"sec": sec, "body": body_s, "idx": idx,
                       "tag": classify(sec, body_s, fresh_days, today)})

    keeps = [e for e in tagged if e["tag"] in ("user", "law", "fresh")]
    moves = [e for e in tagged if e["tag"] == "move"]

    # keep-side dedup (kills the append-new-version disease mechanically)
    keeps, dropped_dupes, low_sim = dedup_keeps(keeps)
    moves_for_topics = list(moves) + list(dropped_dupes)

    def keep_bytes_now(lst):
        return sum(len(e["body"].encode("utf-8")) for e in lst)

    overhead = 900  # header + section titles + rebuilt index allowance
    over_exec = (len(raw) > budget_bytes or n_in > budget_entries)
    pass2 = []
    if over_exec:
        est = keep_bytes_now(keeps) + overhead
        est_items = len(keeps)
        if est > budget_bytes or est_items > budget_entries:
            # pass 2: demote the fresh grace (non-law, non-user) to topics
            keep2, pass2 = [], []
            for e in keeps:
                if e["tag"] == "fresh":
                    pass2.append(e)
                else:
                    keep2.append(e)
            keeps = keep2
            moves_for_topics.extend(pass2)  # v2.2 2026-10-18: demoted fresh grace must land in topics (first-run gap: 2 entries held only by snapshot)

    crit = None
    if over_exec:
        est = keep_bytes_now(keeps) + overhead
        if est > budget_bytes:
            crit = ("L0 still over budget after moving all non-law entries: est %dB > %dB "
                    "- standing laws alone exceed the line; manual digest required (MERGE-QUEUE)" % (est, budget_bytes))

    oversize_laws = [(e["body"][:80], len(e["body"].encode("utf-8")))
                     for e in keeps if e["tag"] in ("user", "law") and len(e["body"].encode("utf-8")) > LAW_MAX_BYTES]

    print("GATE-CHECK bytes=%d exec_budget=%d warn=%d entries=%d exec_budget=%d warn=%d"
          % (len(raw), budget_bytes, warn_bytes, n_in, budget_entries, warn_entries))
    print("CLASSIFY keep=%d (user=%d law=%d fresh=%d) move=%d dedup_dropped=%d low_sim=%d pass2_demoted=%d"
          % (len(keeps), sum(1 for e in keeps if e["tag"] == "user"), sum(1 for e in keeps if e["tag"] == "law"),
             sum(1 for e in keeps if e["tag"] == "fresh"), len(moves), len(dropped_dupes), len(low_sim), len(pass2)))
    print("OVERSIZE-LAWS %d  L1=%s  CRIT=%s" % (len(oversize_laws), ("ok" if not l1_info else "%dB/%d" % (l1_info[1], l1_info[2])), bool(crit)))

    payload = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
               "l0": [path, len(raw), n_in],
               "l1": l1_info,
               "keep": len(keeps), "move": len(moves_for_topics),
               "dedup_dropped": len(dropped_dupes), "low_sim": low_sim,
               "oversize_laws": oversize_laws, "crit": crit,
               "budget": [budget_bytes, budget_entries, warn_bytes, warn_entries, fresh_days]}
    write_flags(mem_dir, payload)

    in_warn = (len(raw) <= warn_bytes and n_in <= warn_entries)
    if in_warn or (not over_exec):
        print("GATE-OK within budget - no action")
        if scheduled:
            _log("OK bytes=%d entries=%d" % (len(raw), n_in))
        return 0
    if report_only:
        print("GATE-OVER budget exceeded (--report: report only, no enforcement)")
        return 0

    # ---- enforce ----
    mtime0 = os.path.getmtime(path)
    snapdir = os.path.join(mem_dir, "cleanup-gate-%s" % today.isoformat())
    os.makedirs(snapdir, exist_ok=True)
    with open(os.path.join(snapdir, "CODELY-pre.md"), "wb") as f:
        f.write(raw)

    os.makedirs(topics_dir, exist_ok=True)
    moved_n = 0
    for e in moves_for_topics:
        if append_topic(topics_dir, topic_of(e["body"]), e["body"]):
            moved_n += 1

    keep_by_sec = {s: [] for s in SECTIONS}
    for e in sorted(keeps, key=lambda e: e["idx"]):
        keep_by_sec[e["sec"]].append(e["body"])

    idx = []
    for tf in sorted(f for f in os.listdir(topics_dir) if f.endswith(".md")):
        with open(os.path.join(topics_dir, tf), encoding="utf-8") as f:
            cnt = sum(1 for l in f if l.startswith("- ["))
        idx.append((tf, cnt))

    # v2.1: KEEP the "## Codely Structured Memories" platform marker on line 1 -
    # dropping it (10-18 实锚两案) made append_memory build a duplicate trailing structure block.
    out = ["## Codely Structured Memories\n\n",
           "# CODELY 全局结构记忆 — 分层制 v3（2026-10-15 立·2026-10-18 记忆治理席 memory-curator 接管）\n"
           "> 机制：注入面预算（预警 35KB/80 条·执法 50KB/120 条）·Tools/memory-budget-gate.py v2 每 4h 静默闸（S4U·快照零删除·法条自动保留+同题去重）；"
           "长文/状态/领域细节=memory/topics/（按需读·索引见 ### Reference）；>300 字新条目=先落主题文件再回写指针；"
           "跨机价值一律走 git 正典+L1（memory.md §8/§10·联合回灌已退役）；写入纪律正身=skill memory-curator（cph4/skills/）。\n\n"]
    n_keep = 0
    for sec, title in (("User", "### User"), ("Feedback", "### Feedback"), ("Project", "### Project"), ("Reference", "### Reference")):
        out.append(title + "\n")
        for e in keep_by_sec[sec]:
            out.append(e + "\n")
            n_keep += 1
        if sec == "Reference":
            out.append("- [memory-gate] 记忆分层主题索引（按需读·verbatim 全量在档）：\n")
            for tf, cnt in idx:
                out.append("- %s（%d 条）=%s\\%s\n" % (tf, cnt, topics_dir, tf))
            out.append("- [memory-gate] 历史瘦身快照=memory\\cleanup-* 与 cleanup-gate-*（零删除回滚通道·联合正本冻结件=cph4/fleet/memory/archive/）\n")
        out.append("\n")

    if os.path.getmtime(path) != mtime0:
        print("ABORT: mtime drift (concurrent write) - rerun")
        return 1
    new_text = "".join(out)
    if crlf:
        new_text = new_text.replace("\n", "\r\n")
    nb = (b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8")
    with open(path, "wb") as f:
        f.write(nb)
    print("GATE-EXEC %d->%dB %d->%d条 MOVED=%d topics=%d snapshot=%s"
          % (len(raw), len(nb), n_in, n_keep, moved_n, len(idx), snapdir))
    if crit:
        print("GATE-CRIT " + crit)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    node = os.environ.get("COMPUTERNAME", "?")
    ledger_row(root, "| %s | %d→%d B | %d→%d 条 | v2 首跑执法：联合回灌已拆除+路径修复+法条保留 %d 条+同题去重 %d 链 | %s 记忆治理席 |"
               % (stamp, len(raw), len(nb), n_in, n_keep,
                  sum(1 for e in keeps if e["tag"] == "law"), len(dropped_dupes), node))
    if scheduled:
        _log("EXEC %d->%dB %d->%d条 moved=%d crit=%s" % (len(raw), len(nb), n_in, n_keep, moved_n, bool(crit)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
