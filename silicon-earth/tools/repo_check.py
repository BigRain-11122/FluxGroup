# -*- coding: utf-8 -*-
"""
repo_check · 把集团旧规则里能自动化的部分接进来

对应旧规则：
  RULES §2 命名：文件名英文、无空格、无中文
  RULES §3 代码：不得含密钥
  大文件红线：单件 >95MB 禁入 git，>20MB 需警告
  提交规范：首行 ≤50 字且带任务号或类型前缀

用法：
  python tools/repo_check.py                 # 仓库体检
  python tools/repo_check.py --msg "T03: ..." # 检查一条提交消息
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SECRET = re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|access[_-]?token)\b\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}")
MSG_HEAD = re.compile(r"^([A-Za-z\u4e00-\u9fa5]{1,12}|T\d+)\s*[:：]")


def say(m):
    print(m, flush=True)


def tracked():
    p = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return [x for x in (p.stdout or "").split("\0") if x.strip()]


def check_names(files, bad):
    for f in files:
        name = os.path.basename(f)
        if any(ord(ch) > 127 for ch in f):
            bad.append(f"文件名含非 ASCII：{f}")
        elif " " in name:
            bad.append(f"文件名含空格：{f}")


def check_sizes(files, bad, warn):
    for f in files:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        mb = os.path.getsize(p) / 1048576.0
        if mb > 95:
            bad.append(f"超 95MB 禁入 git：{f} ({mb:.1f}MB)")
        elif mb > 20:
            warn.append(f"超 20MB 需确认：{f} ({mb:.1f}MB)")


def check_secrets(files, bad):
    for f in files:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p) or os.path.getsize(p) > 1048576:
            continue
        if f.endswith((".png", ".jpg", ".zip", ".woff2", ".mp4")):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except Exception:
            continue
        if SECRET.search(text):
            bad.append(f"疑似密钥：{f}")


def check_msg(msg, bad):
    head = (msg or "").splitlines()[0] if msg else ""
    if len(head) > 50:
        bad.append(f"提交首行 {len(head)} 字，超过 50")
    if not MSG_HEAD.match(head):
        bad.append("提交首行缺少任务号或类型前缀（如 T03: / fix: / docs:）")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 3 and sys.argv[1] == "--msg":
        bad = []
        check_msg(sys.argv[2], bad)
        for x in bad:
            say("✗ " + x)
        if not bad:
            say("✓ 提交消息合规")
        return 1 if bad else 0

    files = tracked()
    bad, warn = [], []
    check_names(files, bad)
    check_sizes(files, bad, warn)
    check_secrets(files, bad)

    say(f"检查 {len(files)} 个已跟踪文件")
    for w in warn[:5]:
        say("  ! " + w)
    if bad:
        say(f"✗ {len(bad)} 处违规：")
        for x in bad[:20]:
            say("  - " + x)
        return 1
    say(f"✓ 命名/体积/密钥 全部通过" + (f"（{len(warn)} 项提醒）" if warn else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
