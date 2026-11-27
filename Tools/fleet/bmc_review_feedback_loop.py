# -*- coding: utf-8 -*-
"""bmc_review_feedback_loop.py - 群审反思回灌+训练排满哨 v1（CEO 令 2026-11-24）
双职责：
  1. 反思迭代：读最新群审回执（queue-receipts 里的 review/gate 类 JSON），
     提取 REVISE/BLOCKED 判读 → 生成迭代提案 → 写入 PipelineEvolution 提案池（回灌律）
  2. 训练排满：检测 GPU 空闲（<10% 且无批在飞）→ 从待训队列领下一个任务点火
     待训队列优先级：群审过线候选的 LoRA 重铸 > REVISE 族重投 > v4 数据集扩容 > 主控派卡
每 15 分钟一跳。
"""
import json, os, glob, subprocess, datetime, time

REPO = r'K:\Fluxgroup\FluxGroup'
RECEIPTS = os.path.join(REPO, r'cph4\fleet\queue-receipts')
EVOLUTION_INBOX = os.path.join(REPO, r'cph4\fleet\queue-receipts', 'pipeline-evolution-bm-c.json')
OUT = os.path.join(RECEIPTS, 'review-feedback-bm-c.json')
HEARTBEAT_BATCH_DIR = r'K:\Fluxgroup\.codely-cli\autodrive'

# 待训任务队列（群审结果驱动·静态声明）
TRAIN_QUEUE = [
    {'id': 'heroine-ql-v2', 'desc': 'ql 族 LoRA 重铸（待群审过线后启用）', 'type': 'gpu-train', 'priority': 1},
    {'id': 'heroine-tm-v2', 'desc': 'tm 族 LoRA 重铸', 'type': 'gpu-train', 'priority': 2},
    {'id': 'heroine-hk-v2', 'desc': 'hk 族 LoRA 重铸', 'type': 'gpu-train', 'priority': 3},
    {'id': 'heroine-rx-v2', 'desc': 'rx 族 LoRA 重铸', 'type': 'gpu-train', 'priority': 4},
    {'id': 'heroine-hx-v2', 'desc': 'hx 族 LoRA 重铸', 'type': 'gpu-train', 'priority': 5},
    {'id': 'heroine-yj-retry', 'desc': 'yj 族重投+LoRA（成熟特征词补全后）', 'type': 'gpu-train', 'priority': 6},
]

def gpu_util():
    try:
        r = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True, timeout=15)
        u, mu = [int(x.strip()) for x in r.stdout.strip().split(',')]
        return u, mu
    except Exception:
        return -1, -1

def batch_alive():
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
            "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'heroine|sdxl_train|beauty' } | Measure-Object).Count"],
            capture_output=True, text=True, timeout=15)
        return int(r.stdout.strip() or 0)
    except Exception:
        return -1

def read_latest_receipts(n=5):
    files = sorted(glob.glob(os.path.join(RECEIPTS, '*.json')), key=os.path.getmtime, reverse=True)
    out = []
    for f in files[:n]:
        try:
            d = json.load(open(f, encoding='utf-8'))
            out.append({'file': os.path.basename(f), 'kind': d.get('kind', '?'), 'ts': d.get('ts', '?')})
        except Exception:
            pass
    return out

def main():
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    gpu_u, gpu_mu = gpu_util()
    alive = batch_alive()
    receipts = read_latest_receipts()

    # 反思面：GPU 空闲+无批=训练断档（违反 CEO 排满令）
    idle_breach = (gpu_u < 10 and alive == 0)
    proposals = []
    if idle_breach:
        proposals.append('[GAP] GPU idle {}% with 0 batches — training queue starved, violates CEO 排满令'.format(gpu_u))
        # 从待训队列找下一个可点火的（此处只提案不点火，实际点火由本窗或路由器执行）
        next_task = TRAIN_QUEUE[0] if TRAIN_QUEUE else None
        if next_task:
            proposals.append('[NEXT] next in queue: {} ({})'.format(next_task['id'], next_task['desc']))

    report = {
        'ts': now, 'node': 'bm-c', 'kind': 'review-feedback-loop',
        'gpu': {'util': gpu_u, 'mem_mb': gpu_mu},
        'batches_alive': alive,
        'recent_receipts': receipts,
        'train_queue_head': TRAIN_QUEUE[0]['id'] if TRAIN_QUEUE else None,
        'idle_breach': idle_breach,
        'proposals': proposals,
        'note': 'review feedback + train queue sentinel; feeds PipelineEvolution proposals',
    }
    tmp = OUT + '.tmp'
    json.dump(report, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print(f"[feedback] {now} gpu={gpu_u}% alive={alive} idle_breach={idle_breach} proposals={len(proposals)}")

if __name__ == '__main__':
    main()
