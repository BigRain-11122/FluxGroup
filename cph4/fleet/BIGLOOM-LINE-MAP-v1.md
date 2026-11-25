# BigLoom 产线总图 v1 — 指针件（正文在独立仓）

> 制=主控（MacBook）· 2026-11-25 · CEO 当日批准成立 BigLoom。
> **本件不是正文，是身位声明**：只写"东西在哪、谁管、怎么验"，不复述内容，避免第二份真理。

## 一、位次（查重律·只补缺不重立）

| 面 | 正身 | 本件态度 |
|---|---|---|
| 公司卡（使命/边界/目录） | `~/BigLoom/README.md` | 不复述 |
| 平台线表（每平台一条线） | `~/BigLoom/docs/LINES-v1.md` | 不复述 |
| 机读路径与不变量 | `~/BigLoom/paths.json` | **路径冲突时以它为准** |
| 采集上游许可裁决 | `~/BigLoom/collect/UPSTREAM-HARVEST-v1.json` | 不复述 |
| 源册实测结论 | `~/BigLoom/collect/SOURCE-VERDICTS.json` | 不复述 |
| BigStream 产线总图（兄弟公司） | `cph4/fleet/BIGSTREAM-LINE-MAP-v3.md` | 原样有效，本件不改它 |

## 二、三条硬事实（要记住的就这三条）

1. **谁管**：BigLoom 由 MacBook（主控 bm-m-1）单独管理，代码留本仓共享，内容在 `~/BigLoom`。
2. **分家口径**：代码留 FluxGroup；内容（gzh / collect，后续 corpus / train*）归 BigLoom。
   旧路径 `cph4/fleet/social/gzh` 是**软链**，失效即事故。
3. **边界**：BigStream 管单品成片，BigLoom 管账号运营 + 素材供给；互不抢机器与发布权。

## 三、验收（一条命令）

```bash
ls -ld ~/FluxGroup/cph4/fleet/social/gzh     # 必须是 symlink → ~/BigLoom/gzh
python3 Tools/fleet/gzh_loop.py --status      # 必须读到 226 篇产业语料
cd ~/BigLoom && git log --oneline -3          # 必须有自己的历史
```

三条同时成立才算"已成立且未断线"。迁移未完成项见 `~/BigLoom/README.md` §五。
