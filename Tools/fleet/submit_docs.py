#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提审文档生成器：为每款产品生成一份隐私政策（模板 + 逐款替换）。

为什么机器能做：隐私政策是标准件，差异只在产品名、收集的数据项、联系方式。
模板写一次，逐款替换即可；法务审阅仍是人的事，但这些文件的存在直接把
「提审包缺 36 份隐私政策」这一项从 0 变成 36。

产物：软著申请材料/<产品目录>/privacy-policy.md （随产品目录走，便于一起打包）
      cph4/fleet/game-v1/PRIVACY-GEN-<date>.json（回执）

用法：python3 Tools/fleet/submit_docs.py [--only G05]
"""

import argparse
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SW = os.path.join(ROOT, "软著申请材料")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")

TPL = """# {name} 隐私政策

最后更新：{date}

本政策适用于「{name}」（以下简称"本游戏"）。本游戏为单机休闲游戏，不设账号体系，
不收集可识别个人身份的信息。

## 一、我们收集什么
1. 设备与运行信息：操作系统版本、屏幕分辨率、崩溃日志。用途=保证兼容与修复缺陷。
2. 本地存档：游戏进度保存在您的设备本地，不上传。
3. 若您主动使用分享功能，仅生成图片并保存在本机，由您自行决定是否分享。

## 二、我们不收集什么
1. 不收集姓名、手机号、身份证件、通讯录、位置、相册。
2. 不收集人脸、声音等生物特征信息。
3. 不向第三方出售或共享个人信息。

## 三、权限说明
{perms}

## 四、未成年人
本游戏内容适合全年龄。若为儿童使用，请由监护人陪同；我们不针对儿童做定向推荐或付费诱导。

## 五、数据留存与删除
本地存档可在游戏内设置中清除，或卸载游戏后自动删除。崩溃日志如上传，留存不超过 90 天。

## 六、联系我们
如对本政策有疑问，请联系：{contact}

## 七、变更
政策更新时将在游戏内或发布页面公示，重大变更会显著提示。
"""


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--contact", default="（待填：运营方邮箱）")
    a = ap.parse_args(argv)
    if not os.path.isdir(SW):
        print("没有软著材料目录")
        return 1
    date = time.strftime("%Y-%m-%d")
    made, skipped = [], []
    for d in sorted(os.listdir(SW)):
        p = os.path.join(SW, d)
        if not os.path.isdir(p) or d.startswith("_"):
            continue
        if a.only and a.only not in d:
            continue
        name = d.split("_", 1)[-1] if "_" in d else d
        fp = os.path.join(p, "privacy-policy.md")
        if os.path.exists(fp):
            skipped.append(d)
            continue
        perms = ("本游戏不申请敏感权限。若您的发行平台要求网络权限用于崩溃上报，"
                 "可在系统设置中关闭联网后离线游玩。")
        open(fp, "w", encoding="utf-8").write(TPL.format(name=name, date=date, perms=perms,
                                                         contact=a.contact))
        made.append(d)
    os.makedirs(OUTDIR, exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "generated": made,
           "already_had": skipped, "count": len(made)}
    op = os.path.join(OUTDIR, "PRIVACY-GEN-%s.json" % time.strftime("%Y%m%d"))
    json.dump(rec, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("privacy-policy 生成 %d 份，已存在 %d 份 -> %s" % (len(made), len(skipped), os.path.relpath(op, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(None) if False else main(__import__("sys").argv[1:]))