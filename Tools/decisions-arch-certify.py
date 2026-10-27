#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decisions.md 分卷认证搬移器（Step2 段级分卷·D-20261006-04）
法源：D-20261003-04 两步路线 + D-20261006-02 orders 波二同法（Tools/orders-arch-certify.py 范式）
认证判据：末格 executed 终态 + 日期 <2026-10-04 + 字节保真搬移 + 备份 + 对账断言
随批证据化翻面：D-20261002-02/03/05/08 + D-20261004-02（板面漂移·依据=D-20261005-02①/D-20261004-05①/D-20261005-11/D-20261006-05①）
"""
import os, re, sys, shutil

ROOT = r'C:\Users\sjs20\Desktop\FluxGroup'
SRC = os.path.join(ROOT, 'docs', 'decisions.md')
ARC = os.path.join(ROOT, 'docs', 'decisions-archive.md')
BAK = os.path.join(ROOT, '.codely-cli', 'tmp', 'decisions.md.bak-20261006-1200')
CUTOFF = '2026-10-04'
THRESH = 204800
FLIPS = {
    'D-20261002-02': 'executed（补呈窗 10-05 00:00 窗内回执核销·D-20261005-02①）',
    'D-20261002-03': 'executed（补呈窗 10-05 00:00 窗内回执核销·D-20261005-02①）',
    'D-20261002-05': 'executed（D-20261004-05① 核销·跳位钉死行双机在册回执窗内）',
    'D-20261002-08': 'executed（初稿出具 D-20261005-11·席7 窗内沉默转正 D-20261006-05④）',
    'D-20261004-02': 'executed（①②③ D-20261005-02② 提前闭口+④ keepwarm 翻档实读核销 D-20261006-05①·全四项毕）',
}
POINTER = '——已整段迁 docs/decisions-archive.md（终态认证·2026-10-06 分卷波一·D-20261006-04）'
NOTE = '> 注：终态 executed 行（日期 <2026-10-04）已字节保真迁 docs/decisions-archive.md（2026-10-06 分卷波一·D-20261006-04·备份 .codely-cli/tmp/decisions.md.bak-20261006-1200）'

row_re = re.compile(r'^\| (2026-\d\d-\d\d) \|')
id_re = re.compile(r'^(D-\d{8}-\d+)')

raw = open(SRC, 'rb').read()
text = raw.decode('utf-8')
eol = '\r\n' if '\r\n' in text else '\n'
lines = text.splitlines(keepends=True)
os.makedirs(os.path.dirname(BAK), exist_ok=True)
shutil.copy2(SRC, BAK)

moved, flips_done, out = [], [], []
for ln in lines:
    s = ln.strip()
    if s.startswith('|'):
        cells = s.split('|')
        c1 = cells[1].strip() if len(cells) > 1 else ''
        c2 = cells[2].strip() if len(cells) > 2 else ''
        title = c2 if re.match(r'^2026-', c1) else c1
        m_id = id_re.match(title)
        dnum = m_id.group(1) if m_id else ''
        status = cells[-2].strip() if len(cells) >= 3 else ''
        if dnum in FLIPS and status.startswith('dispatched'):
            idx = ln.rfind(status)
            if idx == -1:
                print('FLIP-FAIL(rfind): ' + dnum); sys.exit(2)
            ln = ln[:idx] + FLIPS[dnum] + ln[idx + len(status):]
            s = ln.strip()
            cells = s.split('|')
            status = cells[-2].strip()
            flips_done.append(dnum)
        m = row_re.match(s)
        if m and m.group(1) < CUTOFF and status.startswith('executed'):
            moved.append(ln)
            continue
    out.append(ln)

assert set(flips_done) == set(FLIPS), 'flips missing: %s' % (set(FLIPS) - set(flips_done))
assert len(moved) >= 40, 'moved rows too few: %d' % len(moved)
moved_bytes = sum(len(l.encode('utf-8')) for l in moved)
for l in moved:
    assert l.strip().split('|')[-2].strip().startswith('executed'), 'non-executed row moved: ' + l[:80]

# 孤段收口：搬空后零日期行的「## 台账·…批…」段→指针行
res, orphan = [], []
i = 0
while i < len(out):
    ln = out[i]
    if ln.lstrip().startswith('## 台账·'):
        j = i + 1
        while j < len(out) and not out[j].lstrip().startswith('#'):
            j += 1
        if not any(row_re.match(l.strip()) for l in out[i:j]):
            res.append(ln.rstrip('\r\n') + POINTER + eol)
            orphan.append(ln.strip())
            i = j
            continue
    res.append(ln)
    i += 1
out = res

# 旧主段（### 台账）注记行：插在段头后首个表分隔行之后
ins = False
for k, ln in enumerate(out):
    if ln.strip() == '### 台账':
        m2 = k + 1
        while m2 < len(out) and not out[m2].strip().startswith('|---'):
            m2 += 1
        if m2 < len(out):
            out.insert(m2 + 1, NOTE + eol)
            ins = True
        break
if not ins:
    print('WARN: ### 台账 note not inserted')

final_bytes = sum(len(l.encode('utf-8')) for l in out)
print('moved_rows=%d moved_bytes=%d flips=%d orphan_segments=%s final_bytes=%d' % (
    len(moved), moved_bytes, len(flips_done), len(orphan), final_bytes))
if final_bytes > THRESH:
    print('ABORT: final size over threshold %d' % THRESH); sys.exit(3)

arc_text = open(ARC, 'rb').read().decode('utf-8') if os.path.exists(ARC) else ('# Decisions Archive —— 集团决策台账分卷归档（orders-archive 范式·字节保真·git 全量可溯）' + eol)
arc_add = (eol + '## 迁移批次·2026-10-06 12:00 常务轮（decisions.md 分卷波一·D-20261006-04）' + eol + eol +
           '> 溯源：docs/decisions.md（认证=末格 executed 终态+日期 <2026-10-04；随批翻面 D-20261002-02/03/05/08+D-20261004-02；整段迁段：' +
           '；'.join(orphan) + '；字节保真搬移 %d 行 %d B；备份 .codely-cli/tmp/decisions.md.bak-20261006-1200）' + eol + eol +
           ''.join(moved))
open(SRC, 'wb').write(''.join(out).encode('utf-8'))
open(ARC, 'ab').write(arc_add.encode('utf-8'))
print('WRITTEN: decisions.md=%dB archive+=%dB' % (os.path.getsize(SRC), len(arc_add.encode('utf-8'))))
