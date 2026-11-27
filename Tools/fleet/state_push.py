#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_push.py [LEGACY 2026-11-10：git 同步已由 state_sync 独立面承担，本工具不再挂脉] - 用独立工作树把「状态面」推上主线，绕开主工作树的手改/分叉。

Why（2026-11-07 凌晨实测）：主控脉与人工会话共用同一个 git 工作树，只要工作树里有任何未提交
改动（哪怕是修 bug 时放进去的新版文件），脉就判 `git=skipped:dirty(hand-edit ...)` 整段跳过
git。后果不是"晚一点同步"，而是**卡永远不在 origin 上翻面**：车道把同一张卡一遍遍重跑
（bm-m 实测同一张卡连跑 3 次 0.1s），供给看起来永远空，机队满负荷是假的。

正解：状态面（队列 + 回执 + 车道状态）不跟人抢工作树，改为在独立 worktree 里提交推送。
产品代码仍走人工/worktree 流程，两者物理隔离。

推什么（白名单，其余一律不动）：
  cph4/fleet/PRODUCTION-QUEUE.jsonl
  cph4/fleet/PRODUCTION-BACKLOG.jsonl
  cph4/fleet/queue-receipts/**.json
  cph4/fleet/state/remote-receipts/**.json（若未被 ignore）
  cph4/fleet/lanes/**.json

用法：
  python3 Tools/fleet/state_push.py            # 一轮（无变化则静默退出）
  python3 Tools/fleet/state_push.py --dry
Exit: 0 正常（含无变化）｜2 推送失败（已回滚工作树，不影响主工作树）
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WT = os.path.join(os.path.dirname(ROOT), ".fluxgroup-state-wt")

STATE_FILES = [
    "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
]
STATE_DIRS = [
    "cph4/fleet/queue-receipts",
    "cph4/fleet/lanes",
]


def sh(args, cwd=None, timeout=180):
    p = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


CARD_ID_RE = re.compile(rb'"id"\s*:\s*"([^"]+)"')
STATE_RE = re.compile(rb'"state"\s*:\s*"([A-Za-z_]+)"')
TERMINAL_STATES = {b"DONE", b"CANCELLED", b"FAILED", b"UNVERIFIED", b"BLOCKED"}


def _split_lines(blob):
    return [ln.rstrip(b"\r") for ln in blob.split(b"\n") if ln.strip()]


def _line_id(line):
    m = CARD_ID_RE.search(line)
    return m.group(1) if m else None


def _rank(line):
    """Terminal states outrank in-flight ones, so a stale local OPEN cannot
    resurrect a card origin already closed."""
    m = STATE_RE.search(line)
    return 2 if (m and m.group(1) in TERMINAL_STATES) else 1


def merge_jsonl(origin_bytes, local_bytes):
    """Union JSONL cards by id: origin-only cards survive, local wins on ties.
    Line bytes are never re-decoded, so mixed/GBK JSONL stays intact."""
    if not origin_bytes:
        return local_bytes
    if not local_bytes:
        return origin_bytes
    origin_lines = _split_lines(origin_bytes)
    local_lines = _split_lines(local_bytes)
    local_by_id = {}
    local_plain = []
    for ln in local_lines:
        cid = _line_id(ln)
        if cid is None:
            local_plain.append(ln)
        else:
            local_by_id[cid] = ln
    seen = set()
    out = []
    for ln in origin_lines:
        cid = _line_id(ln)
        if cid is None:
            out.append(ln)
            continue
        if cid in seen:
            continue
        seen.add(cid)
        loc = local_by_id.get(cid)
        out.append(loc if (loc is not None and _rank(loc) >= _rank(ln)) else ln)
    out.extend(local_plain)
    for cid, ln in local_by_id.items():
        if cid not in seen:
            out.append(ln)
    nl = b"\r\n" if b"\r\n" in origin_bytes else b"\n"
    return nl.join(out) + nl


def origin_blob(rel):
    """Raw bytes of origin/main:<rel> (no text decoding)."""
    p = subprocess.run(["git", "show", "origin/main:" + rel], cwd=ROOT,
                       capture_output=True, timeout=120)
    return p.stdout if p.returncode == 0 else b""


def ensure_worktree():
    """独立工作树：不存在就基于 origin/main 建一个（detached，不占分支名）。"""
    if os.path.isdir(os.path.join(WT, ".git")) or os.path.isfile(os.path.join(WT, ".git")):
        return True
    sh(["git", "worktree", "prune"])
    sh(["git", "fetch", "--quiet", "origin", "main"])
    rc, out, err = sh(["git", "worktree", "add", WT, "origin/main", "--detach"])
    return rc == 0


def _state_ts(raw):
    """'ts' of a mirror-state JSON, or None when unparseable/absent."""
    try:
        d = json.loads(raw.decode("utf-8-sig"))
    except Exception:
        return None
    if isinstance(d, dict):
        for k in ("ts", "updated_at", "generated_at"):
            v = d.get(k)
            if isinstance(v, str) and v:
                return v
    return None


def newer_state_wins(origin_bytes, local_bytes):
    """Mirror state (lanes/receipts): the newer 'ts' wins, never "local always".

    2026-11-09 R19 live case: a dispatcher assignment written into
    cph4/fleet/lanes/bm-b.json lived 56 seconds - this mirror's blind copyfile of its
    own stale copy erased it, and the starved node never saw the job. Assignments and
    node state both carry 'ts', so comparing them keeps the newest truth either way
    without letting one side win by default.
    """
    if not origin_bytes:
        return local_bytes
    ot, lt = _state_ts(origin_bytes), _state_ts(local_bytes)
    if ot is None or lt is None:
        return local_bytes          # unparseable: keep today's behaviour
    return local_bytes if lt >= ot else origin_bytes


def sync_into_worktree():
    """把状态面复制进独立工作树。返回是否有变化。

    2026-11-08：队列/备料改为「origin ∪ 本地 按 id 合并」，不再整文件覆盖。
    病理实锚＝本席 00:47 恢复的 RESCUE-FREEMEM-BM-C-20261108 在 00:50/00:51
    两轮同步后被本地陈旧队列整文件覆盖（numstat 15/15），append 派发的卡
    凭空消失（同族 R11-7/R12-1/R14-7）。
    """
    n = 0
    sh(["git", "fetch", "--quiet", "origin", "main"])
    for rel in STATE_FILES:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(WT, rel)
        if not os.path.isfile(src):
            continue
        with open(src, "rb") as fh:
            local = fh.read()
        ob = origin_blob(rel)
        if not ob:
            # Never fall back to "local wins" when origin is unreadable
            # (partial/promisor clone, transient git error): that is exactly
            # how appended cards disappeared. Keep origin's copy instead.
            print("[state-push] W-SKIP-NO-ORIGIN %s（保留 origin 版，不覆盖）" % rel)
            n += 1
            continue
        merged = merge_jsonl(ob, local)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(merged)
        n += 1
    for rel in STATE_DIRS:
        src = os.path.join(ROOT, rel)
        if not os.path.isdir(src):
            continue
        for dirpath, _dirs, files in os.walk(src):
            for f in files:
                if not f.endswith(".json"):
                    continue
                s = os.path.join(dirpath, f)
                relpath = os.path.relpath(s, ROOT).replace(os.sep, "/")
                d = os.path.join(WT, os.path.relpath(s, ROOT))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                try:
                    with open(s, "rb") as fh:
                        local = fh.read()
                    with open(d, "wb") as fh:
                        fh.write(newer_state_wins(origin_blob(relpath), local))
                    n += 1
                except Exception:
                    pass
    return n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if not ensure_worktree():
        print("[state-push] worktree 建立失败")
        return 2
    # 顺序很重要：先把工作树对齐到最新 origin，再复制状态面，再提交推送。
    # 反过来（先复制再 rebase）在有并发推送时必然冲突——队列是 append log，同一行必撞。
    copied = 0
    for attempt in range(1, 5):
        sh(["git", "fetch", "--quiet", "origin", "main"], cwd=WT)
        sh(["git", "reset", "-q", "--hard", "origin/main"], cwd=WT)
        copied = sync_into_worktree()
        # 推送前自清（2026-11-08 教训）：队列/备队列一旦带 git 冲突标记被推上 origin，
        # 执行机读到的是坏账本，qcheck 判 RED 后主控"读不到卡"，机队整下午空转。
        # 我这轮就是这么把 383+710 个冲突块推上去的——所以闸要放在**推送通道里**，
        # 不能只靠"改完记得检查"。
        try:
            sys.path.insert(0, HERE)
            import queue_sanitize as _qs
            for _rel in _qs.TARGETS:
                _wtp = os.path.join(WT, _rel)
                if not os.path.isfile(_wtp):
                    continue
                _b, _nj, _tot = _qs.scan(_wtp)
                if _b or _nj:
                    _r = _qs.fix(_wtp)
                    print("[state-push] W-QUEUE-POLLUTED %s 冲突块=%d 非JSON=%d → 已自清 %s"
                          % (_rel, _b, _nj, _r))
        except Exception as _e:
            print("[state-push] W-QUEUE-GUARD 自清失败：%s" % str(_e)[:120])
        rc, dirty, _ = sh(["git", "status", "--porcelain"], cwd=WT)
        if not dirty.strip():
            # 2026-11-08 假绿修复：状态面没变化 ≠ 已同步。以前到这里直接 return 0，
            # 而主工作树可能有未推的提交（实测：报"1429 个文件已同步"，实际本地领先
            # origin 2 个提交、机队拿不到新代码/新卡）——ops_metrics 的"同步成功 0%"就是这个。
            rc, ahead, _ = sh(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=ROOT)
            rc2, behind, _ = sh(["git", "rev-list", "--count", "HEAD..origin/main"], cwd=ROOT)
            try:
                n_ahead, n_behind = int((ahead or "0").strip()), int((behind or "0").strip())
            except Exception:
                n_ahead = n_behind = 0
            if n_ahead and not n_behind:
                if a.dry:
                    print("[state-push] would push %d pending commit(s)" % n_ahead)
                    return 0
                rc3, out3, err3 = sh(["git", "push", "-q", "origin", "HEAD:main"], cwd=ROOT)
                if rc3 == 0:
                    print("[state-push] 补推 %d 个未推提交（状态面本已同步，%d 个文件）"
                          % (n_ahead, copied))
                    return 0
                print("[state-push] 补推失败(%d 提交):%s" % (n_ahead, (err3 or out3)[:160]))
                return 2
            if n_ahead and n_behind:
                # 既领先又落后：不在共享工作树里 rebase（会与脉/并发车道抢树），显式报出。
                print("[state-push] DIVERGED 本地领先 %d / 落后 %d，未自动处理"
                      % (n_ahead, n_behind))
                return 2
            print("[state-push] 无状态变化（%d 个文件已同步）" % copied)
            return 0
        if a.dry:
            print("[state-push] would push:\n" + dirty[:1200])
            return 0
        sh(["git", "add", "-A"], cwd=WT)
        name = sh(["git", "config", "user.name"])[1] or "fleet"
        mail = sh(["git", "config", "user.email"])[1] or "fleet@local"
        msg = "state: 队列/回执同步 %s [via bm-m]" % time.strftime("%Y-%m-%dT%H:%M")
        rc, out, err = sh(["git", "-c", "user.name=" + name, "-c", "user.email=" + mail,
                           "commit", "-q", "-m", msg], cwd=WT)
        if rc != 0:
            print("[state-push] commit 失败:", (err or out)[:160])
            return 2
        rc, out, err = sh(["git", "push", "-q", "origin", "HEAD:main"], cwd=WT)
        if rc == 0:
            head = sh(["git", "rev-parse", "--short", "HEAD"], cwd=WT)[1]
            print("[state-push] pushed", head, "files=%d attempt=%d" % (copied, attempt))
            return 0
        time.sleep(2)
    print("[state-push] push 失败（4 次，并发推送太密）")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))