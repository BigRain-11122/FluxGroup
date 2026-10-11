# OH-20261002-bigdomain — OSS 借力第三窗切片件（BigDomain）

- **窗**：第三窗 2026-10-02 21:40 → 2026-10-05 21:40（P-2026-09-26-08+P-2026-09-28-01 承传·正典=cph4/oss-harvest.md v1.0）·交付 2026-10-01 ~20:3x +08:00（窗开前 ~24.8h 提前交付·R597 窗前 ~5h+R320 窗内 ~71h 先例链·提前依据=slice2 下窗指针①直查线索预置+候选证据窗期稳定+产品优先律「结果早点出」·如实注）
- **实搜面**（13 次外部请求全录·采时 2026-10-01 ~20:2x-20:3x +08:00·宿主只读通道零登录墙零翻页零密钥）：
  - ①GitHub MCP search_repositories `敏感词 stars:>=50 pushed:>=2026-04-01` → 响应解析失败如实记（R597 同型·上游调用按发生计）
  - ②GitHub MCP search_repositories `sensitive word filter language:Python stars:>=50 pushed:>=2026-04-01` → 同解析失败如实记
  - ③api.github.com/search/repositories?q=敏感词（any-field）→ total=11·top1=Dujltqzv/Some-Many-Books=SEO 关键词堆砌垃圾描述（FACE2 污染复发·slice1 已警）→污染面弃用改直查仓法
  - ④api.github.com/search/repositories?q=sensitive word language:Python → total=0 零命中死面如实记
  - ⑤api.github.com/search/repositories?q=敏感词 in:name → total=0 零命中死面如实记（slice2 健康预警「该类仓普遍停更」经验证实：名含敏感词+≥50★+半年内 push 的仓=零）
  - ⑥api.github.com/repos/houbb/sensitive-word 元数据直采（A 级）
  - ⑦api.github.com/repos/adlered/DangerousSpamWords 元数据直采（判负证据）
  - ⑧api.github.com/repos/houbb/sensitive-word/contents/ 根树直采（pom.xml+src/ 单模块 Maven+LICENSE.txt 20,966B+CHANGE_LOG 33,237B）
  - ⑨raw.githubusercontent.com/.../LICENSE → 404（许可文件名=LICENSE.txt 非裸 LICENSE·非缺许可如实注）
  - ⑩raw.githubusercontent.com/.../LICENSE.txt → 「Apache License Version 2.0, January 2004」原文首段直验（许可双源②）
  - ⑪api.github.com/.../contents/src/main → 仅 java/ 子目录
  - ⑫api.github.com/.../contents/src/main/resources → 404 死面（资源路径不在此·词库数据文件定位=接线轮前置）
  - ⑬api.github.com/.../contents/src/main/java/com/github/houbb/sensitive/word → 包树 api/bs/collection/constant/core/…（首页截断·全列定位=接线轮）
- **候选**：houbb/sensitive-word（https://github.com/houbb/sensitive-word · Apache-2.0（spdx+原文双源验） · 6,063★ · 契合点=msgSecCheck 本地预筛词库面〔slice2 指针①承〕：ugc 管道 L1 闸现=词表 mock（src/sandbox/ugc/config.json L14「生产=msgSecCheck 三态 pass/review/risky·AC-UP1 blocked on 平台资质=CEO 物理件」）→真词库预筛降 msgSecCheck 真实调用配额；README「内置支持单词标签分类分级」标签面可映 review/risky 灰区分层；DFA 算法=本地高性能参照〔Java 库本体不引入 Python 栈·采词库数据面+算法设计参照〕；本地提效类候选=本地运行零 API token+省真实调用配额+一句话映射 ugc L1（canon §一 本地提效注记判据全过）
- **采用→落点**：入池（非即采用）→①司级登记簿入池记录行（docs/oss-harvest/README.md·入池≠采用不入采用表）+main 队列 bootstrap 部署包 ugc L1 接线面指针——接线轮=词库数据文件定位（⑫⑬ 前置）+Apache-2.0 §4 attribution/NOTICE 携带+五门复验+接线判据预注册四前置
- **parked+理由**：adlered/DangerousSpamWords（MIT·97★）=健康门判负留痕（pushed_at=2019-04-26·停更 ~7.5 年）｜词库类活跃替代仓=③④⑤ 三搜索面零命中/污染死面在录（类内普遍停更证实）｜houbb Java 库本体引入 Python 栈=不采（采数据面+设计参照·零栈污染）｜pyahocorasick 等 Python DFA 匹配器线=下窗候选方向（词库接线配套·未深采）
- **下窗指针**：第四窗 10-05 21:40→10-08 21:40·线索=①城市共创区块图像素材工具线（slice1 指针③承·两次顺延在册）②若真钥到位=wechatpayv3+houbb 词库双接线实测件（本窗已备 LICENSE raw 双源验〔三前置之一毕〕+词库定位+判据预注册）③Python 本地 DFA 匹配器线（词库接线配套）

## 一 五门评估（入池件：houbb/sensitive-word）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | ugc 沙箱 L1 闸=词表 mock（src/sandbox/ugc/config.json L14 verbatim 锚：生产=msgSecCheck 三态·AC-UP1 blocked on 平台资质=CEO 物理件）→生产级本地预筛词库真缺口；接线收益=明显干净内容本地放行、命中词本地先拦=降 msgSecCheck 真实调用配额（w2 wechatpayv3 同链=真钥到位前入池备线）；「内置支持单词标签分类分级」=标签分级可映 pass/review/risky 三态灰区；slice2 指针①「msgSecCheck 本地预筛词库面」承接 |
| 2 反重复 | 过 | 三面查证（R597 同律）：cph4/README.md 能力注册表 grep 敏感词/sensitive/msgSecCheck/词库=零命中（2026-10-01 本轮预检）+集团切片面 cph4/oss-harvest 全目录 grep 同词=仅 slice1/slice2 指针行命中（零他司同题切片）+司内 src/sandbox grep=ugc config 词表 mock 仅测试语义（L14 note 明示生产=msgSecCheck）=真缺口非双建 |
| 3 许可 | 过 | 双源直验=GitHub API license spdx_id=Apache-2.0（licensee 机器检测自 LICENSE.txt）+raw LICENSE.txt 原文首段「Apache License Version 2.0, January 2004 http://www.apache.org/licenses/」直采互证；Apache-2.0=直用类（CC0/MIT/Apache/BSD）；GPL 禁入交付链不涉；接线轮携带 §4 attribution/NOTICE 前置在册（w2 raw 复验缺口=本窗已补齐） |
| 4 健康 | 过（例外注记） | stars=6,063·forks=804·open_issues=12·archived=false·pushed_at=2026-03-23T10:35:47Z（~6.3 个月前·越半年活跃线 ~9 天=例外注记：④⑤ 搜索面实证该类仓普遍停更零活跃替代，houbb=类内最活跃主导仓〔6,063★ 对类内第二 adlered 97★·两数量级差〕·updated_at=2026-10-01T07:30:58Z〔采时当日〕·CHANGE_LOG 持续维护在册——「死项目默认不采」例外=类内最活跃+无替代·如实注） |
| 5 成本/安全 | 过 | 本地词库数据+DFA 算法参照=本地运行零 API token 零显存零网络（本地提效三问过）；Java 库本体不引入=Python 栈零新依赖（采数据面·接线轮自写 Python DFA/trie 匹配器或配 pyahocorasick 类=下窗指针③）；纯文本处理库零遥测零外发数据面（源码公开可审）；密钥不涉；非模型类 P-17 矩阵不涉 |

三问门（OSS 寻源 web 直采）：必要=窗 3 正典令文自证（P-2026-09-26-08「寻找开源社区」+P-2026-09-28-01 重申·第三窗 10-02 21:40 起承传）；无本地替代=外部仓元数据/许可原文无本地等效源；宿主既有只读通道（web_fetch+GitHub 只读 MCP+api.github.com 直采）非新 API 接入零密钥——过门在案（R266/R320/R597 先例口径）。

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 入池 houbb/sensitive-word（msgSecCheck 本地预筛词库面+DFA 设计参照·ugc L1 生产接线候选） | ①司级登记簿入池记录行（docs/oss-harvest/README.md）+main 队列 bootstrap ugc L1 接线面指针；采用=接线轮（词库文件定位+Apache-2.0 attribution+五门复验+接线判据预注册四前置） | 入池在册 |
| adlered/DangerousSpamWords（词库·MIT·97★） | ④判负留痕（健康门：pushed 2019-04-26 停更 ~7.5 年） | 已闭环 |
| 词库类活跃替代仓搜索面（any-field+in:name+英文 Python 三面） | ④判负留痕（零命中死面 ④⑤+污染面 ③·类内普遍停更经验证实=slice2 健康预警兑现） | 已闭环 |
| houbb Java 库本体引入 | ④判负留痕（栈不契 Python 后端·采数据面+设计参照零栈污染） | 已闭环 |

## 三 验证声明

读源：外部请求 13 次全录（①②MCP 解析失败如实计+③污染面+④⑤零命中死面+⑨⑫404 死面+⑥⑦⑧⑩⑪⑬ 七次实质得·2026-10-01 ~20:2x-20:3x +08:00·零登录墙零翻页零密钥）。分级：houbb 五门证据=A 级直采（GitHub 官方 API 字段+raw LICENSE 原文双源互证）；「词库数据文件具体路径」=🟡存疑待证（src/main/resources 404+包树首页截断〔api/bs/collection/constant/core/…〕·存在性=repo 描述+README「内置词库」自述互证·全列定位=接线轮前置）；本仓/集团在册锚=cph4/README grep+oss-harvest 切片面 grep+src/sandbox/ugc/config.json L14+R597 slice2 指针行。判据=AC-OH11..OH15（backlog R837 行预注册先于外部请求·自验全过）。台账位=D-20260927-03 ③豁免（本目录=BigDomain 切片件唯一台账位·收账 commit 归收取轮）。
