#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""domain_prep.py - 商城前置件：不依赖商户号的活先干完。

为什么（CEO 2026-11-05「虽然物理件我卡住了，但他们后续的工作可以提前开展」）：
  商户号没下来，不代表商品页、定价表、退款说明、支付接入清单都要等。
  这些是纯文本/静态件，机器现在就能出；等资质到位，只需把支付入口从"占位"
  换成真实通道——把等待时间从"整条链路"压到"一步替换"。

产出（都进 git）：
  media/domain/index.html      一页商品页（商品/价格/支付占位/退款说明）
  cph4/fleet/domain/PRICING.json 三档定价（含成本与毛利假设，来源标注）
  cph4/fleet/domain/PAY-INTEGRATION.md 支付接入清单（资质到位后照单执行）
用法：python3 Tools/fleet/domain_prep.py
"""
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(ROOT, "media", "domain")
CFG_DIR = os.path.join(ROOT, "cph4", "fleet", "domain")

# 价格来自既有决策记录（吸嘟嘟明信片模型：买断/家庭包/皮肤；算力包 19.9）
TIERS = [
    {"id": "compute-19.9", "name": "算力包", "price_cny": 19.9,
     "note": "月度；成本与毛利待 BigCompute 台账补，本处只标占位"},
    {"id": "family-pack", "name": "家庭包", "price_cny": 58.0,
     "note": "一次买断，含全部关卡与明信片册"},
    {"id": "skin", "name": "皮肤", "price_cny": 12.0,
     "note": "区间 6–18 元的中间档，按系列定"},
]


def pricing():
    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "currency": "CNY",
        "source": "既有决策记录（明信片模型买断/家庭包/皮肤；算力包 19.9）",
        "tiers": TIERS,
        "unverified": ["各档实际成本", "毛利假设", "云厂商同规格对照价"],
        "rule": "标 unverified 的数字不得对外报；定价最终由 CEO 签",
    }


def page():
    rows = "\n".join(
        '      <div class="card"><h3>%s</h3><div class="price">¥%s</div>'
        '<p>%s</p><button disabled>支付通道待开通</button></div>'
        % (t["name"], t["price_cny"], t["note"]) for t in TIERS)
    return """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>FluxGroup 商城（前置件）</title>
<style>
body{font:15px/1.7 -apple-system,"PingFang SC";margin:0;padding:32px;background:#0f1115;color:#e6e6e6}
h1{font-size:20px}.card{background:#171a21;border:1px solid #262b36;border-radius:10px;padding:18px;margin:12px 0}
.price{font-size:22px;color:#8ecbff}button{padding:8px 14px;border-radius:8px;border:1px solid #3a4150;background:#20242c;color:#8892a4}
.note{margin-top:24px;color:#8892a4;font-size:13px}
</style></head><body>
<h1>商品页（支付未开通）</h1>
%(rows)s
<div class="note">
<p><b>退款说明</b>：未开通支付前不产生任何交易。开通后 7 日内无理由退款，原路退回。</p>
<p><b>合规</b>：本页不含个人身份信息采集；不做定向推送；未成年人需监护人同意。</p>
<p>生成时间 %(ts)s · 数据源 cph4/fleet/domain/PRICING.json</p>
</div></body></html>
""" % {"rows": rows, "ts": datetime.now().isoformat(timespec="seconds")}


def integration():
    return """# 支付接入清单（资质到位后照单执行）

> 前置件已完成：商品页、定价表、退款条款。此清单只在商户号下来后执行，
> 目标是把"占位按钮"替换为真实通道，其余部分不动。

1. 商户号落盘：`docs/legal/MERCHANT-ID.md`（触发 unlock 预案 U-MERCHANT）。
2. 支付渠道接入：选择平台内支付或聚合支付；回调地址指向订单落盘件。
3. 订单落盘：每笔订单写 `cph4/fleet/domain/orders/<YYYYMM>/<order_id>.json`
   （含商品、金额、渠道流水号、时间、退款状态）。
4. 退款：按 7 日无理由规则自动受理；退款结果回写同一订单文件。
5. 对账：每日把渠道账单与本地订单逐笔核对，差异进 `cph4/fleet/domain/RECON.md`。
6. 上线门禁：①真实测试订单 1 笔成功 ②退款 1 笔成功 ③对账 0 差异 —— 三条齐才允许对外。

## 当前状态
- 商品页：已生成（支付按钮为占位）
- 定价表：已生成（成本/毛利标 unverified，不得对外报）
- 订单落盘件：**未建**（需先建 `Tools/fleet/order_sink.py`）
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CFG_DIR, exist_ok=True)
    with open(os.path.join(CFG_DIR, "PRICING.json"), "w", encoding="utf-8") as f:
        json.dump(pricing(), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page())
    with open(os.path.join(CFG_DIR, "PAY-INTEGRATION.md"), "w", encoding="utf-8") as f:
        f.write(integration())
    print("[domain-prep] wrote media/domain/index.html, cph4/fleet/domain/{PRICING.json,PAY-INTEGRATION.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())