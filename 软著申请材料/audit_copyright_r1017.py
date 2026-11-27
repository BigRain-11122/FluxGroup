# -*- coding: utf-8 -*-
# audit_copyright_r1017.py — 软著材料全量审查（CEO 令 2026-10-17「按最新进度更新+精读审查到位」）
# 审查面：①说明书手写行数 vs 指南回写真值对账（生成器只回写指南·说明书行数手写易漂移）
#        ②三件套齐全性（源程序 txt/pdf + 说明书 md/pdf + 指南 md/pdf）
#        ③名称一致性抽检（软著名 vs 说明书标题）
#        ④md 修改时间 vs pdf 渲染时间（pdf 落后 md=需重渲）
import os, re, sys, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import importlib.util
spec = importlib.util.spec_from_file_location("gc", os.path.join(BASE, "generate_copyright.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)   # 只取 PROJECTS 表·不跑 main

issues, stats = [], []
for key, cfg in gc.PROJECTS.items():
    out_dir = os.path.join(BASE, cfg.get('out_dir', f"{key}_{cfg['name_en']}"))
    name_cn, name_en, ver = cfg['name_cn'], cfg['name_en'], cfg['version']
    row = {"key": key, "name": cfg['name_short'], "dir": os.path.basename(out_dir)}
    if not os.path.isdir(out_dir):
        issues.append(f"[{key}] MISSING DIR: {out_dir}")
        continue
    # 三件套
    src_txt = os.path.join(out_dir, f"{name_en}_{ver}_源程序.txt")
    src_pdf = os.path.join(out_dir, f"{name_en}_{ver}_源程序.pdf")
    doc_md  = os.path.join(out_dir, f"{name_en}_{ver}_软件设计说明书.md")
    doc_pdf = os.path.join(out_dir, f"{name_en}_{ver}_软件设计说明书.pdf")
    gd_md   = os.path.join(out_dir, "申请表填写指南.md")
    gd_pdf  = os.path.join(out_dir, "申请表填写指南.pdf")
    row["txt"] = os.path.isfile(src_txt)
    row["pdf"] = os.path.isfile(src_pdf)
    row["doc_md"] = os.path.isfile(doc_md)
    row["doc_pdf"] = os.path.isfile(doc_pdf)
    row["gd"] = os.path.isfile(gd_md) and os.path.isfile(gd_pdf)
    if not row["doc_md"]:
        issues.append(f"[{key}] 说明书.md 缺失")
    # 行数对账
    guide_lines = None
    if os.path.isfile(gd_md):
        m = re.search(r'\|\s*源程序量\s*\|\s*(\d+)行（(\d+)个\.cs文件）', open(gd_md, encoding='utf-8-sig').read())
        if m:
            guide_lines = int(m.group(1))
            row["guide_lines"] = guide_lines
            row["guide_files"] = int(m.group(2))
    doc_lines = None
    if os.path.isfile(doc_md):
        content = open(doc_md, encoding='utf-8-sig').read()
        for pat in (r'有效代码行\s*([\d,]+)\s*行', r'代码行\s*([\d,]+)\s*行', r'有效代码\s*([\d,]+)\s*行',
                    r'共\s*([\d,]+)\s*行'):
            m = re.search(pat, content)
            if m:
                doc_lines = int(m.group(1).replace(',', ''))
                row["doc_lines"] = doc_lines
                break
        m2 = re.search(r'源程序量[^\d]*约?\s*([\d,]+)\s*行', content)
        if m2:
            row["doc_lines2"] = int(m2.group(1).replace(',', ''))
        # 名称一致性：说明书首行应含软著全称
        first = content.splitlines()[0] if content.splitlines() else ''
        if name_cn not in first:
            issues.append(f"[{key}] 说明书标题不含软著全称「{name_cn}」: {first[:40]}")
    if guide_lines and doc_lines and abs(guide_lines - doc_lines) > max(3, guide_lines * 0.005):
        issues.append(f"[{key}] 行数漂移: 说明书 {doc_lines} vs 指南回写 {guide_lines}（差 {guide_lines - doc_lines:+d}）")
    if guide_lines and row.get("doc_lines2") and abs(guide_lines - row["doc_lines2"]) > max(3, guide_lines * 0.005):
        issues.append(f"[{key}] §2 源程序量行漂移: 说明书 {row['doc_lines2']} vs 指南 {guide_lines}（差 {guide_lines - row['doc_lines2']:+d}）")
    # md vs pdf 新旧（pdf 落后 md = 需重渲）
    if row["doc_md"] and row["doc_pdf"] and os.path.getmtime(doc_pdf) < os.path.getmtime(doc_md):
        issues.append(f"[{key}] 说明书.pdf 落后于 .md（需重渲）")
    if row["gd"] and os.path.getmtime(gd_pdf) < os.path.getmtime(gd_md):
        issues.append(f"[{key}] 指南.pdf 落后于 .md（需重渲）")
    # 缺件报（源程序缺=owner 机面不算本机 issue，但记录）
    if not row["txt"]:
        row["src_state"] = "NO-SRC(owner 机)"
    elif row["txt"]:
        mt = os.path.getmtime(src_txt)
        import time
        ts = time.strftime("%m-%d %H:%M", time.localtime(mt))
        row["src_state"] = "OK@" + ts
        if mt < time.mktime(time.strptime("2026-10-17 23:30", "%Y-%m-%d %H:%M")):
            row["src_state"] += "(旧批)"
    stats.append(row)

print("%-6s %-8s %-7s %-6s %-6s %-7s %-4s %s" % ("key", "name", "src", "lines", "files", "docLN", "gd", "dir"))
for r in stats:
    print("%-6s %-8s %-7s %-6s %-6s %-7s %-4s %s" % (
        r["key"], r["name"], r.get("src_state", "OK" if r.get("txt") else "-"),
        r.get("guide_lines", "-"), r.get("guide_files", "-"), r.get("doc_lines", "-"),
        "OK" if r.get("gd") else "-", r["dir"]))
print("\n==== ISSUES (%d) ====" % len(issues))
for i in issues:
    print(" *", i)
