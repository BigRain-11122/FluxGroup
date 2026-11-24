# -*- coding: utf-8 -*-
"""
地产线每日拉取：官方日成交 + 平台板块 + 公众号新文，末尾跑一次模型出当日一屏。

用法：
    python Tools/house/daily_pull.py                # 全跑
    python Tools/house/daily_pull.py --skip-wechat   # 跳过公众号（省流量/防限流）

设计原则：
- 任一步失败不影响其他步，逐步记录 rc；整体 rc=0 仅当三件都成功。
- 只做只读抓取 + 落盘，不改任何既有数据文件（官方快照脚本自身同日覆盖）。
- 公众号关键词按天轮换，避免每天同一词反复打搜狗触发验证码。
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUTDIR = os.path.join(ROOT, 'house', 'realestate')
LOGDIR = os.path.join(OUTDIR, 'logs')

# Windows 控制台 GBK：主进程输出与子进程输出都强制 UTF-8，否则中文/符号会抛异常
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
CHILD_ENV = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')

# 公众号关键词轮换池（每天取 2 个）
KEYWORDS = [
    '苏州 二手房 网签 套数',
    '苏州 新房 库存 去化',
    '苏州 二手房 均价',
    '克而瑞 苏州 市场',
    '土拍网 苏州 月报',
    '苏州 楼市 周报 成交',
]

# 小区抓取轮换池（房天下会限流，每天只抓 2 个板块，缓存逐日累积）
SECTOR_ROTATION = [
    '郭巷', '湖东', '狮山', '元和', '城南', '金阊', '科技城', '沧浪', '平江',
    '双塔', '斜塘', '玲珑', '双湖', '独墅湖', '青剑湖', '高铁新城', '太湖新城',
]


def run(name, cmd, timeout=300):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=timeout,
                           env=CHILD_ENV)
        rc = p.returncode
        out = (p.stdout or b'').decode('utf-8', 'replace')
        err = (p.stderr or b'').decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        rc, out, err = -9, '', f'timeout {timeout}s'
    dt = time.time() - t0
    tail = (out or err).strip().splitlines()
    last = tail[-1][:110] if tail else ''
    print(f'[{name}] rc={rc} {dt:.1f}s  {last}')
    return rc, out, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-wechat', action='store_true')
    ap.add_argument('--skip-sectors', action='store_true')
    ap.add_argument('--skip-communities', action='store_true')
    args = ap.parse_args()

    os.makedirs(LOGDIR, exist_ok=True)
    today = date.today()
    log_path = os.path.join(LOGDIR, f'{today:%Y%m%d}.log')
    lines = [f'==== {datetime.now():%Y-%m-%d %H:%M:%S} daily_pull ====']
    rcs = {}

    py = sys.executable

    print('— 1/6 官方日成交（房管局）')
    rcs['official'] = run('official', [py, os.path.join(HERE, 'snapshot_official.py')])[0]

    print('— 2/6 成交热度监控（CEO 优先项，触发了会推 Windows 通知）')
    rcs['volume'] = run('volume', [py, os.path.join(HERE, 'volume_watch.py'),
                                   '--notify'])[0]

    if args.skip_sectors:
        rcs['sectors'] = 0
    else:
        print('— 3/6 平台板块（房天下，约 25 秒）')
        rcs['sectors'] = run('sectors', [py, os.path.join(HERE, 'scrape_hot_sectors.py')])[0]

    if args.skip_communities:
        rcs['communities'] = 0
    else:
        i = today.toordinal() % len(SECTOR_ROTATION)
        picks = [SECTOR_ROTATION[i], SECTOR_ROTATION[(i + 8) % len(SECTOR_ROTATION)]]
        print(f'— 4/6 小区轮换（{",".join(picks)}）')
        ok = 0
        for s in picks:
            rc = run(f'comm:{s}', [py, os.path.join(HERE, 'scrape_communities.py'),
                                   '--only', s, '--pages', '2'])[0]
            ok += (rc == 0)
            time.sleep(3)
        rcs['communities'] = 0 if ok else 1

    if args.skip_wechat:
        rcs['wechat'] = 0
    else:
        print('— 5/6 公众号索引（搜狗，2 词轮换）')
        idx = today.toordinal() % len(KEYWORDS)
        picks = [KEYWORDS[idx], KEYWORDS[(idx + 3) % len(KEYWORDS)]]
        since = (today - timedelta(days=60)).isoformat()
        ok = 0
        for kw in picks:
            rc = run(f'wechat:{kw[:10]}', [py, os.path.join(HERE, 'wechat_search.py'),
                                           '--pages', '1', '--since', since,
                                           '--save', kw])[0]
            ok += (rc == 0)
            time.sleep(2)
        rcs['wechat'] = 0 if ok == len(picks) else 1

    print('— 6/6 估值筛选 + 单房模型')
    rcs['valuation'] = run('valuation', [py, os.path.join(HERE, 'valuation.py'),
                                         '--screen'])[0]
    rcs['model'] = run('model', [py, os.path.join(HERE, 'deal_model.py')])[0]

    bad = [k for k, v in rcs.items() if v != 0]
    print(f"\n汇总: {'全绿' if not bad else '失败项 ' + ','.join(bad)}  → {log_path}")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines + [json.dumps(rcs, ensure_ascii=False)]))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
