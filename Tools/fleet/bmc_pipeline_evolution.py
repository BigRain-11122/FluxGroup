# -*- coding: utf-8 -*-
"""bmc_pipeline_evolution.py - bm-c 产线自进化哨 v1（CEO 令 2026-11-22:
生成流程和管线要根据需求和市场变化不断迭代更新、不断反审）

四环循环（每 6h 一轮）：
  环1 市场脉动：扫头部平台当期判据（政策/形态/成本标杆）是否与我方正典漂移
  环2 产线反审：读 ProductionRouter 回执+夜批回执+板审结果，统计卡点/慢点/判负模式
  环3 提案生成：漂移或病灶 → 生成 PIPELINE-CHANGE-PROPOSAL 草案（不改法，只提案）
  环4 留痕上报：写 cph4/fleet/queue-receipts/pipeline-evolution-bm-c.json（主控+导演席可见）

纪律：本哨只观测与提案，不擅自改正典（改法走导演席/委员会通道）。
"""
import json, os, glob, datetime, re

REPO = r'K:\Fluxgroup\FluxGroup'
RECEIPTS = os.path.join(REPO, r'cph4\fleet\queue-receipts')
OUT = os.path.join(RECEIPTS, 'pipeline-evolution-bm-c.json')
CANON = {
    'drama_v3': os.path.join(REPO, r'cph4\fleet\drama-dept-v1\DRAMA-v3-20261122.md'),
    'heroine_factory': r'K:\Fluxgroup\.codely-cli\tmp\heroine_lora_factory.py',
    'production_router': os.path.join(REPO, r'Tools\fleet\bmc_production_router.py'),
}

def read_json(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return None

def canon_freshness():
    """正典文件的 mtime 新鲜度（天）"""
    out = {}
    for k, p in CANON.items():
        if os.path.exists(p):
            age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() / 86400
            out[k] = round(age_days, 1)
        else:
            out[k] = None
    return out

def router_signals():
    """从 ProductionRouter 回执抽最近态：卡点/慢速计数"""
    r = read_json(os.path.join(RECEIPTS, 'production-router-bm-c.json'))
    if not r:
        return None
    return {
        'ts': r.get('ts'), 'stalls': r.get('stalls', []),
        'throughput': r.get('throughput', {}), 'plan': r.get('plan'),
    }

def batch_receipts_latest(n=5):
    """最近 n 份 autodrive/night 回执（产出效率证据）"""
    files = sorted(glob.glob(os.path.join(RECEIPTS, '*bm-c*.json')), key=os.path.getmtime, reverse=True)
    out = []
    for f in files[:n]:
        d = read_json(f)
        if d:
            out.append({'file': os.path.basename(f), 'ts': d.get('ts'), 'name': d.get('name')})
    return out

def detect_issues():
    issues = []
    rs = router_signals()
    if rs:
        if rs['stalls']:
            issues.append({'kind': 'router-stall', 'detail': rs['stalls']})
        tp = rs.get('throughput', {})
        for k, v in tp.items():
            if isinstance(v, int) and v < 2 and 'last10min' in k:
                issues.append({'kind': 'slow-throughput', 'lane': k, 'rate': v})
    cf = canon_freshness()
    for k, age in cf.items():
        if age is not None and age > 14:
            issues.append({'kind': 'canon-stale', 'which': k, 'age_days': age})
    return issues

def main():
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    issues = detect_issues()
    proposals = []
    for i in issues:
        if i['kind'] == 'canon-stale':
            proposals.append(f"[proposal] {i['which']} 正典已 {i['age_days']} 天未动——安排市场脉动复扫（环1）+是否需 v+1 迭代")
        elif i['kind'] == 'router-stall':
            proposals.append(f"[proposal] 产线卡点 {i['detail']}——按 ProductionRouter 备道接续并复盘卡因（工艺/参数/通道）")
        elif i['kind'] == 'slow-throughput':
            proposals.append(f"[proposal] 车道 {i['lane']} 出货 {i['rate']}/10min 偏慢——优化等待参数或换更快的生成通道")
    report = {
        'ts': now, 'node': 'bm-c', 'kind': 'pipeline-evolution',
        'cycle': '6h', 'canon_age_days': canon_freshness(),
        'router_signals': router_signals(),
        'recent_receipts': batch_receipts_latest(),
        'issues': issues, 'proposals': proposals,
        'note': 'observation+proposal only; canon changes go through director/council channel',
    }
    os.makedirs(RECEIPTS, exist_ok=True)
    tmp = OUT + '.tmp'
    json.dump(report, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print(f"[evolution] {now} issues={len(issues)} proposals={len(proposals)}")
    for p in proposals:
        print('  ' + p)

if __name__ == '__main__':
    main()
