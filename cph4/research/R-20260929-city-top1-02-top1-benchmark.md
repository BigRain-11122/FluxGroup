# R-20260929-city-top1-02-top1-benchmark — 俯视角低模城市「头部Top1」标杆与可量化视觉判据（CEO 令 2026-09-29·02 波）
> 溯源：CEO 令 2026-09-29 原话「我对polygon资产的使用很不满意，对硅基城市的搭建效果很不满意，怎么做到头部top1你们自己去研究，不要给我看垃圾」·消费方=City3D 施工线·判据预注册=Q1 头部标杆双面（游戏成品+场景艺术·每标杆「为什么头部」要素拆解带源）/Q2 可量化视觉判据（密度/色彩/光影/后处理/构图·尽量可测可机检）/Q3 判据对双机位（L0 俯视 320m 总览+L2 街景 24m）适配三态
> 验证声明：web 读取 20/20 帽（search 6+fetch 14·其中 4 读空/403·1 读判弃）；成源=外采 A=3（Synty 官方产品页·Tiny Glade Steam 官方页·pouncelight 官网弱 A）+仓内复用 A=2（DCP 奖·Synty 范式）·B=4（80.lv×2 直引访谈·维基 Townscaper·Steam 页内 B 级媒体语）·C=3（LinkedIn Oskar 直引·shapes.inc 待证·indienomicon 判弃）；关键结论 A/B 双源达标；失败面文末透明列出。三态=确认/推测/待证。

## 一、标杆面（Q1：头部是谁·为什么头部·「top1」定位=本波按口碑/奖项/销量数据推定）
- **Tiny Glade（2024·Pounce Light 二人组）=品类口碑头部**：Steam 好评如潮 97%（13,902 评·近 30 天 98%）[确认·A Steam 官方页直读]+首月 ~61.6 万份/$15 [确认·B×2 仓内 R-20260928-polygon-style 复用]；头部要素=①gridless 建造+「游戏自动装扮」：画路径自动开门·抬楼自动生柱梁·常春藤包覆·萤火虫点夜 [确认·A Steam 自述] ②「whatever you make will look cozy out of the box」=系统保证任意操作出片 [确认·A] ③自研 Vulkan 管线全控「从资产授权到全部渲染 pass·目标体验先行再设计管线」[确认·B 80.lv 开发者直引] ④渲染师 dev 本人开讲《Rendering Tiny Glades With Entirely Too Much Ray Marching》[待证·仅获视频标题页] ⑤用户标签 Top-Down/Stylized/Colorful/Atmospheric [确认·A] ⑥GameStar「truly magnificent visuals」[确认·B]。
- **Townscaper（2021·Oskar Stålberg 单人）=品类美感模因源**：Metacritic PC 86 [确认·B 维基]；头部要素=①「比真实城建的 sterile metropolises 更 instantly homely」（PC Gamer）[确认·B] ②波函数坍缩拼手工件+规则装饰（拱/花园/悬楼/楼梯自动出现）[确认·B 维基+C Oskar 直引] ③变形网格于无限海→有机街巷·对抗方格感 [确认·B] ④反程序味律=算法约束+手工细节混布（烟囱/屋顶随机变体·窗/邮箱手工布点）[确认·C Oskar 直引] ⑤移植法则=自写光照+简化环境光+描边+自定 shader 保清晰 [确认·C Oskar 直引]；维基正式归类「Video games with low poly graphics」[确认·B]。
- **Dorfromantik（2021·Toukana）=俯视角低模可读性标尺**：DCP 德国电脑游戏奖双冠（新人奖+最佳 game design）[确认·A 仓内复用]+80.lv 定位语「most recognizable examples of minimalist cozy game design」[确认·B]；头部要素=①极简支柱+工作室内律「This is creating too much visual noise」一票否决 [确认·B 直引] ②早期美术风格表七要素：shapes/proportions/atmosphere/lighting/colors/textures/perspective [确认·B] ③资产全程按「slight top-down」游戏视角逐角度验轮廓 [确认·B——与我方机位同族]。
- **场景艺术侧头部=Synty 官方 showcase（Palm City 旗舰包）**：$299.99·1,100+ prefab=Buildings 309+Props 419+Environment 137+FX 13（含 Ground Fog）+Characters 20·贴花 graffiti/grunge/weathering·「Highly detailed, expansive demo scene」[确认·A 官方产品页直读]——官方城的道具:建筑配比 419:309≈**1.36:1**=密度自证；模块化 grid+demo=说明书+共享图集单材质换色范式 [确认·A×7 仓内 R-20260929-synty-usage-doctrine 复用]。
- 互指件：ISLANDERS（2019）=维基 Townscaper 词条「See also」互指的极简城建 [确认·B 指针·观察位未深采]。

## 二、可量化判据面（Q2·逐条可测）
- C1 单资产主色 ≤5：Dorfromantik 顶点色 5 通道硬帽（「more colors within a small asset would create too much noise」）[确认·B]——机检=色板/顶点色通道计数。
- C2 灰度价值结构先行：「regularly check everything in grayscale to validate the value structure——readability through value，色相与饱和度后置」[确认·B]——机检=截图灰度化后明度分层可辨。
- C3 色板手选+引擎级 biome 色组（场景级协调·Synty 换色=图集 UV offset）[确认·B+C 仓内]——机检=同屏 hue 直方图离散度。
- D1 密度配比：道具:建筑≈1.36:1（Palm City 官方 419:309）[确认·A]——机检=街区 prefab 计数比。
- D2 屋顶/门面细节律：烟囱·窗·邮箱类小件必布+随机变体反程序味（手工布点思想）[确认·C Oskar+A Tiny Glade 装扮自述]。
- D3 装扮反馈律：任意建造/装配动作必触发细节（门/柱/常春藤/卵石）[确认·A]。
- L1 光照极简律：单太阳光+阴影提亮（禁黑死）+极淡雾·「用色定义光而非光系统」[确认·B]。
- L2 烘焙 AO 逐资产+描边贴图（Blender/SP/fresnel in Unity）[确认·B]。
- L3 夜景=重涂色组不重打光（Night Mode=新增 biome）[确认·B]。
- L4 描边+自定 shader 替代重光照保清晰（移动/低配口径）[确认·C Oskar]。
- L5 Tiny Glade 软影/全域光 ray marching 自研级 [待证·C 单源·演讲页无正文]。
- P1 后处理轻栈：仅「雾」多源确认（Dorfromantik subtle fog [B]+Synty Ground Fog FX 件 [A]）；bloom 等完整 PP 栈头部三作均无官方公开清单 [待证·零源]。
- F1 非均匀/变形网格→有机街巷（gridless/distorted grid 双源）[确认·A+B]。
- F2 封闭空间→自动绿地花园=疏密呼吸 [确认·B+C]。
- F3 大形优先·轮廓可读（silhouette-first·基本形精心拼合）[确认·B]。
- F4 diorama 心理框架（Tiny Glade「small diorama builder」·Townscaper 海岛玩具）[确认·A/B]。

## 三、俯视角专项面（双机位特化）
- Dorfromantik 全资产按「slight top-down」视角验证=俯视角低模头部已实证的视角纪律 [确认·B]。
- Tiny Glade 标签面同时含 Top-Down（建造）与 First-Person（赏景）=双机位策略在 top1 作实证 [确认·A]。
- 分层推定 [推测·由上推导]：L0 320m 俯视=色块拼贴读法→C1 升格为「街区级色数帽」+C2 灰度整图校验+F1/F3 大形判据主导；L2 24m 街景→D1/D2/D3+L1/L2/L4+P1 近景判据主导。

## 四、适配结论面（Q3 三态）
- **直接采用**：C1·C2·C3·D1（1.36:1 配比）·L1·L2·L3·P1 雾·F1·F2·F3——全部可在 URP+Synty 管线直落；与仓内 city-3d-lighting 技能（AO 烘焙/日夜色轮/雾）同向，法参可校准互证。
- **需改造**：D3 装扮反馈→改「装配后自动补细节层」（贴花/小件散布·非交互玩法件）；D2 手工布点→改数据驱动点位表；L4 描边→320m 俯视收益存疑+24m 与 Synty 平涂风格可能冲突 [推测·两件 PoC 定]；F4 diorama→取「每视野 1 焦点地标」要素·弃整体玩具感。
- **不适用**：L5 ray marching 自研渲染（URP 管线异构·双人组全控管线成本不成立）；Townscaper WFC 实时生成（我方静态城非玩法件·装饰规则思想可借·引擎件不适用）。
- 张力注记：我方法参现有 bloom（city-3d-lighting）在标杆面零确认——标待验（不判负不判采用·PoC 后定）。

## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 色彩三律 C1-C3+密度配比 D1+构图 F1-F3=装配 SOP 验收判据增补 | 任务单：City3D 施工线 | 接线中 |
| 光影四律 L1-L3+P1 雾对表 city-3d-lighting 技能法参 | 法文修改候选：URP 光照法参校准+bloom 待验注记 | 接线中 |
| 三件 PoC（320m 描边·装配后装扮层·焦点地标构图） | 任务单：City3D PoC 批次 | 待派 |
| L5 ray marching+WFC 实时生成=技术路线排除 | 判负留痕 | 已闭环 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 游戏侧三标杆面（Dorfromantik/Townscaper/Tiny Glade）→ T2 Synty 官方 art 面+Palm City 密度数字 → T3 Tiny Glade Steam A 级补采 → T4 判据提炼+俯视特化+适配三态 → 终稿 55 行。
- 失败面：gamedeveloper.com Townscaper 深访 403·ArtStation 低模城代表作页 403（ArtStation 域名 art 侧标杆位改由 Synty 官方页承担·待证）·YouTube《Rendering Tiny Glades》仅吐样板（L5 降级待证）·pouncelight.games 官网 SPA 无正文（163 字符）·indienomicon 侧写与 A/B 源矛盾（「一群朋友」vs 80.lv 二人组·NPC/资源管理机制不见于官方）判 C 弃承重·Tiny Glade GI/时序=C 单源·完整后处理栈零官方源。
- 防线二建议：直读 80.lv Dorfromantik 访谈抽验「顶点色 5 通道」与「灰度校验」两句+直读 syntystore Palm City 页抽验 419:309 两承重主张。
