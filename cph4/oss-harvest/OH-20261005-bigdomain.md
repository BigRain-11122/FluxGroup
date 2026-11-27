# OH-20261005-bigdomain — OSS 借力第四窗切片件（BigDomain）

- **窗**：第四窗 2026-10-05 21:40 → 2026-10-08 21:40（P-2026-09-26-08+P-2026-09-28-01 承传·正典=cph4/oss-harvest.md v1.0）·交付 2026-10-04 ~18:49 +08:00（窗开前 ~26.8h 提前交付·R837 窗开前 ~24.8h+R597 窗日+R320 窗内先例链·提前依据=slice3 下窗指针③直查线索预置+候选证据窗期稳定+产品优先律「结果早点出」·如实注）
- **实搜面**（4 次外部请求全录·采时 2026-10-04 ~18:4x-18:49 +08:00·宿主只读通道零登录墙零翻页零密钥）：
  - ①GitHub MCP search_repositories `pyahocorasick in:name` → 响应解析失败如实记（R597/R837 ①② 同型）
  - ②api.github.com/repos/WojciechMula/pyahocorasick 元数据直采（A 级全字段）
  - ③raw.githubusercontent.com/WojciechMula/pyahocorasick/master/LICENSE → BSD 3-Clause 原文全文直采（许可双源）
  - ④pypi.org/pypi/pyahocorasick/json → 259,801 字符超宿主内联上限=取回中止死面如实记（PyPI 发布/轮子面细目=接线轮复验前置）
- **候选**：WojciechMula/pyahocorasick（https://github.com/WojciechMula/pyahocorasick · BSD-3-Clause（spdx+原文双源验） · 1,126★ · 契合点=slice3 下窗指针③「Python 本地 DFA 匹配器线（词库接线配套）」承：R838 自写 trie（65,141 词·src/sandbox/ugc/wordlist.py）=沙箱现役 L1 预筛件〔入池≠采用·trie 保持现役〕→pyahocorasick=Aho-Corasick 自动机 C 扩展+纯 Python 双实现〔API description 原文「C extension and plain python」〕=bootstrap 高吞吐性能升级候选：AC fail-links 多模式匹配最坏 O(n) 保证·纯 trie 失配回退最坏 O(n×最长词)·弹幕/聊天高频预筛与 msgSecCheck 配额保护链〔ugc L1 本地先拦=R838 canon 面承〕生产档吞吐收益
- **采用→落点**：入池（非即采用）→①司级登记簿入池记录面（三）行（docs/oss-harvest/README.md·入池≠采用不入采用表）+接线轮五前置=Bench 对照判据预注册（65,141 词真实语料持续吞吐对照 R838 trie+最坏情形对抗输入+API 语义等价三问）+BSD-3-Clause 再分发条款携带+五门复验+PyPI 发布/轮子面复验（④ 前置）+R838 trie 现役保持注记
- **parked+理由**：slice3 指针①「城市共创区块图像素材工具线」=判负留痕收口（两次顺延线闭口：图像运算面 cv2 已在栈〔watermark 套件现役依赖〕·EXIF/GPS 隐私剥除与缩略/压缩/格式白名单同栈可覆〔重编码剥除=若启用该面接线实测验证·次要注记〕=零新依赖缺口·引入第二图像库=栈污染·不采）｜slice3 指针②真钥双接线实测件=维持 gated（wechatpayv3+houbb 词库接线=CEO 物理件真钥到位即燃·本窗不涉）｜`limits`/频控类仓=判负（lobby AC-S9 E_RATE_LIMIT〔server.py L154-221+test_client.py L597〕+ugc rate_limit〔pipeline.py L117-179〕双面在栈自研=双建面·本轮判读面实勘检出）
- **下窗指针**：第五窗 10-08 21:40→10-11 21:40·线索=①若真钥到位=wechatpayv3+houbb 词库双接线实测件（三前置已备·维持 gated）②pyahocorasick bench 接线轮（若接线判据触发：真实语料吞吐对照+BSD-3 携带+PyPI 轮子面复验）③生产部署观测线（metrics/日志结构化=bootstrap 期启动前再评·开放面）

## 一 五门评估（入池件：WojciechMula/pyahocorasick）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | slice3 指针③原文承（「Python 本地 DFA 匹配器线（词库接线配套）」）+R837 parked 行预告（「pyahocorasick 等 Python DFA 匹配器线=下窗候选方向」）；R838 自写 trie=沙箱现役 L1 预筛（65,141 词·qa/prefilter-R838.log test_prefilter 18/18）→生产弹幕/聊天高频面 AC 自动机=最坏情形 O(n) 保证升级候选（纯 trie 失配重启=最坏 O(n×L)）；接线收益=高频 msgSecCheck 配额保护链吞吐升级·本地提效三问过（本地运行零 API token 零网络） |
| 2 反重复 | 过 | 三面查证（R597/R837 同律）：cph4/README.md 能力注册表 grep pyahocorasick/Aho/DFA/自动机/词库/图像/Pillow=零命中（2026-10-04 本轮预检）+集团切片面 cph4/oss-harvest 全目录 grep 同词=仅本司 slice1/slice2/slice3 指针与 parked 行命中（零他司同题切片）+司内=wordlist.py trie 现役在册（R838 采用行·本簿上表）→**非双建注记**：入池≠采用·trie 保持沙箱现役·pyahocorasick=接线轮 bench 对照候选（判负即弃·真缺口=生产吞吐档非沙箱功能档） |
| 3 许可 | 过 | 双源直验=GitHub API license spdx_id=BSD-3-Clause（licensee 机器检测）+raw master/LICENSE 原文「Copyright (c) Wojciech Muła … Redistribution and use in source and binary forms, with or without modification…」BSD 3-Clause 全文直采互证；BSD=直用类（CC0/MIT/Apache/BSD·slice1 canon 枚举）；GPL 禁入交付链不涉；接线轮 BSD-3 再分发条款携带前置在册 |
| 4 健康 | 过 | stars=1,126·forks=147·open_issues=40·archived=false·disabled=false·pushed_at=2026-04-27T15:57:04Z（半年活跃线内〔2026-10-04 采时 ~5.3 个月〕·无例外注记=R837 houbb 对照更净）·created_at=2013-05-30（13 年存续库）·updated_at=2026-10-01T17:47:29Z（采时周内）；类内单主导仓（Aho-Corasick Python 实现事实标准·topics=aho-corasick/automaton/string-manipulation/trie） |
| 5 成本/安全 | 过 | 本地文本匹配零网络零遥测零密钥（本地提效三问过）；纯 Python 回退实现=API description 原文「C extension and plain python」→装包双通道（C 扩展提速+纯 Python 可移植回退）·PyPI 发布/轮子细目=④ 死面=接线轮复验前置🟡；非模型类 P-17 矩阵不涉零显存；源码公开可审 |

三问门（OSS 寻源 web 直采）：必要=窗 4 正典令文自证（P-2026-09-26-08「寻找开源社区」+P-2026-09-28-01 重申·第四窗 10-05 21:40 起承传）；无本地替代=外部仓元数据/许可原文无本地等效源（司内 trie=沙箱功能等效件非 OSS 评估替代源·二者关系=接线轮 bench 对照非重复造轮）；宿主既有只读通道（GitHub 只读 MCP+api.github.com 直采+raw 直采+PyPI JSON）非新 API 接入零密钥——过门在案（R266/R320/R597/R837 先例口径）。

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 入池 WojciechMula/pyahocorasick（Aho-Corasick 自动机·ugc L1 词库预筛生产吞吐升级候选） | ①司级登记簿入池记录面（三）行（docs/oss-harvest/README.md）+接线轮五前置（bench 对照判据预注册+BSD-3 再分发携带+五门复验+PyPI 轮子面复验+R838 trie 现役保持注记） | 入池在册 |
| slice3 指针①城市共创区块图像素材工具线 | ④判负留痕收口（cv2 在栈自足〔watermark 现役依赖〕+EXIF 剥除=重编码即达·若启用接线实测·两次顺延线闭口；引入第二图像库=栈污染） | 已闭环 |
| slice3 指针②真钥双接线实测件 | ③门控留置（CEO 物理件真钥到位即燃·三前置已备·维持 gated） | 已闭环 |
| `limits`/频控类仓 | ④判负留痕（lobby AC-S9 E_RATE_LIMIT+ugc rate_limit 双面在栈自研=双建面·本轮判读面实勘检出） | 已闭环 |

## 三 验证声明

读源：外部请求 4 次全录（①MCP 解析失败如实计+④PyPI JSON 超内联上限中止死面+②③ 两次实质得·2026-10-04 ~18:4x-18:49 +08:00·零登录墙零翻页零密钥）。分级：pyahocorasick 五门证据=A 级直采（GitHub 官方 API 字段+raw LICENSE 原文双源互证）；「PyPI 发布/轮子面细目」=🟡存疑待证（④ 死面·纯 Python 回退=API description 原文锚·接线轮复验前置）；本仓/集团在册锚=cph4/README grep+oss-harvest 切片面 grep+src/sandbox/lobby E_RATE_LIMIT 实勘〔server.py L154-221〕+src/sandbox/ugc/wordlist.py R838 采用行+slice3 下窗指针行。判据=AC-OH16..OH20（backlog R1131 行预注册先于外部请求·自验全过）。台账位=D-20260927-03 ③豁免（本目录=BigDomain 切片件唯一台账位·收账 commit 归收取轮）。
