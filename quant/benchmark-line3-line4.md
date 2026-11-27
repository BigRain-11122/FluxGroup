# 全球头部对标取证（线三·线四）

## 线三 量化
### Medallion/头部可查事实
- 【事实】1988年成立；2006年起只限员工及家属，外部投资人被清退；管理费5%、业绩费44%；当年规模54亿美元，成立以来年化34.2%[1]
- 【事实】300名员工中90人有数理博士；Medallion费4%、业绩费36–44%，费后年化>30%；公司约500亿美元AUM[2]
- 【事实·原话】Patterson（理盛统计学家）称最重要工具是单变量简单回归，难在选变量与清洗数据；"我们有7位博士专门清洗数据、整理数据库"[3]
- 【推断】重心在数据管道与简单模型正确性，非信号数量

### 防自欺的制度化做法
- 【事实】López de Prado（AQR，JFDS 2019冬）：多重检验校正，防试验次数造成的假显著[4]
- 【事实】Harvey/Liu/Zhu（RFS 2016）主张新因子t值门槛由2提到约3[5]；Arnott/Harvey/Markowitz给出回测协议：记录试验次数、样本外检验[6]

### 成本与执行（TCA/滑点）
- 【事实】AQR用一家大型机构1998–2011、19市场、近1万亿美元实盘交易估成本：实盘成本远低于学术估计、可承载规模高一个数量级；价值/动量可覆盖成本，短期反转在合理规模下不可[7]
- 【事实】成本锚：IBKR美股固定0.005美元/股（每单最低1美元、上限成交额1%）[8]；【推断】100美元股价≈0.5bp/边，不含冲击

### 小团队可行路线
- 【推断】自有/家族资金不对外募资，绕开牌照与费率内卷；只做低换手、成本可测策略
- 【未核实】日本投资运用业资本金5000万日元、香港SFC第9类500万港元等门槛（无原文）

## 线四 算力商业化
### 卖什么与毛利结构
- 【事实】CoreWeave 2026Q2：收入25.75亿美元(+112%)、成本8.79亿；调整后EBITDA 15.1亿(59%)；净亏6.26亿；backlog约1040亿美元；活跃电力1.5GW、签约3.7GW[9]。毛利率≈66%【推断·自算】
- 【事实】Lambda按需H100 3.99、B200 6.69美元/GPU·hr；1-Click集群B200 16卡9.86、256+卡8.87，租期2周–1年[10]
- 【事实】Together：serverless按token；专用推理按分钟/副本，H100 3.99、B200 8.99美元/GPU·hr[11]
- 【事实】Vast市场：主机自设on-demand价+interruptible最低出价、按秒计费[12]；抽成比例未核实

### 利用率与调度
- 【事实】CoreWeave Spot可抢占裸金属，最长7分钟窗口分告警、排空、移出，全抢占后自动回补[13]；Together有preemptible档[14]；Vast用竞价双轨填谷；【未核实】利用率数字

### 客户来源
- 【事实】CoreWeave客户含Caterpillar、Databricks、Runway，以及量化机构Hudson River Trading；Jane Street投资10亿美元[9]
- 【事实】集中度：Microsoft曾占2024年收入62%（S-1转述）[15]；【推断】买neocloud因大厂容量不足，需裸金属大集群+快速扩容

### 小团队门槛与死法
- 【事实】中国：H100裸金属月租2024年约8万元→2025年5万多，个别4.8万逼近成本，跌到4万消纳方宁违约[16]
- 【事实】死法：假订单（只有"战略框架协议"）、指定供应商吃回扣、壳公司签约索赔无门、采购失误（200台机头15万→7万，亏千万）[16]
- 【推断】门槛=拿卡+资金+绿电/机房；无长约消纳方时2–3年GPU折旧吞掉毛利

## 来源
1 https://www.institutionalinvestor.com/article/2btfqaay8z86stkqx8jy8/innovation/medallion-to-become-a-close-knit-fund
2 https://www.forbes.com.au/news/billionaires/billionaire-jim-simons-last-interview/
3 https://news.ycombinator.com/item?id=19065226 （Talking Machines 播客 Nick Patterson 访谈转录）
4 https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JFDS_Winter2019_A-Data-Science-Solution-to-Multiple-Testing-Crisis---Lopez_de_Prado.pdf
5 https://academic.oup.com/rfs/article-abstract/29/1/5/1843824
6 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3275654 （doi 10.2139/ssrn.3275654）
7 https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies
8 https://investors.interactivebrokers.com/en/index.php?f=49761
9 https://content-archive.fast-edgar.com/20260811/AUZ2K22CZ22282Z2222G2WZZMTBIOZMS9282/coreweave2q26earningspress.htm
10 https://lambda.ai/pricing
11 https://docs.together.ai/docs/dedicated-endpoints/pricing
12 https://docs.vast.ai/host/hosting-overview
13 https://docs.coreweave.com/platform/capacity-plans/spot-node-pools
14 https://docs.together.ai/docs/preemptible-compute
15 https://quantlogix.ai/quantlogix-ipo-brief-lambda-2026-08-15
16 https://www.leiphone.com/category/chips/pq8JNwz1wb4jP5x6.html

## 我无法核实的项
- 理盛的数据/执行投入占比、科学家vs交易员人数；Medallion近年规模（2006年54亿与2024年公司500亿口径不同）
- 头部"研究-交易隔离"的制度文本；头部自披露的滑点/TCA数字（只能用AQR实盘基准替代）
- CoreWeave/Lambda具体利用率；Together毛利率；Vast官方抽成比例
- 日本、香港小团队牌照门槛原文；"日本/香港散户向量化"的任何可核实统计
- Lambda口径冲突：媒体称2026年收入>15亿美元、拟融资30亿@约120亿估值；另一机构称2025Q4年化约7.6亿、无S-1
