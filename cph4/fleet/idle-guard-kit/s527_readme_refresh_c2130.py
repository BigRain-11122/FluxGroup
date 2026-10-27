# -*- coding: utf-8 -*-
# s527_readme_refresh_c2130.py - refresh the S527 hand-off README so it lists what
# is actually on disk now (plates + proxies + contact/proxy boards + verify +
# conform receipts), with a single artifact table. Bank job
# s527-delivery-readme-refresh-v1.
#
# Zero GPU. PASS gate: README-REFRESH-END ok=1 + every listed path exists.

import hashlib
import json
import os
import time

XQ = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing"
DELIVERY = os.path.join(XQ, "delivery")
RECEIPT = os.path.join(DELIVERY, "README-S527-4k.md")
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOG_OUT = os.path.join(LOGDIR, "s527_readme.out.txt")

EXTRA = [
    (os.path.join(DELIVERY, "proxy", "xq-S527-PROXY-CONTACT-c2129.jpg"),
     "S527 出货六盘 1600px 联系板（翻页审看用）"),
    (os.path.join(DELIVERY, "VERIFY-S527-4K-c2127.json"),
     "出货完整性复验收据（逐张重算 SHA256 vs 清单 vs 源盘，6/6 恒等、0 不符）"),
    (os.path.join(XQ, "abatch_s7r", "xq-S7R-FAMILY-RATIFY-BOARD-c2126.jpg"),
     "S7R 板族一页签认索引（四板缩略 + 标签映射 + sha 短号）"),
]


def logline(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG_OUT, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    if os.path.exists(LOG_OUT):
        os.remove(LOG_OUT)
    man = json.load(open(os.path.join(DELIVERY, "MANIFEST-s527-4k.json"), encoding="utf-8-sig"))
    entries = man["entries"]
    logline("README-REFRESH-START plates=%d" % len(entries))

    lines = []
    lines.append("# S527 六张 4K 出货母版 — 交接说明（C2130 刷新版）")
    lines.append("")
    lines.append("更新于 %s。本页只列盘上真实存在的文件；路径均相对于 `media/MV/mv0001/xingqing/`。" % time.strftime("%Y-%m-%d %H:%M"))
    lines.append("")
    lines.append("## 一 出货母版（4K·grain 0.10·3840×2194）")
    lines.append("")
    lines.append("| 文件（delivery/） | 字节 | SHA256 前 16 |")
    lines.append("|---|---|---|")
    for e in entries:
        p = os.path.join(DELIVERY, e["file"])
        if not os.path.exists(p):
            raise SystemExit("missing plate " + p)
        lines.append("| `%s` | %d | `%s` |" % (e["file"], os.path.getsize(p), sha16(p)))
    lines.append("")
    lines.append("## 二 审看辅助件")
    lines.append("")
    lines.append("| 文件 | 字节 | 用途 |")
    lines.append("|---|---|---|")
    prox = sorted(os.listdir(os.path.join(DELIVERY, "proxy"))) if os.path.isdir(os.path.join(DELIVERY, "proxy")) else []
    for name in prox:
        if not name.endswith(".jpg"):
            continue
        p = os.path.join(DELIVERY, "proxy", name)
        lines.append("| `delivery/proxy/%s` | %d | 1600px 翻页代理（非交付件） |" % (name, os.path.getsize(p)))
    for p, note in EXTRA:
        if not os.path.exists(p):
            raise SystemExit("missing extra " + p)
        rel = os.path.relpath(p, XQ).replace("\\", "/")
        lines.append("| `%s` | %d | %s |" % (rel, os.path.getsize(p), note))
    lines.append("")
    lines.append("## 三 复验法")
    lines.append("")
    lines.append("`certutil -hashfile <文件> SHA256` 或 Python `hashlib.sha256`，逐张与本表与")
    lines.append("`delivery/MANIFEST-s527-4k.json` 对数；`VERIFY-S527-4K-c2127.json` 是最近一次全量复验的机读收据。")
    lines.append("")
    lines.append("代理件（proxy/）只作审看，**不进交付**；交付恒为 delivery/ 下的 4K PNG 母版。")
    lines.append("")

    text = "\n".join(lines)
    open(RECEIPT, "w", encoding="utf-8", newline="\n").write(text)
    logline("README %s %dB" % (os.path.basename(RECEIPT), len(text.encode("utf-8"))))
    logline("README-REFRESH-END ok=1 plates=%d proxies=%d extras=%d"
            % (len(entries), len([n for n in prox if n.endswith(".jpg")]), len(EXTRA)))


if __name__ == "__main__":
    main()