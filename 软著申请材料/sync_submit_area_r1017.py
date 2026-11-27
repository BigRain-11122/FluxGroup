# -*- coding: utf-8 -*-
# sync_submit_area_r1017.py — 报审提交区三件套换新（CEO 令 10-17 刷新批·本轮实质内容变化四款）
import os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(BASE, "_报审提交区")

def find_dir(needle):
    for root, dirs, files in os.walk(SUB):
        for d in dirs:
            if needle in d:
                return os.path.join(root, d)
    return None

JOBS = [
    # (源款目录, 文件名三件, 提交区款目录关键字)
    ("P08_GhostMarshal", "GhostMarshal_V1.0", "奈何桥"),
    ("P01_LanternSlayer", "LanternSlayer_V1.0", "提灯斩鬼"),
    ("FluxVerse_FluxVerse", "FluxVerse_V1.0", "超体宇宙城"),
    ("G09_GimmeAll", "GimmeAll_V1.0", "吸嘟嘟"),
]

PAIRS = [
    ("%s_源程序.pdf", "01_源程序.pdf"),
    ("%s_软件设计说明书.pdf", "02_软件设计说明书.pdf"),
    ("申请表填写指南.pdf", "03_申请表填写指南.pdf"),
]

for proj_dir, stem, needle in JOBS:
    tgt_dir = find_dir(needle)
    if not tgt_dir:
        print("MISS submit dir for:", needle)
        continue
    for src_tpl, dst_name in PAIRS:
        src_name = src_tpl % stem if "%s" in src_tpl else src_tpl
        src = os.path.join(BASE, proj_dir, src_name)
        if not os.path.isfile(src):
            print("MISS src:", src)
            continue
        dst = os.path.join(tgt_dir, dst_name)
        shutil.copy2(src, dst)
        print("SYNC %-14s <- %s/%s" % (needle, proj_dir, src_name))
print("DONE")
