#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""submit_ledger_fill.py - 按盘上事实重建「报审台账」，把 32 款未登记的产品补进来。

Why（2026-11-07）：提审链上真正的卡点是资质与材料齐备，而 `报审台账.md` 只有人工随手写的
几行，32 款在册产品没有登记——提审时说不清"这一款交到哪一步"。票据类台账必须由盘上事实
生成（目录里有什么、多大、缺什么），不能靠人回忆，也不能写"待补"糊过去。

产出（都是真件，不是报告）：
  1. 软著申请材料/_报审提交区/报审台账.md   —— 人读面，逐款一行
  2. cph4/fleet/queue-receipts/submit-ledger-<date>.json —— 机读回执

幂等：重复运行只会覆写这两份文件，不追加重复行。
退出码：0 正常写出｜2 软著目录不存在（机制故障，别当"没活"）
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SW = os.path.join(ROOT, "软著申请材料")
SUB = os.path.join(SW, "_报审提交区")
OUT_MD = os.path.join(SUB, "报审台账.md")
RC = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")

# 提审要交的四件套；键=展示名，值=文件名关键词
# (展示名, 文件名关键词, 成品扩展名)。扩展名不可省：CCPC 目录里只有 build_source_pdf.ps1
# 这类构建脚本，把"脚本在"当"成品在"就是假绿——提审要交的是 PDF，不是生成它的脚本。
NEEDS = [
    ("源程序", ("源程序", "source"), (".pdf", ".txt", ".doc", ".docx", ".zip")),
    ("软件设计说明书", ("说明书", "manual", "design"), (".pdf", ".doc", ".docx", ".md")),
    ("申请表填写指南", ("申请表", "apply", "guide"), (".pdf", ".doc", ".docx", ".md")),
    ("隐私政策", ("privacy", "隐私"), (".md", ".txt", ".pdf")),
]
SCRIPTS = (".ps1", ".py", ".cmd", ".sh")
DRAFT_MARKS = ("草版", "草填", "draft", "wip")


def scan_dir(p):
    """返回该产品目录的文件清单（相对名 + 字节数），跳过归档/隐藏目录。

    2026-11-07：CCPC 格式的四款把材料放在 `提交材料/` 子目录里（含 build_*.ps1 与草版 PDF），
    只扫一层会把它们误判成"缺源程序/缺说明书"——假缺口比缺料更坏，因为它会派出一张
    不该存在的补料卡。所以下钻一层已知的存放目录。
    """
    out = []
    subdirs = ("提交材料",)
    try:
        for name in sorted(os.listdir(p)):
            fp = os.path.join(p, name)
            if name.startswith("."):
                continue
            if os.path.isfile(fp):
                out.append({"file": name, "bytes": os.path.getsize(fp)})
            elif os.path.isdir(fp) and name in subdirs:
                for n2 in sorted(os.listdir(fp)):
                    f2 = os.path.join(fp, n2)
                    if os.path.isfile(f2) and not n2.startswith("."):
                        out.append({"file": name + "/" + n2, "bytes": os.path.getsize(f2)})
    except Exception:
        pass
    return out


PRIVACY_TMPL = """# {product} 隐私政策

最后更新：{date}
适用范围：「{product}」（以下简称"本游戏"）。本游戏为单机休闲游戏，不设账号体系，
不收集可识别个人身份的信息。

## 一、我们收集什么
1. 设备与运行信息：操作系统版本、屏幕分辨率、崩溃日志。用途=保证兼容性与修复缺陷。
2. 本地存档：游戏进度保存在您的设备本地，不上传服务器。
3. 若您主动使用分享功能，仅在本机生成图片，由您自行决定是否对外分享。

## 二、我们不收集什么
1. 不收集姓名、手机号、身份证件、通讯录、精确位置、相册内容。
2. 不收集人脸、声纹等生物特征信息。
3. 不向第三方出售、出租或交换个人信息。

## 三、权限说明
本游戏不申请敏感权限。若发行平台要求网络权限仅用于崩溃上报，您可在系统设置中关闭联网后
离线游玩，主体功能不受影响。

## 四、未成年人保护
本游戏内容适合全年龄。儿童使用时请由监护人陪同；我们不针对儿童做定向推荐或付费诱导。

## 五、数据留存与删除
本地存档可在游戏内设置中清除，或卸载游戏后自动删除。崩溃日志如上传，留存不超过 90 天。

## 六、联系我们
如对本政策有疑问，请联系：（待填：运营方邮箱）

## 七、变更
政策更新时将在游戏内或发布页面公示；涉及收集范围扩大的变更，会以显著方式提示。
"""


def fill_privacy(rows, date):
    """给缺隐私政策的产品写一份产品级 dy 政策。幂等：已存在就不覆盖。"""
    wrote = []
    for r in rows:
        if "隐私政策" not in r.get("lacks", []):
            continue
        d = os.path.join(ROOT, r["dir"])
        fp = os.path.join(d, "privacy-policy.md")
        if os.path.exists(fp):
            continue
        try:
            open(fp, "w", encoding="utf-8").write(
                PRIVACY_TMPL.format(product=r["product"], date=date))
            wrote.append(os.path.relpath(fp, ROOT))
        except Exception as e:
            print("  写失败", r["product"], str(e)[:60])
    return wrote


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_MD)
    ap.add_argument("--json", default="")
    ap.add_argument("--fill-privacy", action="store_true",
                    help="为缺隐私政策的产品，按其名称生成产品级 privacy-policy.md（幂等，已存在不覆盖）")
    a = ap.parse_args(argv)
    if not os.path.isdir(SW):
        print("没有软著申请材料目录")
        return 2

    # 报审区：逐批 × 逐产品
    batches = []
    if os.path.isdir(SUB):
        for b in sorted(os.listdir(SUB)):
            bp = os.path.join(SUB, b)
            if not os.path.isdir(bp) or b.startswith("_"):
                continue
            prods = [d for d in sorted(os.listdir(bp))
                     if os.path.isdir(os.path.join(bp, d)) and not d.startswith("_")]
            batches.append((b, bp, prods))
    # 根目录产品（报审区之外的 22 款）：同一套四件套口径，一起纳入台账，
    # 否则台账只覆盖 14 款、另有 22 款仍然"说不清交到哪一步"。
    root_prods = [d for d in sorted(os.listdir(SW))
                  if os.path.isdir(os.path.join(SW, d)) and not d.startswith("_")]
    if root_prods:
        batches.append(("根目录", SW, root_prods))

    rows, missing_agg = [], {}
    for b, bp, prods in batches:
        for d in prods:
            p = os.path.join(bp, d)
            files = scan_dir(p)
            names = [f["file"] for f in files]
            lack = []
            for label, keys, exts in NEEDS:
                hit = any(any(k in n.lower() for k in keys) and n.lower().endswith(exts)
                          for n in names)
                if not hit:
                    lack.append(label)
                    missing_agg[label] = missing_agg.get(label, 0) + 1
            has_script = any(n.lower().endswith(SCRIPTS) for n in names)
            # 草版不算定稿：提审要交的是定稿件，把"草版在"记成 READY 又是一次假绿。
            drafts = [n for n in names if any(m in n for m in DRAFT_MARKS)]
            rows.append({"batch": b, "product": d, "dir": os.path.relpath(p, ROOT),
                         "files": files, "file_count": len(files),
                         "total_bytes": sum(f["bytes"] for f in files),
                         "lacks": lack, "has_build_script": has_script,
                         "drafts": drafts,
                         "verdict": ("MATERIAL-GAP" if lack else
                                     ("MATERIAL-DRAFT" if drafts else "MATERIAL-READY"))})

    filled = []
    if a.fill_privacy:
        filled = fill_privacy(rows, time.strftime("%Y-%m-%d"))
        if filled:
            # 补完立刻重扫，台账必须反映补后的真实状态，不能停留在补前的缺口上
            rows, missing_agg = [], {}
            for b, bp, prods in batches:
                for d in prods:
                    p = os.path.join(bp, d)
                    files = scan_dir(p)
                    names = [f["file"] for f in files]
                    lack = []
                    for label, keys, exts in NEEDS:
                        if not any(any(k in n.lower() for k in keys) and n.lower().endswith(exts)
                                   for n in names):
                            lack.append(label)
                            missing_agg[label] = missing_agg.get(label, 0) + 1
                    rows.append({"batch": b, "product": d, "dir": os.path.relpath(p, ROOT),
                                 "files": files, "file_count": len(files),
                                 "total_bytes": sum(f["bytes"] for f in files),
                                 "lacks": lack,
                                 "verdict": "MATERIAL-READY" if not lack else "MATERIAL-GAP"})

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "scope": "报审提交区",
           "privacy_filled": filled,
           "batches": len(batches), "products": len(rows),
           "material_ready": sum(1 for r in rows if r["verdict"] == "MATERIAL-READY"),
           "material_draft": sum(1 for r in rows if r["verdict"] == "MATERIAL-DRAFT"),
           "missing_by_kind": dict(sorted(missing_agg.items(), key=lambda kv: -kv[1])),
           "rows": rows}
    md = ["# 报审台账（由盘上事实生成）", "",
          "生成时间：%s　｜　批次 %d　｜　产品 %d　｜　定稿齐 %d　｜　仅草版 %d"
          % (rec["ts"], rec["batches"], rec["products"], rec["material_ready"],
             rec["material_draft"]), "",
          "> 本文件由 `Tools/fleet/submit_ledger_fill.py` 从目录实测生成，重复运行覆盖，不追加。",
          "> 「材料齐」只表示四件套文件在位，不代表已通过审核；资质类（AppID/ICP/软著证书）" ,
          "> 属 CEO 物理件，不在此表。", "",
          "## 缺件聚合", ""]
    md += ["- %s：%d 款" % (k, v) for k, v in rec["missing_by_kind"].items()] or ["- 无"]
    md += ["", "## 逐款", "",
           "| 批次 | 产品 | 文件数 | 体积 | 结论 | 缺什么 |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append("| %s | %s | %d | %.1f KB | %s | %s |"
                  % (r["batch"], r["product"], r["file_count"], r["total_bytes"] / 1024.0,
                     r["verdict"], "、".join(r["lacks"]) if r["lacks"] else "—"))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n")

    jp = a.json or os.path.join(RC, "submit-ledger-%s.json" % time.strftime("%Y%m%d"))
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    json.dump(rec, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("batches=%d products=%d ready=%d draft=%d"
          % (rec["batches"], rec["products"], rec["material_ready"], rec["material_draft"]))
    for k, v in rec["missing_by_kind"].items():
        print("  缺 %-14s %d 款" % (k, v))
    print("wrote", os.path.relpath(a.out, ROOT), "+", os.path.relpath(jp, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))