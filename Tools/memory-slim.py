# -*- coding: utf-8 -*-
"""memory-slim.py — CODELY.md 记忆件无损压缩器（C-20260930-05 长判例下钻律执法件）

法：条目 >400 字 → 全文逐字节保真下钻 <同域>/.codely-cli/memory/mem-<日期>-<序号>.md，
原位留一行指针（原时间戳+一句话判读+档名）。零删改·字节对账·压缩前后报表。
用法：
  python Tools/memory-slim.py --dry   # 演练（只报数不动盘）
  python Tools/memory-slim.py --run   # 实压（备份→压缩→对账→报表）
  python Tools/memory-slim.py --audit # 体量帽审计（法条②执法面·周轮可复用）
"""
import io, os, re, sys, shutil, datetime

ROOT = r'C:\Users\sjs20\Desktop\FluxGroup'
GLOBAL = r'C:\Users\sjs20\.codely-cli\CODELY.md'
BACKUP = os.path.join(ROOT, '.codely-cli', 'tmp', 'memory-slim-backup-%s' % datetime.date.today().strftime('%Y%m%d'))
LIMIT = 400           # 长判例下钻律：>400 字
CAP = 30 * 1024       # 体量帽律：单件 ≤30KB
SKIP_DIRS = {'.git', 'Library', 'Temp', '__pycache__', 'node_modules', 'auto-saves', 'retention'}
DATE = datetime.date.today().strftime('%Y%m%d')

def find_codely_files():
    files = [GLOBAL]
    for dirpath, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if any(seg in dirpath for seg in ('.codely-cli',)):  # 不入各域 .codely-cli 内部找
            dirs[:] = []
            continue
        for f in fs:
            if f == 'CODELY.md':
                files.append(os.path.join(dirpath, f))
    return files

def parse_entries(text):
    """返回 (行列表, 条目行号集)——条目=以 '- [' 开头的单行块。"""
    lines = text.splitlines(keepends=False)
    ent = [i for i, l in enumerate(lines) if l.lstrip().startswith('- [')]
    return lines, ent

def digest(entry_text, limit=90):
    t = re.sub(r'^\s*-\s*\[[^\]]*\]\s*', '', entry_text)
    for sep in ('。', '；', '：', ':', '——', '，'):
        i = t.find(sep)
        if 0 < i < limit:
            return t[:i + 1]
    return t[:limit]

def archive_path_for(codely_path, seq, scope_tag):
    d = os.path.join(os.path.dirname(codely_path), '.codely-cli', 'memory')
    return os.path.join(d, 'mem-%s-%s-%03d.md' % (DATE, scope_tag, seq))

def slim_file(path, dry, scope_tag):
    text = io.open(path, encoding='utf-8', errors='strict').read()
    lines, ents = parse_entries(text)
    longs = [i for i in ents if len(lines[i].strip()) > LIMIT]
    if not longs:
        return dict(path=path, before=len(text), after=len(text), moved=0, archives=[], skip=True)
    out_lines = list(lines)
    archives, moves = [], []
    seq = 1
    for i in longs:
        entry = lines[i].rstrip('\r')
        ap = archive_path_for(path, seq, scope_tag); seq += 1
        body = '# 记忆档案（memory-slim 下钻·%s）\n> 源=%s（C-20260930-05 长判例下钻律·全文逐字节保真）\n\n%s\n' % (
            DATE, os.path.relpath(path, ROOT) if ROOT in path else path, entry)
        rel = os.path.relpath(ap, os.path.dirname(path)).replace('\\', '/')
        m = re.match(r'\s*-\s*(\[[^\]]*\])', entry)
        ts = m.group(1) if m else '[%s]' % DATE
        ptr = '- %s %s → 全文档案: %s' % (ts, digest(entry), rel)
        moves.append((i, entry, ap, body, ptr))
        archives.append(ap)
    if dry:
        after = len(text) - sum(len(e) for _, e, _, _, _ in moves) + sum(len(p) for *_, p in moves)
        return dict(path=path, before=len(text), after=after, moved=len(moves), archives=[a for _, _, a, _, _ in moves], skip=False, dry=True)
    os.makedirs(os.path.dirname(archives[0]), exist_ok=True)
    for i, entry, ap, body, ptr in moves:
        io.open(ap, 'w', encoding='utf-8', newline='\n').write(body)
        out_lines[i] = ptr
    new_text = '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')
    io.open(path, 'w', encoding='utf-8', newline='\n').write(new_text)
    # 字节对账：档案正文必须与原文逐字节一致
    ok = True
    for i, entry, ap, body, ptr in moves:
        if entry not in io.open(ap, encoding='utf-8').read(): ok = False
    return dict(path=path, before=len(text), after=len(new_text), moved=len(moves), archives=archives, skip=False, verify_ok=ok)

def audit(files):
    print('# 记忆件体量帽审计（C-20260930-05 法条②·%s）' % datetime.datetime.now().strftime('%F %H:%M'))
    bad = 0
    for p in files:
        t = io.open(p, encoding='utf-8', errors='replace').read()
        _, ents = parse_entries(t)
        longs = [l for l in (t.splitlines()) if l.lstrip().startswith('- [') and len(l.strip()) > LIMIT]
        over = len(t.encode('utf-8')) > CAP
        flag = ('超帽! ' if over else '') + ('超限条%d ' % len(longs) if longs else '')
        if over or longs: bad += 1
        print('%-64s %7.1fKB  条目%3d  超限%2d %s' % (
            os.path.relpath(p, ROOT) if ROOT in p else '【全局】' + p,
            len(t.encode('utf-8')) / 1024, len(ents), len(longs), flag))
    print('结论：%d/%d 件违帽' % (bad, len(files)))
    return 1 if bad else 0

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--dry'
    files = find_codely_files()
    if mode == '--audit':
        sys.exit(audit(files))
    dry = mode != '--run'
    print('memory-slim %s · LIMIT=%d 字 · 阈上条目下钻' % ('DRY' if dry else 'RUN', LIMIT))
    if not dry:
        os.makedirs(BACKUP, exist_ok=True)
    tb = ta = tm = 0
    report = []
    for p in files:
        tag = 'g' if (ROOT + r'\gaming') in p and p.count('gaming') == 1 else 'm' if 'MiniGame' in p else 'q' if 'quant' in p else 'c' if 'cph4' in p else 'o'
        r = slim_file(p, dry, tag)
        if not dry and not r.get('skip'):
            shutil.copy2(p, os.path.join(BACKUP, os.path.basename(os.path.dirname(p)) + '__' + os.path.basename(p)))
        tb += r['before']; ta += r['after']; tm += r['moved']
        report.append(r)
        print('%-64s %6.1fK→%6.1fK  下钻%2d 条 %s' % (
            os.path.relpath(p, ROOT) if ROOT in p else '【全局】', r['before'] / 1024, r['after'] / 1024, r['moved'],
            '' if r.get('skip') or r.get('verify_ok', True) else '!!对账失败!!'))
    print()
    print('合计：%.1fKB → %.1fKB（省 %.0f%%）·下钻 %d 条' % (tb / 1024, ta / 1024, 100 * (1 - ta / tb) if tb else 0, tm))
    if not dry:
        print('备份：%s' % BACKUP)
    fail = [r for r in report if not r.get('verify_ok', True)]
    sys.exit(1 if fail else 0)

if __name__ == '__main__':
    main()
