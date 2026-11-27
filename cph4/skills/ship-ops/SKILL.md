---
name: ship-ops
description: 分发与上架席（C4 SHIP）。Use when publishing or submitting any output — platform declaration checkbox, AIGC dual marking, micro-drama filing (备案), WeChat mini-game submission chain, ICP/软著 prerequisites, release receipt, or deciding whether a piece may go out at all. Triggers on 发布/上架/提审/备案/标识/声明位/平台/回执/下架/B站/抖音/微信小游戏.
---

# 分发与上架席

正典深度位：合规=`GimmeAll/docs/family/CONTENT-COMPLIANCE.md`+`Tools/family_compliance_check.py`｜架构 C4 段=`cph4/ARCHITECTURE-v2-FLUXOS-20261102.md` §十｜资质链=`cph4/fleet/BIGGAME-G1-*`＋docs/orders.md 物理件区。本件只收高频硬律。

## 硬律速查（违例即返工族）

1. **双标识分轨**：隐式标识（元数据 `AIGC` 字段＋内容哈希＋服务方编码）机器写、强制；显式"AI 生成"字样**不加**（CEO 2026-10-30 令），但平台上传声明位照实勾选。两条不可互换——把"不加显式"当成"不用声明"是本席最常见错误。
2. **微短剧备案后上线**：无备案号不发任何一集；算法侧不得写诱导沉迷/诱导消费的钩子。
3. **资质链顺序不可跳**：微信 AppID → ICP → 软著报审 → 提审。前一环没下来，下一环开工=白做。全线卡点在 CEO 物理件（2026-09-16 挂至今），查到卡住只报"卡在第几环"，不改代码绕过。
4. **发布回执三件**：平台＋链接＋时间。发完报备一条即可，CEO 抽查可否决下架重发；不自建审批流。
5. **片尾出处声明保留**：`转载需注明出处 @大喵没鱼吃`（CEO 2026-10-19 令）。任何重剪、压制、放大版本都不得丢这一卡。
6. **日志留存 ≥6 个月**：无显式标识的输出，留存"提供给谁＋何时"的记录。
7. **不买量**：短剧/漫剧卖平台方成片，不自投流（投流约占出海成本 50%，北美获客 ≈5.28 美元/人，2026-11-03 市场简报）。小游戏走零买量亲子付费。

## 上架前机械自查（缺一项不提交）

```
ffprobe -v error -show_entries format_tags -of json <成片>   # 看 AIGC 隐式字段在不在
grep -c "转载需注明出处" <字幕/片尾>                          # 应 ≥1
ls <备案号文件>                                              # 无则不发
python Tools/family_compliance_check.py                      # 儿童场景四查必过
```

## 工具速查
`Tools/family_compliance_check.py`（AIGC 标识＋零真人脸＋品牌规避＋儿童场景）｜`Tools/fleet/ship_ledger.py`（发布台账）｜`Tools/car_adapt_check.py`（车机 10 档，仅渠道交付用）。

## 可跑自查（自动生成·2026-11-03）
判据：下面这条命令必须能在本机真跑起来（rc∈{0,1,2} 且有输出）；跑不起来说明技能指向的工具已失效，先修工具再谈技能。

```
python3 Tools/fleet/ship_ledger.py --help
```
实测：rc=0，输出 5 行，首行 `usage: ship_ledger.py [-h] {add,data,show} ...`。
