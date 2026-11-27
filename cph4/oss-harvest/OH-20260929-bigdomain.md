# OH-20260929-bigdomain — OSS 借力第二窗切片件（BigDomain）

- **窗**：次窗 2026-09-29 21:40 → 2026-10-02 21:40（P-2026-09-26-08+P-2026-09-28-01 承传·正典=cph4/oss-harvest.md v1.0）·交付 2026-09-29 ~16:2x +08:00（窗开前 ~5h 提前交付·R320 窗内提前 ~71h 先例的窗前延伸·提前依据=候选证据窗期稳定+slice1 下窗指针①直查仓线索预置·如实注）
- **实搜面**（4 次外部请求全录·采时 2026-09-29 ~16:2x +08:00·宿主只读通道零登录墙零翻页零密钥）：
  - ①GitHub MCP search_repositories `wechatpayv3 in:name` → 响应解析失败如实记（上游调用按发生计·工具面解析异常）
  - ②GitHub MCP get_file_contents `minibear2021/wechatpayv3 /LICENSE` → 同解析失败如实记（许可验证改道双源面见 §一 门 3）
  - ③`github.com/minibear2021/wechatpayv3` repo 页直采：1.3k★·fork 179·249 commits·MIT 标注·Python·「微信支付 API v3 Python SDK」·直连+服务商双模式·回调解密/账单下载/消费者投诉 2.0 接口在册
  - ④`api.github.com/repos/minibear2021/wechatpayv3` 元数据直采（A 级）：stars=1338·pushed_at=2026-09-11T02:23:50Z（18 天前）·open_issues=1·license spdx_id=MIT·default_branch=master·archived=false·created=2021-04-14
- **候选**：minibear2021/wechatpayv3（https://github.com/minibear2021/wechatpayv3 · MIT · 1338★ · 契合点=pay 沙箱 v3 适配器〔R555 callback_style:v3 opt-in·STANDIN 真钥占位三注记〕的真钥接线实现缺口：真实 RSA 签名/平台证书/回调 AEAD 解密/账单下载全量官方 V3 面）
- **采用→落点**：入池（非即采用·真钥=CEO 物理件）→①司级登记簿入池记录行（docs/oss-harvest/README.md·入池≠采用不入采用表）+main 队列 #1 bootstrap 部署包 pay 接线面指针——接线轮=LICENSE raw 原文复验+五门复验+接线判据预注册三前置（R576 §五 执法承）
- **parked+理由**：官方 wechatpay-apiv3 org 工具族（certificate-downloader 等=Go 栈证书工具非 Python SDK·栈不契本司后端·🟡常识别面未深采）｜自研扩展线（sandbox v3.py 站位面全量自研签名/解密 vs SDK 采用=接线轮裁量项·R555 在册）｜slice1 FACE2 污染查询词线（已绕开·直查仓法兑现=闭环）
- **下窗指针**：第三窗 10-02 21:40→10-05 21:40·线索=①msgSecCheck 本地预筛词库面（slice1 指针②承·健康门风险预警=该类仓普遍停更·直查活跃仓优先）②城市共创区块图像素材工具线（slice1 指针③承）③若真钥到位=接线实测件（LICENSE raw 原文复验+SDK 实装判据预注册先行）

## 一 五门评估（入池件：minibear2021/wechatpayv3）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | pay 沙箱 v3 适配器真钥接线缺口直补（R555：v3.py V3Channel=callback_style:v3 opt-in·真实 V3 验签串式 HMAC 站位 RSA·resource 信封可逆站位译码·STANDIN 三注记=真钥/平台证书 CEO 物理件）；src/sandbox grep `wechatpay`=零命中（mock 自足·AC-Y4 四坏例自造）=真实现缺口；P-47-4 19.9 支付对接旗舰路径；slice1 指针①「直查 wechatpayv3 仓绕开污染查询词」兑现 |
| 2 反重复 | 过 | 三面查证：cph4/README.md 能力注册表 grep `wechatpay|微信支付|wechat.pay|支付 SDK`=零命中+集团切片面 cph4/oss-harvest 全目录 grep 同词=仅本司 slice1 指针行命中（零他司支付 SDK 切片）+司内 sandbox 零真 SDK import=真缺口非双建 |
| 3 许可 | 过 | 双源直验=GitHub API license spdx_id=MIT（licensee 机器检测自 LICENSE 原文）+repo 页「MIT license」标注互证；MIT=直用类（CC0/MIT/Apache/BSD）；GPL 禁入交付链不涉；raw LICENSE 原文直采因 4 次请求预算未做=接线轮 raw 复验前置（§二 表在册·如实注） |
| 4 健康 | 过 | stars=1338（repo 页 1.3k 互证）·pushed=2026-09-11（18 天前·半年内活跃线内远优）·open_issues=1（对 1338★ 极低占比）·archived=false·249 commits·QQ 群+discussions 运营面在册=非死项目 |
| 5 成本/安全 | 过 | 本地 Python 库（本地优先三问过）；网络调用仅指向微信支付官方 API 端点=生产必需面（真钥=CEO 物理件·密钥只进 .env 律）；依赖常规栈（cryptography 加解密族）；MIT 开源可审+repo Security policy 面在册；非模型类 P-17 矩阵不涉零显存 |

三问门（OSS 寻源 web 直采）：必要=窗 2 正典令文自证（P-2026-09-26-08「寻找开源社区」+P-2026-09-28-01 重申·次窗 09-29 21:40 起承传）；无本地替代=外部仓元数据无本地等效源；宿主既有只读通道（web_fetch+GitHub 只读 MCP）非新 API 接入零密钥——过门在案（R266/R320 先例口径）。

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 入池 minibear2021/wechatpayv3（pay V3 SDK·bootstrap 真钥接线候选） | ①司级登记簿入池记录行（docs/oss-harvest/README.md）+main 队列 #1 bootstrap pay 接线面指针；采用=接线轮（LICENSE raw 原文复验+五门复验+接线判据预注册三前置） | 入池在册 |
| 官方 wechatpay-apiv3 org 工具族（Go 栈） | ④判负留痕（栈不契 Python 后端·🟡常识别面未深采） | 已闭环 |
| 自研扩展线（v3.py 站位面全量自研 vs SDK） | ②调研件引用（R555 在册·接线轮裁量项） | 已闭环 |
| slice1 FACE2 污染查询词线 | ④判负留痕（直查仓法绕开兑现） | 已闭环 |

## 三 验证声明

读源：外部请求 4 次=GitHub MCP search（解析失败如实计）+GitHub MCP LICENSE 取件（解析失败如实计）+repo 页 web_fetch+api.github.com 元数据直采（2026-09-29 ~16:2x +08:00·零登录墙零翻页零密钥）。分级：候选五门证据=A 级直采（GitHub 官方 API 字段+repo 页双源互证）；「官方 org Go 工具族」=🟡存疑待证（常识面未深采）；本仓/集团在册锚=cph4/README.md grep+cph4/oss-harvest 切片面 grep+R555 pay v3 适配器记录+src/sandbox grep 实勘。判据=AC-OH6..OH10（backlog 本行预注册先于外部请求·自验全过·门 3 改道注记如实）。台账位=D-20260927-03 ③豁免（本目录=BigDomain 切片件唯一台账位·收账 commit 归收取轮）。
