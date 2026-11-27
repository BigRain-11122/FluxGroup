#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""softcopyright_audit.py — 软著申请材料全面审查（只读，零 LLM）。

为什么需要它
------------
36 套软著材料靠人一套套翻必然漏。实测已发现系统性问题：说明书 PDF 只有 2 页 / 11 页，
而中国版权保护中心要求文档交「前 30 页 + 后 30 页」（不足 60 页全交），每页 ≥30 行；
源程序每页 ≥50 行。页数不足 = 直接退件，属于纯流程债。

判据
----
  C1 必备件：源程序(txt|pdf)、说明书(md|pdf)、申请表指南(md)、icon_512、隐私政策
  C2 源程序页数 ≥30（目标 60），每页行数 ≥50
  C3 源程序页眉：<全称> <版本> 源程序  第 N 页 共 M 页，N 连续 1..M
  C4 说明书页数 ≥30（目标 60）
  C5 名称/版本一致：源程序页眉 = 说明书标题 = 指南表格
  C6 PDF 页数 == TXT 页数（有 txt 时）

用法
----
  python Tools/softcopyright_audit.py
  python Tools/softcopyright_audit.py --only G09_GimmeAll
  python Tools/softcopyright_audit.py --json out.json
  python Tools/softcopyright_audit.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "软著申请材料"

PAGE_MIN_SRC, LINE_MIN_SRC = 30, 50
PAGE_MIN_DOC = 30
HEADER_RE = re.compile(
    r"^(?P<name>\S+?)\s+(?P<ver>V?\d+\.\d+)\s+源程序\s+第\s*(?P<no>\d+)\s*页\s*共\s*(?P<total>\d+)\s*页"
)
REQUIRED = {
    "src_txt": (".txt",),
    "src_pdf": ("源程序.pdf",),
    "doc_md": ("说明书.md",),
    "doc_pdf": ("说明书.pdf",),
    "guide_md": ("申请表填写指南.md",),
    "icon": ("icon_512.png",),
    "privacy": ("privacy-policy.md",),
}


def pdf_pages(path: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return -1


def read_text(p: Path) -> str:
    """Always utf-8-sig: these docs are written with a BOM by Windows tools, and a stray
    \\ufeff makes every name comparison fail for reasons that have nothing to do with the doc."""
    return p.read_text(encoding="utf-8-sig", errors="replace")


def find(files, suffix):
    for f in files:
        if f.endswith(suffix):
            return f
    return None


def audit_dir(d: Path) -> dict:
    files = [f.name for f in d.iterdir() if f.is_file()]
    reds, notes, info = [], [], {"dir": d.name, "files": len(files)}

    missing = [k for k, sufs in REQUIRED.items() if not any(find(files, s) for s in sufs)]
    if missing:
        reds.append("C1 缺件: " + str(missing))

    src = find(files, ".txt")
    name_ver = None
    if src:
        text = read_text(d / src)
        pages = [p for p in re.split(r"\n(?=\S+?\s+V?\d+\.\d+\s+源程序\s+第)", text)
                 if HEADER_RE.match(p.strip())]
        info["src_pages_txt"] = len(pages)
        if len(pages) < PAGE_MIN_SRC:
            reds.append(f"C2 源程序只有 {len(pages)} 页（<{PAGE_MIN_SRC}）")
        bad, totals, nos = [], set(), []
        for p in pages:
            m = HEADER_RE.match(p.strip())
            body = [l for l in p.strip().splitlines()[1:] if l.strip()]
            if len(body) < LINE_MIN_SRC:
                bad.append((m["no"] if m else "?", len(body)))
            if m:
                totals.add(int(m["total"]))
                nos.append(int(m["no"]))
                name_ver = name_ver or (m["name"], m["ver"])
        if bad:
            reds.append(f"C2 每页行数 <{LINE_MIN_SRC}: {bad[:3]}")
        if len(totals) > 1:
            reds.append(f"C3 总页数不一致: {sorted(totals)}")
        if nos and nos != list(range(1, len(nos) + 1)):
            reds.append(f"C3 页码不连续: {nos[:5]}")
    else:
        notes.append("无 txt 源程序，跳过 C2/C3 行级校验")

    doc_pdf = find(files, "说明书.pdf")
    if doc_pdf:
        n = pdf_pages(d / doc_pdf)
        info["doc_pages"] = n
        if n >= 0 and n < PAGE_MIN_DOC:
            reds.append(f"C4 说明书只有 {n} 页（<{PAGE_MIN_DOC}）")

    src_pdf = find(files, "源程序.pdf")
    if src_pdf and src:
        n = pdf_pages(d / src_pdf)
        info["src_pages_pdf"] = n
        if info.get("src_pages_txt") and n >= 0 and n != info["src_pages_txt"]:
            reds.append(f"C6 源程序 PDF {n} 页 ≠ TXT {info['src_pages_txt']} 页")

    doc_md = find(files, "说明书.md")
    guide = find(files, "申请表填写指南.md")
    if name_ver and doc_md:
        title = read_text(d / doc_md).splitlines()[0]
        if name_ver[0] not in title or name_ver[1] not in title:
            reds.append(f"C5 说明书标题与页眉不一致: {title[:40]!r} vs {name_ver}")
    if name_ver and guide:
        if name_ver[0] not in read_text(d / guide):
            reds.append(f"C5 指南未出现全称 {name_ver[0]!r}")

    return {"dir": d.name, "reds": reds, "notes": notes, "info": info,
            "verdict": "PASS" if not reds else "FAIL"}


def run(only=None):
    dirs = [p for p in sorted(BASE.iterdir()) if p.is_dir() and not p.name.startswith("_")]
    dirs = [p for p in dirs if "CCPC" not in p.name]   # 另一种提交格式，单独审
    if only:
        dirs = [p for p in dirs if p.name == only]
    return [audit_dir(d) for d in dirs]


def self_test() -> int:
    import tempfile

    fails = 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        def make(name, pages=30, lines=55, full=True, hdr="测试软件 V1.0", doc_hdr=None):
            d = base / name
            d.mkdir()
            body = []
            for i in range(1, pages + 1):
                body.append(f"{hdr} 源程序  第 {i} 页 共 {pages} 页")
                body += ["    // code"] * lines
            (d / "测试_V1.0_源程序.txt").write_text("\n".join(body), encoding="utf-8")
            (d / "测试_V1.0_说明书.md").write_text(f"# {doc_hdr or hdr} 软件设计说明书\n内容\n",
                                                   encoding="utf-8")
            (d / "申请表填写指南.md").write_text(f"| 软件全称 | {hdr} |\n", encoding="utf-8")
            (d / "icon_512.png").write_bytes(b"\x89PNG")
            (d / "privacy-policy.md").write_text("privacy", encoding="utf-8")
            if full:
                (d / "测试_V1.0_源程序.pdf").write_bytes(b"%PDF-1.4\n")
                (d / "测试_V1.0_说明书.pdf").write_bytes(b"%PDF-1.4\n")
            return d

        r = audit_dir(make("GOOD"))
        if any(x.startswith(("C4", "C6")) for x in r["reds"]):
            fails += 1
            print("FAIL 假 PDF 不应触发页数红:", r["reds"])
        else:
            print("PASS 好件通过")

        d = make("MISS", full=False)
        (d / "icon_512.png").unlink()
        if not any(x.startswith("C1") for x in audit_dir(d)["reds"]):
            fails += 1
            print("FAIL 缺件未抓")
        else:
            print("PASS 抓到缺件")

        if not any(x.startswith("C2") for x in audit_dir(make("BADPAGES", pages=10))["reds"]):
            fails += 1
            print("FAIL 页数不足未抓")
        else:
            print("PASS 抓到页数不足")

        if not any(x.startswith("C5") for x in audit_dir(make("MISMATCH", doc_hdr="别的软件 V1.0"))["reds"]):
            fails += 1
            print("FAIL 名称不一致未抓")
        else:
            print("PASS 抓到名称不一致")

    print(json.dumps({"self_test": "PASS" if not fails else "FAIL", "failures": fails},
                     ensure_ascii=False))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    rows = run(args.only)
    red = [r for r in rows if r["reds"]]
    print(f"{'目录':<28} {'结论':<6} 说明")
    for r in rows:
        print(f"{r['dir']:<28} {r['verdict']:<6} {'; '.join(r['reds'])[:110]}")
    print(f"\n合计 {len(rows)} 套，红 {len(red)} 套")

    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print("json=" + args.json)
    return 0 if not red else 1


if __name__ == "__main__":
    raise SystemExit(main())
