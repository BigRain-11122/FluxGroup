#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bmc_supervisor.py — bm-c 智能体监督盘（谁在岗、谁偷懒、谁卡死）

为什么（CEO 2026-11-22「用好用足、排满单子、做好智能体的监控监督」）：
  现在这台机器上常驻 5 个席（生产者/收口员/自省员/ComfyGuard/自动巡航），外加一个 GPU 队列。
  「有没有在干活」不能靠感觉——必须有机器判据：
    · GPU 连续 <10% 且队列里有 pending 活  = **生产者失职**（RED）
    · ComfyUI 不服务                              = **引擎失职**（RED）
    · 某席位超过 2 个节律没心跳                    = **守卫失职**（AMBER）
    · 在飞活长时间无进展                          = **卡死嫌疑**（AMBER）
  每轮写 supervisor.json（机读）+ 一行 log；有 RED/AMBER 时退出码非 0，便于任务面板变红。

用法：python Tools/fleet/bmc_supervisor.py [--quiet]
Exit: 0 GREEN；1 AMBER；2 RED
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = r'K:\Fluxgroup\FluxGroup'
BANK = os.path.join(REPO, 'cph4', 'fleet', 'work-bank', 'bm-c-gpu-bank.json')
PROD = os.path.join(REPO, 'cph4', 'fleet', 'production')
OUT = os.path.join(PROD, 'supervisor.json')
LOG = os.path.join(PROD, 'supervisor.log')
FLAG = r'K:\Fluxgroup\.codely-cli\machine-state.flag'
NO_WIN = 0x08000000 if os.name == 'nt' else 0

# 席位 → (任务名, 最大允许间隔秒)
SEATS = [
    ('生产者 BmcIdleGuard', 'BmcIdleGuard', 900),
    ('收口员 Bmc-ProdFinalize', 'Bmc-ProdFinalize', 1500),
    ('自省员 Bmc-ProdIterate', 'Bmc-ProdIterate', 26 * 3600),
    # 2026-11-22: 两个 ComfyGuard 跑同一脚本同一端口（重复），-bmc 已禁用；
    # 保留直跑 .py 的 FluxGroup-ComfyGuard。
    ('引擎守卫 ComfyGuard', 'FluxGroup-ComfyGuard', 900),
    ('总控 Orchestrator', 'Bmc-Orchestrator', 300),
    ('自动巡航 AutodriveGuard', 'Bmc-AutodriveGuard', 1500),
]


def sh(cmd, timeout=30):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              errors='replace', timeout=timeout,
                              creationflags=NO_WIN).stdout.strip()
    except Exception:
        return ''


def gpu():
    out = sh('nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader')
    try:
        u, used, tot = [x.strip() for x in out.split(',')]
        return int(u.replace('%', '')), int(used.split()[0]), int(tot.split()[0])
    except Exception:
        return -1, -1, -1


def comfy_ok():
    try:
        urllib.request.urlopen('http://127.0.0.1:8188/system_stats', timeout=6).read()
        return True
    except Exception:
        return False


def seat_state(name, task, max_gap):
    ps = ('Get-ScheduledTaskInfo -TaskName "%s" | Select-Object LastRunTime,LastTaskResult,'
          'NumberOfMissedRuns | ConvertTo-Json -Compress' % task)
    out = sh('powershell -NoProfile -Command "%s"' % ps.replace('"', '\\"'))
    try:
        d = json.loads(out) if out else {}
    except Exception:
        d = {}
    lr = d.get('LastRunTime')
    age = None
    if lr:
        try:
            # /Date(ms)/ 或 ISO 都兜一下
            if lr.startswith('/Date('):
                ms = int(lr[6:-2])
                age = time.time() - ms / 1000.0
            else:
                import datetime
                dt = datetime.datetime.fromisoformat(lr[:19])
                age = time.time() - dt.timestamp()
        except Exception:
            age = None
    state = 'OK'
    if age is None:
        state = 'UNKNOWN'
    elif age > max_gap:
        state = 'STALE(%.0f min)' % (age / 60)
    return {'seat': name, 'task': task, 'last_run_age_s': None if age is None else int(age),
            'state': state, 'result': d.get('LastTaskResult')}


def bank_state():
    try:
        b = json.load(open(BANK, encoding='utf-8'))
    except Exception:
        return {}, 0
    st = {}
    for j in b.get('jobs', []):
        st[j.get('status')] = st.get(j.get('status'), 0) + 1
    return st, len(b.get('jobs', []))


def in_flight():
    m = ('Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match '
         "'mv_kf_batch|h3_i2v_album|drama_ep_chain' -and $_.Name -match 'python'} | "
         'Select-Object -First 5 ProcessId | ConvertTo-Json -Compress')
    out = sh('powershell -NoProfile -Command "%s"' % m.replace('"', '\\"'))
    try:
        d = json.loads(out) if out else None
    except Exception:
        d = None
    if not d:
        return []
    return [d] if isinstance(d, dict) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()

    paused = False
    try:
        paused = 'paused' in open(FLAG, 'r', encoding='utf-8', errors='replace').read()
    except Exception:
        pass

    u, used, tot = gpu()
    comfy = comfy_ok()
    st, total = bank_state()
    pending = st.get('pending', 0)
    procs = in_flight()
    seats = [seat_state(n, t, g) for n, t, g in SEATS]

    alerts = []
    if paused:
        verdict = 'PAUSED'
        alerts.append('CEO 让路窗（machine-state.flag=paused）——零动作，正常')
    else:
        busy = u >= 15 or len(procs) > 0
        if not comfy:
            alerts.append('RED ComfyUI 不服务（8188 无响应）→ 引擎守卫失职或引擎崩')
        if not busy and pending > 0:
            alerts.append('RED 空转：GPU %d%% 且无在飞进程，但有 %d 单 pending → 生产者未认领' % (u, pending))
        for s in seats:
            if s['state'].startswith('STALE'):
                alerts.append('AMBER %s 心跳 %s（> 阈值）' % (s['seat'], s['state']))
            elif s['state'] == 'UNKNOWN':
                alerts.append('AMBER %s 读不到 LastRunTime' % s['seat'])
        if busy and u >= 15 and not procs:
            alerts.append('AMBER GPU 忙但无己方在飞进程（可能是他窗/他任务占用）')
        red = any(x.startswith('RED') for x in alerts)
        amber = any(x.startswith('AMBER') for x in alerts)
        verdict = 'RED' if red else ('AMBER' if amber else 'GREEN')

    doc = {'ts': time.strftime('%Y-%m-%dT%H:%M:%S'), 'verdict': verdict, 'paused': paused,
           'gpu_util': u, 'vram_used_mb': used, 'vram_total_mb': tot,
           'comfy': comfy, 'bank': st, 'bank_total': total, 'pending': pending,
           'in_flight': len(procs), 'seats': seats, 'alerts': alerts}
    os.makedirs(PROD, exist_ok=True)
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    line = '%s %-5s gpu=%d%% inflight=%d pending=%d comfy=%s | %s' % (
        doc['ts'], verdict, u, len(procs), pending, 'UP' if comfy else 'DOWN',
        ' ; '.join(alerts) if alerts else 'all seats nominal')
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    if not a.quiet:
        print(line)
        for s in seats:
            print('   %-26s %-14s last=%ss' % (s['seat'], s['state'], s['last_run_age_s']))
    return 0 if verdict in ('GREEN', 'PAUSED') else (1 if verdict == 'AMBER' else 2)


if __name__ == '__main__':
    sys.exit(main())
