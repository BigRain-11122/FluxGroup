# -*- coding: utf-8 -*-
"""
地产线 · 专家团判据执行器 v1
读：judgment-rubric-v1.json（判据库）+ metrics-*.json（房源实测值）
出：分层得分、加权总分、否决项、未测项、证据置信度、可证伪条件

三态判定（这是严谨性的核心）：
  pass   通过
  fail   不通过
  unknown 未测 —— 不计入得分，但会列进"必须核实"，否决项未测=阻断
运行：python Tools/house/panel_review.py [metrics.json]
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RUBRIC = os.path.join(ROOT, 'house', 'realestate', 'judgment-rubric-v1.json')
DEFAULT_METRICS = os.path.join(ROOT, 'house', 'realestate', 'metrics-20261116-yunjiaoyuan.json')


def judge(item, v):
    if v is None:
        return 'unknown'
    op, th = item['op'], item['threshold']
    try:
        if item['type'] == 'num':
            v = float(v)
            if op == '>=':
                return 'pass' if v >= th else 'fail'
            if op == '<=':
                return 'pass' if v <= th else 'fail'
            if op == 'band':
                return 'pass' if th[0] <= v <= th[1] else 'fail'
        elif item['type'] == 'cat':
            if op == 'in':
                return 'pass' if v in th else 'fail'
            if op == 'eq':
                return 'pass' if v == th else 'fail'
        elif item['type'] == 'bool':
            return 'pass' if bool(v) == bool(th) else 'fail'
    except Exception:
        return 'unknown'
    return 'unknown'


def fmt(v):
    if v is None:
        return '未测'
    if isinstance(v, bool):
        return '是' if v else '否'
    if isinstance(v, float):
        return f'{v:g}'
    return str(v)


def main():
    mpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_METRICS
    rubric = json.load(open(RUBRIC, encoding='utf-8'))
    metrics = json.load(open(mpath, encoding='utf-8'))
    vals = metrics['values']
    notes = metrics.get('notes', {})
    conf_map = {k: v['confidence'] for k, v in rubric['evidence_scale'].items()}

    print(f"专家团评审 {rubric['version']}")
    print(f"标的：{metrics['subject']}\n")

    total_num = total_den = 0.0
    pass_w = tested_w = all_w = 0.0
    conf_num = conf_den = 0.0
    veto_fail, veto_unknown, unknowns = [], [], []

    for layer in rubric['layers']:
        print(f"— {layer['name']}（层权重 {layer['weight']}%）")
        num = den = 0.0
        for it in layer['items']:
            v = vals.get(it['id'])
            st = judge(it, v)
            w = it['weight']
            all_w += w
            mark = {'pass': '过', 'fail': '否', 'unknown': '未测'}[st]
            line = f"  {it['id']} {it['name']:<22} {fmt(v):>10} {mark:>4}  (权重{w}, 证据{it['evidence']})"
            if st == 'unknown' and notes.get(it['id']):
                line += f"  ← {notes[it['id']]}"
            print(line)
            if st != 'unknown':
                den += w
                tested_w += w
                if st == 'pass':
                    num += w
                    pass_w += w
                conf_num += w * conf_map[it['evidence']]
                conf_den += w
            else:
                unknowns.append((it['id'], it['name'], it['veto']))
                if it['veto']:
                    veto_unknown.append((it['id'], it['name']))
            if it['veto'] and st == 'fail':
                veto_fail.append((it['id'], it['name'], fmt(v), it['threshold']))
        layer_score = (num / den * 100) if den else 0
        print(f"  → 层得分 {layer_score:.1f}（已测权重 {den:.0f}）\n")
        total_num += layer_score * layer['weight'] / 100
        total_den += layer['weight'] if den else 0

    print('=' * 60)
    conservative = pass_w / all_w * 100 if all_w else 0
    tested_rate = pass_w / tested_w * 100 if tested_w else 0
    coverage = tested_w / all_w if all_w else 0
    print(f'保守分（未测按 0 计）：{conservative:.1f} / 100   ← 定级用这个')
    print(f'已测通过率：{tested_rate:.1f}%（仅在已测项内计算，仅供参考）')
    print(f'覆盖率：{coverage*100:.0f}%（已测权重 {tested_w:.0f} / 总权重 {all_w:.0f}）')
    conf = (conf_num / conf_den) if conf_den else 0
    print(f'证据置信度：{conf*100:.0f}%  （A=1.0 / B=0.75 / C=0.5 加权）')

    if veto_fail:
        print('\n[一票否决] 以下项不通过：')
        for i, n, v, th in veto_fail:
            print(f'  ✗ {i} {n}：实测 {v}，要求 {th}')
    if veto_unknown:
        print('\n[阻断] 以下否决项未测，签约前必须核实：')
        for i, n in veto_unknown:
            print(f'  ? {i} {n}')
    if unknowns:
        print(f'\n未测项 {len(unknowns)} 条（不计分，须补测）：')
        for i, n, _ in unknowns:
            print(f'  - {i} {n}')

    # 评级（严格版：覆盖率不足或否决项未测，不给 A/B）
    if veto_fail:
        grade = 'D（否决）'
    elif veto_unknown:
        grade = 'PENDING（否决项未测，不得签约）'
    elif coverage < 0.80:
        grade = 'C（覆盖率不足 80%，结论不可靠）'
    elif conservative >= 80 and conf >= 0.85:
        grade = 'A（可执行）'
    elif conservative >= 70:
        grade = 'B（谨慎可执行）'
    elif conservative >= 60:
        grade = 'C（观察/需补测）'
    else:
        grade = 'D（否决）'
    print(f'\n评级：{grade}')

    print('\n可证伪条件（出现任一，结论作废重判）：')
    print('  1. 同面积段成交中位低于 13,500（价格锚下移）')
    print('  2. 苏州新房去化周期超过 36 个月')
    print('  3. 物业书面禁止分租（改造方案失效）')
    print('  4. 产证附图与图示户型不一致')
    print('  5. 商贷利率回升至 4.0% 以上')

    out = {
        'subject': metrics['subject'], 'rubric': rubric['version'],
        'conservative_score': round(conservative, 1),
        'tested_pass_rate': round(tested_rate, 1),
        'coverage': round(coverage, 3),
        'confidence': round(conf, 3), 'grade': grade,
        'veto_fail': veto_fail, 'veto_unknown': veto_unknown,
        'unknowns': [{'id': i, 'name': n} for i, n, _ in unknowns],
    }
    p = os.path.join(ROOT, 'house', 'realestate', 'panel-review-20261116.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n已写出 {p}')


if __name__ == '__main__':
    main()
