#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_dashboard.py - 机队控制台看板生成器（自动刷新·真实数据）
读取 NATS 心跳/队列/条线状态/产出记录，生成 fleet-console.html。
接入总控脉每轮自动重跑，页面 30s 自动刷新 = 双保险。
"""
import sys, time, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

def _run_contingency():
    """每次刷新前先跑预案引擎（20s 环=预案环，独立于 60s 主控环·双环冗余）"""
    try:
        import fleet_contingency
        fleet_contingency.main()
    except Exception as e:
        print('contingency-skip:', str(e)[:120])

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "fleet-console.html")
names = {'bm-a':'公司生产力','bm-b':'小钢炮','bm-c':'传家宝','bm-m':'MacBook Pro','bm-d':'算力大脑'}
role = {'bm-a':'中枢·装配·夜GPU','bm-b':'声音·TTS·480P','bm-c':'KF·出片·画质','bm-m':'主控·调度·35B','bm-d':'大脑·回测(未装)'}

def main():
    _run_contingency()
    now=int(time.time()*1000); ts=time.strftime('%Y-%m-%d %H:%M:%S')
    hb={}
    for n in ('bm-a','bm-b','bm-c','bm-m','bm-d'):
        s=fl.kv_get('state.'+n)
        if s:
            age=(now-int(s.get('ts_utc_ms') or 0))/1000
            hb[n]={'name':names.get(n,n),'online':age<=900,'age_s':round(age,1),'ram':s.get('ram_free_gb'),'gpu':s.get('gpu_util_pct')}
        else:
            hb[n]={'name':names.get(n,n),'online':False,'age_s':None}
    qf=os.path.join(ROOT,'cph4/fleet/PRODUCTION-QUEUE.jsonl')
    from collections import Counter
    rows=[]
    try:
        rows=fl.read_jsonl(qf)
    except Exception: pass
    q=dict(Counter(r.get('state') for r in rows))
    running=[(r.get('id'),(r.get('title') or '')[:34],r.get('owner'),str(r.get('claimed_at') or '')[:16]) for r in rows if r.get('state')=='RUNNING'][:4]
    failed=[(r.get('id'),(r.get('failure') or '')[:44]) for r in rows if r.get('state')=='FAILED'][:4]
    open_=[(r.get('id'),(r.get('title') or '')[:30]) for r in rows if r.get('state')=='OPEN'][:4]
    lines=[]
    try:
        ms=json.load(open(os.path.join(ROOT,'cph4/fleet/dispatcher/MASTER-STATE.json'),encoding='utf-8-sig'))
        for k,v in (ms.get('lines') or {}).items():
            if v.get('verdict') in ('BLOCKED','STALE'): lines.append((k,v.get('verdict','')))
    except Exception: pass
    rec=os.path.join(ROOT,'cph4/fleet/queue-receipts'); recent=[]
    if os.path.isdir(rec):
        for f in sorted(os.listdir(rec),reverse=True)[:8]:
            if f.endswith(('.md','.json')):
                p=os.path.join(rec,f)
                recent.append((f,time.strftime('%m-%d %H:%M',time.localtime(os.path.getmtime(p)))))
    ht=[]
    try: ht=[l.strip()[:150] for l in open('/tmp/fleet-health.log').readlines()[-2:]]
    except Exception: pass
    cyc=''
    try: cyc=[l for l in open('/tmp/fluxgroup-member.log') if 'MASTER cyc' in l][-1][:110]
    except Exception: pass

    def card(n):
        s=hb.get(n,{}); on=s.get('online',False)
        ram=s.get('ram'); gpu=s.get('gpu'); age=s.get('age_s')
        return f'''<div class="node {'ok' if on else 'dead'}"><div class="nh"><span class="dot"></span><b>{s.get('name',n)}</b><span class="tag">{n}</span></div><div class="nr">{role.get(n,'')}</div><div class="nm"><span>状态 <b>{'在线' if on else '离线'}</b></span><span>心跳 {f'{age:.0f}s' if age is not None else '—'}</span><span>内存 {f'{ram}G' if ram is not None else '—'}</span><span>GPU {f'{gpu}%' if gpu is not None else '—'}</span></div></div>'''
    cards=''.join(card(n) for n in ('bm-a','bm-b','bm-c','bm-m','bm-d'))
    run_html=''.join(f'<li><span class="run">●</span>{i} <span class="dim">· {ow} · {ct}</span></li>' for i,_,ow,ct in running) or '<li class="dim">无运行中</li>'
    line_html=''.join(f'<li><span class="warn">⚠</span>{k} — {v}</li>' for k,v in lines)
    fail_html=''.join(f'<li><span class="warn">●</span>失败 {i}: {f}</li>' for i,f in failed)
    open_html=''.join(f'<li><span class="dim">○</span>待派 {i}</li>' for i,_ in open_[:3])
    rec_html='<br>'.join(f'<span class="dim">{t} · </span>{f}' for f,t in recent[:6])
    online=sum(1 for v in hb.values() if v['online'])
    src=f'数据源：NATS 心跳 / PRODUCTION-QUEUE / MASTER-STATE / queue-receipts（采集 {ts}）'
    html=f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<title>FLUX 机队控制台</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0e16;color:#e3eaf6;font-family:-apple-system,'PingFang SC',sans-serif;padding:26px;max-width:1200px;margin:0 auto}}
.hdr{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:4px}} h1{{font-size:20px}} .sub{{color:#6b7c99;font-size:12px}}
.hero{{display:flex;gap:14px;margin:16px 0 18px}} .hcard{{flex:1;background:#101826;border:1px solid #1f2b42;border-radius:12px;padding:14px 18px}}
.hcard .num{{font-size:30px;font-weight:700}} .hcard .lbl{{font-size:12px;color:#8ea0c0;margin-top:2px}}
.okc .num{{color:#2fd08a}} .war .num{{color:#f5c543}} .der .num{{color:#e5484d}}
.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:18px}}
.node{{background:#101826;border:1px solid #1f2b42;border-radius:12px;padding:13px 15px}}
.node.ok{{border-top:3px solid #2fd08a}} .node.dead{{border-top:3px solid #e5484d;opacity:.8}}
.nh{{display:flex;align-items:center;gap:8px;font-size:14px}} .dot{{width:8px;height:8px;border-radius:50%;background:#2fd08a}} .dead .dot{{background:#e5484d}}
.tag{{margin-left:auto;font-size:10px;color:#7a8aa5;background:#19233a;padding:2px 7px;border-radius:20px}}
.nr{{color:#7a8aa5;font-size:11px;margin:6px 0 9px}} .nm{{font-size:11px;color:#aeb9cd;display:flex;flex-wrap:wrap;gap:4px 12px}} .nm b{{color:#fff}}
.panels{{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:12px}}
.panel{{background:#101826;border:1px solid #1f2b42;border-radius:12px;padding:14px 16px}} h2{{font-size:13px;color:#8ea0c0;margin-bottom:10px;font-weight:600}}
.kpi{{display:flex;gap:22px;margin-bottom:10px}} .kpi b{{font-size:24px;color:#fff;display:block}} .kpi span{{font-size:11px;color:#8ea0c0}}
li{{list-style:none;font-size:12.5px;padding:4px 0;border-bottom:1px dashed #1c2740}} .run{{color:#2fd08a}} .warn{{color:#f5c543}} .dim{{color:#7a8aa5;font-size:11px}}
.mono{{font-family:Menlo,monospace;font-size:10.5px;color:#7a8aa5;line-height:1.9;word-break:break-all}}
.src{{color:#56647f;font-size:10.5px;margin-top:14px;border-top:1px solid #1c2740;padding-top:8px}}
</style></head><body>
<div class="hdr"><h1>⚡ FLUX 机队控制台</h1><div class="sub">每 30s 自动刷新 · {ts}</div></div>
<div class="hero">
  <div class="hcard okc"><div class="num">{online}/5</div><div class="lbl">节点在线 · MacBook Pro 主控值守</div></div>
  <div class="hcard war"><div class="num">{len(lines)}</div><div class="lbl">阻塞/停摆条线</div></div>
  <div class="hcard okc"><div class="num">{q.get('RUNNING',0)}</div><div class="lbl">任务运行中</div></div>
  <div class="hcard der"><div class="num">{q.get('FAILED',0)}</div><div class="lbl">失败任务</div></div>
  <div class="hcard"><div class="num">{q.get('DONE',0)}</div><div class="lbl">累计完成</div></div>
</div>
<div class="grid">{cards}</div>
<div class="panels">
  <div class="panel"><h2>⚠ 需关注</h2><ul>{line_html or '<li class=dim>无阻塞/停摆条线</li>'}{fail_html}{open_html}</ul></div>
  <div class="panel"><h2>▶ 运行中</h2><ul>{run_html}</ul><div class="kpi" style="margin-top:8px"><div><b>{q.get('DONE',0)}</b><span>完成</span></div><div><b>{q.get('OPEN',0)}</b><span>待派</span></div><div><b>{q.get('RUNNING',0)}</b><span>运行</span></div></div></div>
  <div class="panel"><h2>📦 最近产出</h2><div style="font-size:12px;line-height:2">{rec_html}</div></div>
</div>
<div class="mono" style="margin-top:12px;background:#0d1320;border:1px solid #1c2740;border-radius:10px;padding:10px 14px"><b style="color:#8ea0c0">主控脉（最近调度轮）</b><br>{cyc or '—'}<br><br>{ht[0] if ht else ''}<br>{ht[1] if len(ht)>1 else ''}</div>
<div class="src">{src}</div>
</body></html>'''
    with open(OUT,'w',encoding='utf-8') as f: f.write(html)
    print('dashboard ok %s online=%d/5' % (ts, online))

if __name__ == '__main__':
    main()
