#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git-no-reversal-check.py — 推前反转闸（versioning §4.4 ⑤·2026-10-14 fc1b936 修法包回退事故后立）
                              + --audit 丢行守望档（同日第三次丢行案后立·b9af38b 陈旧基吞 3 行实录）

用法:
  python Tools/git-no-reversal-check.py <候选提交SHA> [origin_ref] [--whitelist-file <file>] [--depth N] [--audit]

判据（普通档）: origin 近 N 笔(默认10)提交的每条「有意义增行」(>=16 字符·非表头/分隔/纯符号):
      ① 候选树中在 -> OK;
      ② 候选树中无但 origin 现行内容中也无 -> 本前已亡(他窗正当改写) -> 跳过;
      ③ 候选树中无而 origin 现行内容中在 -> REVERSAL·exit 1（本批删了活行·停推）。
      白名单文件=一行一个路径前缀, 命中跳过(合法归档/改名须在提交信息注明)。
判据（--audit 自审计档·丢行守望）: 跳过②存活过滤与例外表——近 N 笔历史增行在候选树中消失即全部报出
      （含正当改写·作晨检/死线班告警清单人工判读；丢行→按行所在提交 blob 逐字恢复+补录注记=事件班处理）。
巡班执法（ROUND 步8 附）: python Tools/git-no-reversal-check.py origin/main origin/main --depth 30 --audit
场景: 外科提交/直改提交 push 前最后一道闸 + 每日丢行守望——防陈旧树提交把他窗新上链内容静默回退。
注意: 候选与 origin_ref 须已 fetch; 候选树基于 origin_ref 构建(同链)。
"""
import subprocess
import sys

GIT = r"C:\Program Files\Git\cmd\git.exe"


def run(*a):
    return subprocess.run([GIT] + list(a), capture_output=True).stdout.decode("utf-8", "replace")


def main():
    argv = sys.argv[1:]
    pos = [a for a in argv if not a.startswith("--")]
    cand = pos[0] if pos else "HEAD"
    origin = pos[1] if len(pos) > 1 else "origin/main"
    depth = 10
    if "--depth" in argv:
        depth = int(argv[argv.index("--depth") + 1])
    AUDIT = "--audit" in argv
    wl = []
    if "--whitelist-file" in argv:
        with open(argv[argv.index("--whitelist-file") + 1], encoding="utf-8-sig") as fh:
            wl = [l.strip() for l in fh if l.strip() and not l.startswith("#")]

    shas = run("log", origin, "-%d" % depth, "--format=%H").split()
    bad = 0
    checked = 0
    skipped = 0
    for sha in shas:
        parent = run("rev-parse", sha + "^").strip()
        files = run("show", sha, "--name-only", "--format=").splitlines()
        for f in files:
            if not f or any(f.startswith(p) or p in f for p in wl):
                continue
            cand_b = subprocess.run([GIT, "show", cand + ":" + f], capture_output=True).stdout
            cur = cand_b.decode("utf-8-sig", "replace") if cand_b else ""
            o_b = subprocess.run([GIT, "show", origin + ":" + f], capture_output=True).stdout
            cur_o = o_b.decode("utf-8-sig", "replace") if o_b else ""
            d = run("diff", parent, sha, "--unified=0", "--", f)
            for line in d.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    s = line[1:].rstrip("\r").strip()
                    if len(s) >= 16 and not s.startswith(("|---", "| 日期", "---", "#", "++")):
                        checked += 1
                        if s in cur:
                            continue
                        if not AUDIT and s not in cur_o:
                            skipped += 1
                            continue
                        bad += 1
                        print("  REVERSAL %s %s :: %s" % (sha[:8], f, s[:60].encode("unicode_escape").decode("ascii")))
    if bad:
        mode = "AUDIT-ALERT(丢行守望·含正当改写·人工判读)" if AUDIT else "REVERSAL-DETECTED"
        print("%s: %d / %d 条历史增行在候选树中消失 (本前已亡跳过 %d)" % (mode, bad, checked, skipped))
        if not AUDIT:
            print("停推。先做内容级并合(以 origin 尾为锚重放)再推；合法归档/改名走 --whitelist 并在提交信息注明。")
        sys.exit(1)
    print("NO-REVERSAL: 近 %d 笔 origin 增行检查 %d 条·零消失·放行 (本前已亡跳过 %d)" % (depth, checked, skipped))


if __name__ == "__main__":
    main()
