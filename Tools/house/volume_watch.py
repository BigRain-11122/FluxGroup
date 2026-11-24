# -*- coding: utf-8 -*-
"""
日成交量热度监控（CEO 令 2026-11-16：尤其要监控日成交量，热度起来要及时通知）。

口径（必须先说清，否则报警必是假警）：
  · 指标 = 房管局「六区二手住宅」日成交套数（res_units），不用含商办的总套数。
  · 只认「日终档」：采集时刻 ≥ 21:30。盘中值（如 16:42）与日终值差 15%~25%，
    混用会天天误报。当日若只有盘中档 → 标 INTRADAY，不进基线、不参与判定。
  · 基线 = 近 N 日（默认 20）中位数。用中位数不用均值，抗单日异常。
  · 周内效应：周末网签本就少，中位数基线能吸收大部分；周一/周六单列在输出里提示。

三条告警（任一触发）：
  A 单日突破：今日 ≥ 基线 × 1.60
  B 趋势抬升：近 5 日均值 ≥ 前 20 日均值 × 1.30
  C 连续高位：连续 3 日 ≥ 基线 × 1.25

冷却：同类告警 3 日内不重复（写 alerts-log.jsonl 判重）。
基线不足（<8 个日终档）：只记录不告警，输出「建设中 X/8」。

用法：
    python Tools/house/volume_watch.py                # 只算+打印
    python Tools/house/volume_watch.py --notify        # 触发时发 Windows 通知
    python Tools/house/volume_watch.py --self-test
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')
DAILY = os.path.join(RE, 'official-daily.jsonl')
ALERTS_DIR = os.path.join(RE, 'alerts')
ALERTS_LOG = os.path.join(ALERTS_DIR, 'alerts-log.jsonl')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

FINAL_TS = '21:30'          # 该时刻及之后算日终档
MIN_BASE = 8                # 基线最少天数
N_BASE = 20


# ---------------- 数据 ----------------
def load_series(path=DAILY):
    """返回 [{date, ts, res, units, final: bool}]，按日期升序。"""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            sh = (r.get('secondhand') or {}).get('total') or {}
            res = sh.get('res_units')
            if not res:
                continue
            ts = r.get('ts') or '00:00'
            out.append(dict(date=r.get('date'), ts=ts, res=int(res),
                            units=int(sh.get('units') or 0),
                            final=ts >= FINAL_TS))
    out.sort(key=lambda x: x['date'])
    return out


# ---------------- 判定（纯函数，便于自检） ----------------
def evaluate(series, n_base=N_BASE, min_base=MIN_BASE, k_spike=1.60,
             k_trend=1.30, k_streak=1.25, streak_days=3,
             cooldown_days=3, fired=(), today=None):
    """
    series: load_series() 的输出
    fired:  已发过的 [(type, date_str)]，用于冷却
    返回 dict(status, baseline, today_row, ratio, alerts, note)
    """
    if not series:
        return dict(status='NO-DATA', baseline=None, today_row=None, ratio=None,
                    alerts=[], note='official-daily.jsonl 空，先跑 snapshot_official.py')

    today_row = series[-1]
    if today is not None and today_row['date'] != today:
        today_row = dict(date=today, ts='—', res=0, units=0, final=False)

    # 基线池 = 除今日外的日终档
    pool = [r for r in series[:-1] if r['final']]
    res_pool = [r['res'] for r in pool]

    base = statistics.median(res_pool) if res_pool else None
    need = max(0, min_base - len(res_pool))

    alerts = []
    note = ''
    ratio = None

    if base:
        ratio = today_row['res'] / base

    if len(res_pool) < min_base:
        note = f'基线建设中 {len(res_pool)}/{min_base} 日终档（还差 {need} 天），只记录不告警'
        status = 'WARMUP'
    elif not today_row['final']:
        note = f"今日为盘中档（{today_row['ts']}），与日终档不可比，本次不判定"
        status = 'INTRADAY'
    else:
        status = 'OK'
        if ratio is not None and ratio >= k_spike:
            alerts.append(dict(type='A_spike', ratio=ratio,
                               msg=f"单日突破：{today_row['res']} 套 = 基线 {base:.0f} 的 {ratio:.2f} 倍（阈值 {k_spike}）"))
        if len(res_pool) >= n_base:
            last5 = [r['res'] for r in pool[-5:]] if len(pool) >= 5 else None
            prev20 = [r['res'] for r in pool[-25:-5]] if len(pool) >= 25 else res_pool
            if last5:
                m5, m20 = statistics.mean(last5), statistics.mean(prev20)
                if m20 and m5 / m20 >= k_trend:
                    alerts.append(dict(type='B_trend', ratio=m5 / m20,
                                       msg=f"趋势抬升：近 5 日均 {m5:.0f} 套 = 前 20 日均 {m20:.0f} 的 {m5/m20:.2f} 倍（阈值 {k_trend}）"))
        if len(pool) >= streak_days:
            streak = [r['res'] for r in pool[-(streak_days - 1):]] + [today_row['res']]
            if all(x >= base * k_streak for x in streak):
                alerts.append(dict(type='C_streak', ratio=min(streak) / base,
                                   msg=f"连续高位：连续 {streak_days} 日 ≥ 基线 {base:.0f} 的 {k_streak} 倍"
                                       f"（{[int(x) for x in streak]}）"))

    # 冷却
    kept = []
    for a in alerts:
        recent = [d for t, d in fired if t == a['type']]
        if recent:
            last = max(recent)
            if (date.fromisoformat(today_row['date']) - date.fromisoformat(last)).days < cooldown_days:
                a['suppressed'] = True
                note = (note + '；' if note else '') + f"{a['type']} 在冷却期内（上次 {last}）"
                continue
        kept.append(a)

    return dict(status=status, baseline=base, today_row=today_row, ratio=ratio,
                alerts=kept, note=note, pool_n=len(res_pool))


# ---------------- 通知 ----------------
def _ps_lit(s):
    """
    PowerShell 单引号字面量。必须自己转义，不能用 json.dumps：
    json 只转义 ASCII 引号，而 PowerShell 把中文引号 “ ” 也当字符串分隔符，
    正文里一旦带中文引号就会把脚本截断（本轮实测踩过，表现为静默 rc=1）。
    """
    s = (s.replace('\u201c', '\u0022').replace('\u201d', '\u0022')
          .replace('\u2018', "'").replace('\u2019', "'")
          .replace('\r', ' ').replace('\n', ' '))
    return "'" + s.replace("'", "''") + "'"


def toast(title, body):
    """Windows 通知。用 CREATE_NO_WINDOW 避免黑窗闪。"""
    ps = '\n'.join([
        "$ErrorActionPreference='Stop'",
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null",
        "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)",
        "$x=$t.GetElementsByTagName('text')",
        f"$x.Item(0).AppendChild($t.CreateTextNode({_ps_lit(title)})) | Out-Null",
        f"$x.Item(1).AppendChild($t.CreateTextNode({_ps_lit(body)})) | Out-Null",
        "$n=[Windows.UI.Notifications.ToastNotification]::new($t)",
        "$appid='{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'",
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appid).Show($n)",
    ])
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    try:
        p = subprocess.run(['powershell.exe', '-NoProfile', '-Command', ps],
                           capture_output=True, timeout=25,
                           creationflags=flags)
        return p.returncode == 0
    except Exception:
        return False


def fired_pairs(path=ALERTS_LOG, days=60):
    if not os.path.exists(path):
        return []
    out = []
    cut = (date.today() - timedelta(days=days)).isoformat()
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get('date', '') >= cut:
                out.append((r.get('type'), r.get('date')))
    return out


def record(result, notified):
    os.makedirs(ALERTS_DIR, exist_ok=True)
    tr = result['today_row']
    rec = dict(date=tr['date'], ts=tr['ts'], res=tr['res'],
               baseline=result['baseline'], ratio=result['ratio'],
               status=result['status'], notified=notified,
               alerts=[a['type'] for a in result['alerts']],
               note=result.get('note', ''))
    with open(ALERTS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    if result['alerts']:
        p = os.path.join(ALERTS_DIR, f"ALERT-{tr['date']}.md")
        with open(p, 'w', encoding='utf-8') as f:
            f.write(f"# 成交热度告警 {tr['date']}\n\n")
            f.write(f"- 二手住宅成交：**{tr['res']} 套**（{tr['ts']}）\n")
            f.write(f"- 基线（近 20 日终档中位）：{result['baseline']:.0f} 套\n")
            f.write(f"- 今日 / 基线：**{result['ratio']:.2f} 倍**\n\n")
            for a in result['alerts']:
                f.write(f"- [{a['type']}] {a['msg']}\n")
            f.write('\n## 怎么读这个告警\n\n')
            f.write('成交量抬头是**流动性恢复**的信号，但**不等于涨价**——也可能是"以价换量"。\n'
                    '所以动作是：立刻去看目标房源的报价有没有跟涨，而不是马上追价。\n'
                    '价格方向要等月度机构数据（克而瑞/中指院）确认。\n')
        return p
    return None


# ---------------- 自检 ----------------
def _mk(dates, res_list, final=True, ts='22:30'):
    return [dict(date=d, ts=ts, res=r, units=r, final=final)
            for d, r in zip(dates, res_list)]


def self_test():
    ok = True
    days = [(date(2026, 10, 1) + timedelta(days=i)).isoformat() for i in range(40)]

    def check(name, cond, extra=''):
        nonlocal ok
        print(('[ok] ' if cond else '[FAIL] ') + name + (f'  {extra}' if extra else ''))
        ok = ok and cond

    # 1) 平稳序列不报警
    s = _mk(days, [200, 210, 195, 205, 215, 200, 190] * 6)
    r = evaluate(s)
    check('平稳序列不报警', r['status'] == 'OK' and not r['alerts'],
          f"status={r['status']} alerts={[a['type'] for a in r['alerts']]}")

    # 2) 单日突破 1.6x
    s2 = _mk(days[:-1], [200] * 39) + _mk([days[-1]], [340])
    r2 = evaluate(s2)
    check('单日 340/200=1.70 触发 A', any(a['type'] == 'A_spike' for a in r2['alerts']))

    # 3) 1.5x 不该触发 A（1.5 < 1.6）
    s3 = _mk(days[:-1], [200] * 39) + _mk([days[-1]], [300])
    r3 = evaluate(s3)
    check('单日 1.50 倍不触发 A', not any(a['type'] == 'A_spike' for a in r3['alerts']))

    # 4) 趋势抬升：近5日 280 vs 前20日 200
    s4 = _mk(days[:-5], [200] * 35) + _mk(days[-5:], [280] * 5)
    r4 = evaluate(s4)
    check('近5日/前20日=1.40 触发 B', any(a['type'] == 'B_trend' for a in r4['alerts']))

    # 5) 连续 3 日高位（各 1.25x）
    s5 = _mk(days[:-3], [200] * 37) + _mk(days[-3:], [260] * 3)
    r5 = evaluate(s5)
    check('连续 3 日 1.30 倍触发 C', any(a['type'] == 'C_streak' for a in r5['alerts']))

    # 6) 基线不足不告警
    s6 = _mk(days[:5], [200] * 4) + _mk([days[5]], [500])
    r6 = evaluate(s6)
    check('基线 4/8 时只记录不告警', r6['status'] == 'WARMUP' and not r6['alerts'],
          f"status={r6['status']}")

    # 7) 盘中档不判定
    s7 = _mk(days[:-1], [200] * 39) + _mk([days[-1]], [400], final=False, ts='16:42')
    r7 = evaluate(s7)
    check('盘中档不判定', r7['status'] == 'INTRADAY' and not r7['alerts'])

    # 8) 冷却期抑制
    s8 = _mk(days[:-1], [200] * 39) + _mk([days[-1]], [340])
    fired = [('A_spike', days[-2])]
    r8 = evaluate(s8, fired=fired)
    check('冷却期内 A 被抑制', not any(a['type'] == 'A_spike' for a in r8['alerts']),
          f"note={r8.get('note', '')[:40]}")

    print('\nSELF-TEST', 'PASS 8/8' if ok else 'FAIL')
    return 0 if ok else 1


# ---------------- 主流程 ----------------
def reference_level():
    """统计基线还没攒够时的参考水平：10 月机构口径 ÷ 24 个有效交易日。"""
    try:
        with open(os.path.join(RE, 'baselines.json'), encoding='utf-8') as f:
            b = json.load(f)
        m = b['market']
        units = m['secondhand_monthly_units']['v']
        return dict(daily=units / 24, monthly=units,
                    src=m['secondhand_monthly_units']['src'])
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--notify', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--force', action='store_true', help='忽略冷却，用于验证通道')
    ap.add_argument('--test-notify', action='store_true', help='发一条标注过的测试通知')
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if args.test_notify:
        ok = toast('地产热度监控 · 通道测试',
                   '这条是测试。真触发时才推：日成交量异常时会写"成交热度告警"。')
        print(f'测试通知：{"已发送" if ok else "失败"}')
        return 0 if ok else 1

    series = load_series()
    res = evaluate(series, fired=() if args.force else fired_pairs())
    tr = res['today_row']

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        return

    print('=' * 58)
    print(f"二手住宅日成交监控 · {tr['date']} {tr['ts']}")
    print('=' * 58)
    print(f"今日：{tr['res']} 套（总套数含商办 {tr['units']}）")
    ref = reference_level()
    if ref:
        print(f"参考水平：{ref['daily']:.0f} 套/日（10 月机构口径 {ref['monthly']:,} 套 ÷ 24 交易日）")
    if res['baseline']:
        print(f"统计基线：{res['baseline']:.0f} 套／日（近 {res.get('pool_n', 0)} 个日终档中位）")
        print(f"今日/基线：{res['ratio']:.2f} 倍")
    else:
        print('统计基线：暂无')
    print(f"状态：{res['status']}")
    if res.get('note'):
        print(f"说明：{res['note']}")
    if res['alerts']:
        print('\n⚠ 告警：')
        for a in res['alerts']:
            print(f"  · {a['msg']}")
    else:
        print('\n无告警。')

    notified = False
    if args.notify and res['alerts']:
        body = f"{tr['res']} 套 / 基线 {res['baseline']:.0f} = {res['ratio']:.2f} 倍。" \
               f"{res['alerts'][0]['msg'][:60]}"
        notified = toast('地产成交热度告警', body)
        print(f"\n通知已发送：{'是' if notified else '否（通道失败，已落告警文件）'}")

    p = record(res, notified)
    if p:
        print(f'告警文件：{p}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
