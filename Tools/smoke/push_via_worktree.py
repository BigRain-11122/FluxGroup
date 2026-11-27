# -*- coding: utf-8 -*-
"""通用外科上链：把给定提交重放到 origin/main 并推送（状态类冲突取上游）。"""
import os, shutil, subprocess, sys

REPO = r'K:\Fluxgroup\FluxGroup'
WT = r'K:\Fluxgroup\wt-push-tmp'
STATE_PREFIX = ('cph4/fleet/rt/', 'cph4/fleet/state/', 'quant/.codely-cli/', 'media/logs/')
SHAS = sys.argv[1:]


def g(a, cwd=WT, check=False):
    p = subprocess.run(['git'] + a, cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if check and p.returncode != 0:
        print('FAIL', ' '.join(a), (p.stderr or '')[-300:])
    return p


if os.path.isdir(WT):
    subprocess.run(['git', 'worktree', 'remove', WT, '--force'], cwd=REPO, capture_output=True)
    shutil.rmtree(WT, ignore_errors=True)

print(g(['worktree', 'add', '--detach', WT, 'origin/main'], cwd=REPO).stdout.strip()[-80:])
# 过滤器回环：两个被 .gitattributes 当二进制的文件会让 rebase 一直报脏
for f in ('media/drama-tools/drama_mix_batch.py', 'media/drama-tools/drama_voicegen_batch.py'):
    g(['update-index', '--assume-unchanged', f])

for sha in SHAS:
    p = g(['cherry-pick', sha])
    if p.returncode == 0:
        print('ok   ', sha)
        continue
    st = [x for x in g(['diff', '--name-only', '--diff-filter=U']).stdout.split() if x]
    ours = [f for f in st if f.replace('\\', '/').startswith(STATE_PREFIX)]
    theirs = [f for f in st if f not in ours]
    if ours:
        g(['checkout', '--ours', '--'] + ours)
        g(['add', '--'] + ours)
    if theirs:
        g(['checkout', '--theirs', '--'] + theirs)
        g(['add', '--'] + theirs)
    c = g(['cherry-pick', '--continue'])
    print(('ok* ' if c.returncode == 0 else 'ABORT ') + sha)
    if c.returncode != 0:
        g(['cherry-pick', '--abort'])

for i in range(8):
    g(['fetch', '-q', 'origin', 'main'])
    if g(['rebase', '-q', 'origin/main']).returncode != 0:
        g(['rebase', '--abort'])
        print('rebase-fail')
        break
    push = g(['push', 'origin', 'HEAD:main'])
    if push.returncode == 0:
        print('PUSHED:', (push.stderr or '').strip().splitlines()[-1][:120])
        break
    print('retry', i + 1)
    import time
    time.sleep(5)

subprocess.run(['git', 'worktree', 'remove', WT, '--force'], cwd=REPO, capture_output=True)
shutil.rmtree(WT, ignore_errors=True)
