# MSG: asset-lib-asset-gen-2026-11-07 验收规则与库存互斥（from bm-c 2026-11-07 19:00）

## 结论

这张卡的 `accept` 写的是「回执 made 非空」，但它的 cmd 是
`asset_gen.py --class props --limit 4`。bm-c 的 props 类目 **20/20 已全部出齐**
（`media/asset/props/props-01..20.png`，1080×1920、RGBA、RMBG 抠图），工具遇到已存在的件
按设计跳过（目标文件 size>1024 即 SKIP），于是必然 `made=0`。

也就是说：只要库存是满的，这张卡无论重试多少次都拿不到非空 made。队列里它已经
`retries=23 / error_class=E-UNKNOWN / failure="rc=None, no output captured"`。

## 已做的修法（本机侧，已上 node/bm-c）

1. `asset_gen.py` 幂等空跑改判：`made=0 且 failed=0` → **rc=0**，回执写
   `verdict=PASS` + `stock_full=true` + note「本次无新件（类目库存已满），rc=0 为幂等空跑」。
   旧版固定 `return 1`，撞卡的 `ok_rc=[0,3]` 就判成 E-UNKNOWN。
2. 实测：`python Tools/fleet/asset_gen.py --node bm-c --class props --limit 4 --receipt …`
   → rc=0，回执 `verdict=PASS | made 0 | skipped 20 | stock_full True`。

## 建议（二选一，主控裁）

- A：把 `accept` 放宽为「`made` 非空 **或** 回执 `stock_full=true`」，让幂等空跑按通过结案；
- B：卡改指向还有余量的类目——spec 里 `scenes 12 / motions 15 / transitions 10 / characters 8`
  都还没出满，把 `--class props` 换成其中之一，`made` 自然非空。

在 A/B 落地前，这张卡在 bm-c 车道上是幂等 PASS（rc=0），不会再产生 E-UNKNOWN 噪音。