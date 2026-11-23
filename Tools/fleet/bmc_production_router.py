# -*- coding: utf-8 -*-
"""bmc_production_router.py - bm-c 产线路由器 v1（CEO 令 2026-11-22:
科学排产线+全面利用本地算力+多方案接续（某环节卡了就换下一个方案））

三层结构：
  L1 资源感知：GPU util / 显存 / 8189-8188 健康 / 在飞批存活
  L2 卡点检测：单 shot 超 8 分钟不出货 / 队列死 / 训练无进展 → 判卡
  L3 方案切换：GPU 主线卡 → 切 CPU 线（音色语料/清洗）→ 切备线（v3 数据集扩容/道具库）

产物：cph4/fleet/queue-receipts/production-router-bm-c.json（主控可见）
用法：每 5 分钟跑一次（task-register 正门注册）
"""
import json, os, subprocess, time, glob, datetime

REPO = r'K:\Fluxgroup\FluxGroup'
OUT_JSON = os.path.join(REPO, r'cph4\fleet\queue-receipts\production-router-bm-c.json')
OUT_DIR = r'D:\ComfyUI\ComfyUI\output'
# U060 静默律：本脚本由 pythonw 承载（无控制台），子进程必须显式隐藏，
# 否则每次 nvidia-smi / powershell 调用都会弹可见黑窗（2026-11-23 实测）。
NO_WINDOW = 0x08000000

def gpu_stats():
    try:
        r = subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],
                           capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        u, mu, mt = [int(x.strip()) for x in r.stdout.strip().split(',')]
        return u, mu, mt
    except Exception:
        return -1, -1, -1

def comfy_health(port):
    try:
        import urllib.request
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/system_stats', timeout=5) as r:
            return True
    except Exception:
        return False

def batch_alive(pattern):
    """在飞 python 批存活数"""
    try:
        r = subprocess.run(['powershell','-NoProfile','-Command',
            f"(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {{ $_.CommandLine -match '{pattern}' }} | Measure-Object).Count"],
            capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        return int(r.stdout.strip() or 0)
    except Exception:
        return -1

def recent_outputs(prefix, minutes=10):
    """最近 N 分钟内指定前缀的产出数（出货速率）"""
    cutoff = time.time() - minutes * 60
    n = 0
    for f in glob.glob(os.path.join(OUT_DIR, prefix + '*')):
        if os.path.getmtime(f) > cutoff:
            n += 1
    return n

def main():
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    gpu_u, gpu_mu, gpu_mt = gpu_stats()
    h89, h88 = comfy_health(8189), comfy_health(8188)
    heroine_alive = batch_alive('heroine')
    pl_rate = recent_outputs('pl_ql', 10)

    # L2 卡点判定
    stalls = []
    if heroine_alive > 0 and pl_rate == 0 and gpu_u < 20:
        stalls.append('gpu-lane-stalled: factory alive but no output & GPU idle')
    if not h89 and not h88:
        stalls.append('both-comfy-down')
    # L3 方案路由
    plan = 'gpu-mainline'          # 主线：女主 LoRA 工厂（8189 PuLID 流水线）
    if 'gpu-lane-stalled' in stalls:
        plan = 'switch-cpu-lane'   # 切 CPU：音色语料/数据清洗/道具库提案
    elif 'both-comfy-down' in stalls:
        plan = 'switch-comfy-guard-revive'

    report = {
        'ts': now, 'node': 'bm-c', 'kind': 'production-router',
        'gpu': {'util': gpu_u, 'mem_used_mb': gpu_mu, 'mem_total_mb': gpu_mt},
        'comfy': {'8189': h89, '8188': h88},
        'batches': {'heroine_factory': heroine_alive},
        'throughput': {'pl_ql_last10min': pl_rate},
        'stalls': stalls, 'plan': plan,
        'lanes': {
            'gpu-mainline': 'heroine-lora-factory (ql in-flight, then tm/hk...)',
            'gpu-alt-1': 'main-dispatch KF batches (8188)',
            'gpu-alt-2': 'v3 dataset expansion / verify boards',
            'cpu-mainline': 'voicebank corpus (audio-separator+whisperX, awaiting jobs list)',
            'cpu-alt-1': 'asset-lib proposals (styles/typography)',
            'cpu-alt-2': 'captions/cleanup for training data',
        },
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    tmp = OUT_JSON + '.tmp'
    json.dump(report, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT_JSON)
    print(f"[router] {now} gpu={gpu_u}% mem={gpu_mu}/{gpu_mt} 8189={h89} 8188={h88} "
          f"factory={heroine_alive} pl_rate={pl_rate}/10min plan={plan}")

if __name__ == '__main__':
    main()
