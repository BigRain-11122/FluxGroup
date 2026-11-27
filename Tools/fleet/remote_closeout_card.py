#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""remote_closeout_card.py - 用「卡」当远程执行通道，把分叉节点拉回 origin。

为什么（2026-11-07 实证）：FleetLink 的 /poke 只做 `git merge --ff-only`，节点一旦
有本地提交就永远拉不到新代码——"我们修好了，机器还在跑旧码"的唯一结构性原因。
但 Tools/queue_claim.py 第 376 行是 `subprocess.run(job["cmd"], shell=True, ...)`：
卡里的 cmd 本来就是在节点上执行的**通用命令通道**，只是从来没用过。

本工具生成一张自包含卡：cmd 是 base64 编码的 PowerShell（UTF-16LE），因此
  - 不依赖节点上任何新文件（正是要解决的问题）
  - 不受 Windows 引号 / 中文编码 / 换行影响（PS 5.1 读无 BOM 的 .ps1 会按 GBK）
执行序列照 node_closeout.ps1 的安全线，绝不 --hard、绝不 rebase、绝不 push 历史：
  1) 救生分支 salvage-auto-<ts>（本地提交一个都不丢）
  2) fetch origin main
  3) reset --mixed origin/main（提交对齐，工作树文件保留）
  4) checkout origin/main -- Tools（只把工具树换成 origin 版，这是"新代码到机"的关键）
  5) 自校验 HEAD==origin/main 并写回执 cph4/fleet/queue-receipts/closeout-<node>.json

用法：
  python3 Tools/fleet/remote_closeout_card.py --nodes bm-a,bm-c [--apply]
  python3 Tools/fleet/remote_closeout_card.py --print-cmd     # 只打印可粘贴命令
"""
import argparse
import base64
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")

# 纯 ASCII：PS 5.1 在 GBK 代码页下读无 BOM 脚本，中文会吃掉引号字节
PS = r"""
$ErrorActionPreference='Continue'
$roots=@('C:\Fluxgroup\FluxGroup','C:/Fluxgroup/FluxGroup','C:\Users\sjs20\Desktop\FluxGroup','K:/Fluxgroup/FluxGroup','K:\Fluxgroup\FluxGroup')
$root=$null
foreach($c in $roots){ if(Test-Path (Join-Path $c '.git')){ $root=$c; break } }
if(-not $root){ Write-Output 'E-NOROOT'; exit 2 }
$ts=(Get-Date).ToString('yyyyMMdd-HHmmss')
$tag='salvage-auto-'+$ts
& git -C $root branch $tag 2>&1 | Out-Null
& git -C $root fetch origin main 2>&1 | Out-Null
if($LASTEXITCODE -ne 0){ Write-Output 'E-FETCH'; exit 3 }
$ah=(& git -C $root rev-list --count origin/main..HEAD) -join ''
$bh=(& git -C $root rev-list --count HEAD..origin/main) -join ''
& git -C $root reset --mixed origin/main 2>&1 | Out-Null
& git -C $root checkout origin/main -- Tools 2>&1 | Out-Null
$h=((& git -C $root rev-parse HEAD) -join '').Trim()
$o=((& git -C $root rev-parse origin/main) -join '').Trim()
$ok='false'; if($h -eq $o){ $ok='true' }
$node='__NODE__'
$rd=Join-Path $root 'cph4\fleet\queue-receipts'
New-Item -ItemType Directory -Force -Path $rd | Out-Null
$rec='{"node":"'+$node+'","ts":"'+(Get-Date).ToString('o')+'","before_ahead":'+$ah+',"before_behind":'+$bh+',"head":"'+$h+'","origin":"'+$o+'","aligned":'+$ok+',"salvage":"'+$tag+'"}'
Set-Content -Path (Join-Path $rd ("closeout-"+$node+".json")) -Value $rec -Encoding UTF8
Write-Output $rec
"""


def encoded(ps_text):
    return base64.b64encode(ps_text.encode("utf-16-le")).decode("ascii")


def ps_for(node):
    return PS.replace("__NODE__", node)


def card_for(node, cmd):
    return {
        "state": "OPEN", "owner": None,
        "id": "REMOTE-CLOSEOUT-%s-20261107" % node,
        "title": "远程收口：把 %s 的分叉仓库拉回 origin（自包含命令，不依赖节点文件）" % node,
        "cmd": cmd,
        "cwd": "",
        "requires": [],
        "deliverable": "cph4/fleet/queue-receipts/closeout-%s.json" % node,
        "accept": "回执 aligned=true 且 head==origin；否则看 before_ahead/before_behind 与 E- 前缀",
        "needs": "cpu", "nodes": [node], "hard_nodes": [node], "prio": "P0", "day_ok": True,
        "heavy": False, "timeout_s": 600,
        "why": "跨机执行断点：poke 只做 ff-only，分叉节点永远拉不到新代码。卡 cmd 是通用执行通道（queue_claim 用 shell=True）",
        "created_by": "remote_closeout_card", "verify_on_node": True,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", default="bm-a,bm-b,bm-c")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--print-cmd", action="store_true")
    a = ap.parse_args(argv)
    cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand ' + encoded(PS)
    if a.print_cmd:
        node = [n.strip() for n in a.nodes.split(",") if n.strip()][0]
        print('powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand ' + encoded(ps_for(node)))
        return 0
    nodes = [n.strip() for n in a.nodes.split(",") if n.strip()]
    made = []
    for n in nodes:
        c = card_for(n, 'powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand '
                        + encoded(ps_for(n)))
        if not a.apply:
            made.append(c["id"])
            print("[dry] %s  cmd_len=%d" % (c["id"], len(cmd)))
            continue
        rows = []
        for p in (QUEUE, BACKLOG):
            # 2026-11-11 旧队列已归档（"机制变了就从头开始"），这里原来会直接
            # FileNotFoundError——收口卡于是自那时起一张都发不出去。
            if not os.path.exists(p):
                continue
            rows += [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        if any(r.get("id") == c["id"] for r in rows):
            print("[skip] %s 已存在" % c["id"])
            continue
        # 2026-11-14：不再写退役的 PRODUCTION-QUEUE.jsonl——上一版在这里 append，
        # 会把这个 11-11 已归档的文件重新创建出来，把"旧通道"复活，RG-09/10 于是
        # 拿一份没人执行的文件判红。收口卡只走 v3。
        # 2026-11-14：分叉机可能还在读旧队列，所以旧通道照写；但 v3 执行面
        # （rt/<station>/queue.jsonl）必须同时投一份，否则"新机器收不到、老机器
        # 又不认"，收口就永远只停在文件里。
        try:
            import station_shards as ss
            NODE2ST = {"bm-a": "delivery", "bm-b": "audio", "bm-c": "visual",
                       "bm-d": "brain", "bm-m": "control"}
            st = NODE2ST.get(n)
            if st:
                row = {"id": c["id"], "station": st, "state": "OPEN",
                       "product_id": "", "stage": "closeout-%s" % c["id"][-8:],
                       "cmd": c["cmd"], "cmd_reviewed": True,
                       "deliverable": c.get("deliverable") or "", "judge": "path",
                       "requires": [], "why": c.get("why") or "分叉收口",
                       "created_by": "remote_closeout_card",
                       "created_at": c.get("created_at")}
                if st == "control":
                    ss.upsert("control", row)
                else:
                    ss.append_outbox("control", [row])
                print("[v3] %s -> %s" % (c["id"], st))
        except Exception as e:
            print("[v3] 投递失败：%s" % str(e)[:60])
        print("[queued] %s" % c["id"])
        made.append(c["id"])
    print("done: %s" % made)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))