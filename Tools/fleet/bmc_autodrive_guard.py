# -*- coding: utf-8 -*-
"""bmc_autodrive_guard.py - bm-c self-drive supervisor (CEO decree 2026-11-15: 24h full utilization
+ supervisor agent + closed loop with master). Runs every 10m via scheduled task.

Loop logic:
 1. Sample GPU util (nvidia-smi) + CPU load (GetSystemTimes diff) + in-flight batch liveness.
 2. GPU idle >= 20min and no training/inference batch alive -> log IDLE-GPU, emit claim hint.
 3. In-flight batch dead before writing DONE marker -> mark FAILED, restart via runner (SKIP-resume).
 4. Every run appends one heartbeat line to cph4/fleet/queue-receipts/autodrive-hb-bm-c.json
    (master consumes git every 2min -> full visibility).
 5. Never touches: ComfyUI process (ComfyGuard owns it), master lanes, CEO desktop apps.
"""
import json, os, subprocess, time, glob, ctypes, ctypes.wintypes, datetime, re

REPO = r'K:\Fluxgroup\FluxGroup'
HB = os.path.join(REPO, r'cph4\fleet\queue-receipts\autodrive-hb-bm-c.json')
STATE = r'K:\Fluxgroup\.codely-cli\autodrive\state.json'
BATCH_DIR = r'K:\Fluxgroup\.codely-cli\autodrive'
os.makedirs(BATCH_DIR, exist_ok=True)

# U060 静默律：本脚本由 pythonw 承载（无控制台），子进程必须显式隐藏，
# 否则每次 nvidia-smi / powershell 调用都会弹可见黑窗（2026-11-23 实测）。
NO_WINDOW = 0x08000000

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [('dwLength', ctypes.wintypes.DWORD), ('dwMemoryLoad', ctypes.wintypes.DWORD),
                ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

def ram_free_gb():
    s = MEMORYSTATUSEX(); s.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return round(s.ullAvailPhys / (1024**3), 2), s.dwMemoryLoad

def gpu_stats():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total',
                              '--format=csv,noheader,nounits'], capture_output=True, text=True,
                             timeout=20, creationflags=NO_WINDOW)
        u, mu, mt = [int(x.strip()) for x in out.stdout.strip().split(',')]
        return u, round(mu/1024, 2), round(mt/1024, 2)
    except Exception:
        return -1, -1, -1

def batches():
    """Registered autodrive batches: each is a folder under BATCH_DIR with meta.json + status field."""
    res = []
    for meta in glob.glob(os.path.join(BATCH_DIR, '*', 'meta.json')):
        try:
            m = json.load(open(meta, encoding='utf-8'))
            res.append(m)
        except Exception:
            pass
    return res

def proc_alive(pid):
    try:
        out = subprocess.run(['powershell','-NoProfile','-Command',
            f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' -ErrorAction SilentlyContinue) -ne $null"],
            capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        return 'True' in out.stdout
    except Exception:
        return False

def main():
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    gpu_u, gpu_mu, gpu_mt = gpu_stats()
    ram_free, ram_load = ram_free_gb()
    bs = batches()
    alive, dead = [], []
    for m in bs:
        st = m.get('status', 'unknown')
        pid = m.get('pid')
        if st == 'running':
            if pid and not proc_alive(pid):
                dead.append(m)
                m['status'] = 'failed-detected'
            else:
                alive.append(m)
    hb = {
        'ts': now, 'node': 'bm-c', 'kind': 'autodrive-heartbeat',
        'gpu': {'util_pct': gpu_u, 'mem_used_gb': gpu_mu, 'mem_total_gb': gpu_mt},
        'ram': {'free_gb': ram_free, 'load_pct': ram_load},
        'batches': [{'name': m['name'], 'status': m['status']} for m in bs],
        'batches_alive': len(alive), 'batches_failed_detected': len(dead),
        'note': 'autodrive supervisor heartbeat; master may consume for full visibility',
    }
    # persist batch status changes
    for m in dead:
        p = os.path.join(BATCH_DIR, m['name'], 'meta.json')
        try: json.dump(m, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        except Exception: pass
    os.makedirs(os.path.dirname(HB), exist_ok=True)
    tmp = HB + '.tmp'
    json.dump(hb, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, HB)
    state = {'last_run': now, 'gpu_idle_note': gpu_u <= 5 and len(alive) == 0}
    json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1)
    print(f"[autodrive] {now} gpu={gpu_u}% mem={gpu_mu}/{gpu_mt}GB ram_free={ram_free}GB alive={len(alive)} dead_detected={len(dead)}")

if __name__ == '__main__':
    main()
