#!/usr/bin/env python3
# orders-arch-certify.py -- orders.md 分卷认证步脚本（D-20261006-02·值守轮 2026-10-05 午处方脚本化）
# 认证判据（全态扫描·治二态扫描不足）：表格行末格终态=executed（纯 executed 或 X→executed 迁移终态）
#   且整格无 部分/撤单/关单 标记，且行首日期 < 2026-10-01（近 2 日 CEO 令恒留活跃卷）
# 字节保真：按 b'\n' 切行原样搬移；--apply 前备份落 .codely-cli/tmp；--dry 仅出认证清单
# 用法：python orders-arch-certify.py --dry | --apply
import sys, re, os

ROOT = r'C:\Users\sjs20\Desktop\FluxGroup'
ORD  = os.path.join(ROOT, 'docs', 'orders.md')
ARC  = os.path.join(ROOT, 'docs', 'orders-archive.md')
BAK  = os.path.join(ROOT, '.codely-cli', 'tmp')
CUTOFF = '10-01'  # 日期 >= 10-01 一律保留
KEEP_MARK = ('部分', '撤单', '关单')

def last_cell(s):
    s = s.rstrip('\r').rstrip()
    if not s.startswith('|') or s.count('|') < 4:
        return None
    if s.endswith('|'):
        i = s.rfind('|', 0, len(s) - 1)
        return s[i + 1:len(s) - 1] if i >= 0 else None
    i = s.rfind('|')
    return s[i + 1:] if i >= 0 else None

def row_date(s):
    m = re.search(r'\|\s*(?:2026-)?(\d{2}-\d{2})', s)
    return m.group(1) if m else None

def terminal_executed(cell):
    if not cell or 'executed' not in cell:
        return False
    for kw in KEEP_MARK:
        if kw in cell:
            return False
    parts = cell.split('→')
    head = parts[0].strip().lstrip('*~').strip()
    tail = parts[-1].strip().lstrip('*~').strip()
    if head.startswith('executed'):
        return True
    return len(parts) > 1 and tail.startswith('executed')

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--dry'
    raw = open(ORD, 'rb').read()
    lines = raw.split(b'\n')
    moved, kept = [], []
    for i, lb in enumerate(lines):
        s = lb.decode('utf-8', 'replace').rstrip('\r')
        cell = last_cell(s)
        if cell is not None:
            d = row_date(s)
            if d is not None and d < CUTOFF and terminal_executed(cell):
                moved.append((i + 1, d, s))
                continue
        kept.append(lb)
    moved_bytes = sum(len(l) + 1 for l in (m[2].encode('utf-8', 'replace') + b'\n' for m in moved))
    # dry report
    print(f'[certify] old={len(raw)}B rows_moved={len(moved)} bytes_moved~={moved_bytes}')
    print(f'[certify] projected_new={len(raw) - moved_bytes}B (line 256,000B) -> {"PASS" if len(raw) - moved_bytes <= 256000 else "FAIL"}')
    for n, d, s in moved:
        head = re.sub(r'\s+', ' ', s)[:96]
        print(f'  L{n} [{d}] {head}')
    if mode != '--apply':
        print('[certify] DRY only -- no write. rerun with --apply')
        return
    os.makedirs(BAK, exist_ok=True)
    bak = os.path.join(BAK, 'orders.md.bak-20261006-0000')
    with open(bak, 'wb') as f:
        f.write(raw)
    new = b'\n'.join(kept)
    with open(ORD, 'wb') as f:
        f.write(new)
    stamp = '2026-10-06 00:00 常务轮（D-20261006-02·值守轮认证步处方承接）'
    hdr = (f'\n## 轮转波二·{stamp}\n\n'
           f'> 认证判据=末格终态 executed 且日期 <2026-10-01·字节保真搬移 {len(moved)} 行/'
           f'{moved_bytes}B·源=docs/orders.md 轮转律（§4.1·orders-archive 范式·波一先例 D-20260930-008②）·'
           f'工具 Tools/orders-arch-certify.py（--dry/--apply）\n\n').encode('utf-8')
    body = b'\n'.join(m[2].encode('utf-8', 'replace') for m in moved) + b'\n'
    with open(ARC, 'ab') as f:
        f.write(hdr + body)
    chk = open(ORD, 'rb').read()
    print(f'[apply] backup={bak}')
    print(f'[apply] orders.md {len(raw)}B -> {len(chk)}B (delta={len(raw)-len(chk)}B vs est {moved_bytes}B)')
    print(f'[apply] archive append {len(hdr)+len(body)}B; rows={len(moved)}')

if __name__ == '__main__':
    main()
