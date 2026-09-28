# R-20260928-unity2d-bigmap-oss-docs — Unity 拼接 2D 大地图·官方文档精读窗（CEO 直令·ledger P-2026-09-28-03 第二窗）

> 溯源：ledger P-2026-09-28-03 第二窗（CEO 原话 2026-09-28 ~11:xx「精读各个官方文档 好好全面调研学习」——首窗 R-20260928-unity2d-bigmap-oss 的深读批）·消费方=CEO spike 裁决（Unity-MCP）+FluxVerse 承建线（RuleTile/灰盒/居民行走）·判据预注册=①MCP 双雄 ②Tilemap 官方件+编辑器双生态 ③算法底座+Tuanjie fork 证据。
> 验证声明：精读件 15——GitHub README 7 件（api readme 端点·OH 切片3 通道：coplay/ivan/st2u/ldtk2u/extras/wabba/scenario/wfc）+官网文档 5 处（ldtk.io/docs·doc.mapeditor.org·docs.unity3d.com Manual/Tilemap·coplaydev wiki·redblobgames A*）+**本机官方文档 2 件**（extras@3.1.3 包内 Documentation~/RuleTile.md 全文+LICENSE.md 原文）+PackageCache 直证；死面如实：docs.tuanjie.cn 连接失败·ldtk wiki 页抓取噪声（官网补源）。

## 一、Unity-MCP 双雄精读（spike 选型证据包）

- **CoplayDev/unity-mcp**（README+wiki 精读）：要求=**Unity 2021.3 LTS→6.x**（Tuanjie 1.10.3=2022.3.62t15 在带内）+Python 3.10+（uv）——纯本地 stdio·**零账号零登录**；安装=Package Manager git URL `CoplayDev/unity-mcp.git?path=/MCPForUnity` 或 `openupm add com.coplaydev.unity-mcp`；**47 工具**（manage_scene/manage_gameobject/manage_script/manage_material/manage_physics/run_tests/editor_state/多实例路由…）；v10.0.0（2026-06-30）·Roslyn 脚本校验·ACM SIGGRAPH Asia'25 论文在册·MIT·Discord 社区。
- **IvanMurzak/Unity-MCP**（README 精读）：**Editor+Runtime 双面**（可进编译后游戏=游戏内 LLM 位）·**70+ 工具**+技能自动生成·unitypackage/openupm/npm CLI 三装法·**ai-game.dev OAuth 登录=云账号依赖**·Docker·中文文档·Apache-2.0。
- **选型判定**：CoplayDev 先 spike——零账号与零服务器红线/本地优先最贴；IvanMurzak 为备（Runtime 思想对 M2+ 居民线有价值·云登录面 CEO 裁）。**fork 风险两件同源**：UnityEditor API 面（r99 异名律先例=spriteSheet→spritesheet）——spike 判据预注册：①git URL 包解析成功②编译零红③会话令其建 5×5 Tilemap+截图回传④editor_state 读相为真。

## 二、Tilemap 官方件精读（**本机在盘直证=R-1 勘正**）

- **勘正**：R-1「UPM 可装性待证」被实况推翻——**com.unity.2d.tilemap.extras@3.1.3 已装在 City 工程**（Tuanjie 原生 2D 模板 cn.tuanjie.template.2d 自带·packages-lock L86+PackageCache 双证）——**RuleTile 零安装可用**；官方 2d-extras GitHub 仓已只读（README Notice 原文），正典分发=Package Manager extras 包。
- **RuleTile.md 精读**（包内官方文档全文）：3×3 邻居盒三态（Don't Care/This/Not This）→规则命中即应用 Sprite/GameObject/Collider；**规则变换 Fixed/Rotated(90° 轮转)/Mirror X/Y/XY=一条规则覆盖四向+镜像**（道路/江岸规则资产写法核心）；Output=Fixed/Random(Perlin+Shuffle)/Animation(Min/MaxSpeed)；Extend Neighbor 超 3×3；**规则按命中频率排序**（常用置顶=匹配性能律）；Tile Palette 涂绘同普通 tile。
- **许可门=PASS**（LICENSE.md 原文直读）：Unity Companion License（Unity-dependent projects）+分发实况=Tuanjie 官方模板自带=随引擎正典面。灰盒行动：道路 RuleTile（Rotated）+江岸 RuleTile（Mirror XY）+街区 Random 输出=200x200 灰盒拼接三资产·判据=自动选型截图+断言。

## 三、编辑器双生态精读（Tiled/LDtk+两导入器·parked 维持但知识入库）

- **Tiled**（官方手册精读）：Infinite Maps（无限图·与固定图互转）/Worlds（多文件世界+pattern matching 邻接显隐）/Terrains 地形笔刷（概率+变换+填充模式）/Automapping（规则图自动贴图）/Tile 动画+碰撞编辑器/层视差-tint-blend/JSON+TMX 双格式——**手工大地图编辑全功能面在册**。
- **SuperTiled2Unity**：ScriptedImporter=Tiled 保存即自动重导入（免导出步）·itch.io 免费分发·readthedocs 文档。
- **LDtk**（官网 docs 精读）：**World 三布局=Grid-vania（大地图自动分区）/linear/free+多关卡拖拽重排**（R-1 🟡 项就此转 ✓）；Auto-rendering=视觉规则自动贴皮（同 RuleTile 思想）；Aseprite 直载+live reload；JSON 有文档+Tiled TMX 可选导出；v1.5.3·《Dead Cells》导演出品·平台聚焦 platformer/俯视角。
- **LDtkToUnity**：openupm com.cammin.ldtkunity·2019.3+·实体 prefab 替换+字段导入+自动枚举生成·SpriteAtlas 拆分·独立关卡文件支持·后处理脚本 API——导入管线知识完备。
- 维持 parked：与 manifest 单一源正典不并轨；重评条件不变（人类手工绘制地图内容需求出现时）。

## 四、算法底座与生态件精读

- **Red Blob Games A***（实现页精读）：三表实现法（frontier=open 集/came_from 父指针/cost_so_far）——**样例代码明示 Apache v2 许可可直用**（2026-08 仍在更新）=居民「走路上班回家」直接算法底座·许可干净可抄（能抄就抄令正面样本）。
- **WFC**（mxgmn README 精读）：观察（最低熵坍缩）-传播循环·N=3 局部相似·矛盾可能（NP-hard 罕见）——无 LICENSE 文件=采用判负·仅思想学习（OH 观察位维持）。
- **wabbajack16 样本**：柏林噪声+高度阈值+**边界过渡规则**（sourceType/adjacentType/transitionSet/priority 资产化=RuleTile 同族思想）+Job System/Burst 并行+chunk 卸载示例——超大世界线可学实现件。
- **scenario-labs/skills**：65 技能·agentskills.io 技能格式（Claude Code/Cursor 等 70+ 客户端）——**判负**（Scenario MCP 云平台依赖+与 TJGenerators 同模型族撞面禁双建）；留存价值=技能写法参照（其 scenario-seedream 技能=Seedream 同族·印证 TJGenerators 选型不孤证）。

## 五、Tuanjie fork 面证据汇总

- docs.tuanjie.cn=连接失败（死面如实）；**本机证据链 A 级**：extras@3.1.3 随 Tuanjie 原生模板入盘+TECH r8 2D 全家桶自检通过+r99 异名律先例（fork API 有改名风险面）→ 结论=**瓦片拼接面 fork 兼容已实证·MCP 桥面待 spike**（判据 §一）。

## 六、结论应用表（research-protocol §二.1 强制）

| 结论 | 落点 | 状态 |
|---|---|---|
| ①RuleTile 在盘直证+精读+许可 PASS（R-1 勘正） | 任务单升级：@FluxVerse 承建位「灰盒三规则资产」（道路 Rotated/江岸 MirrorXY/街区 Random·判据=自动选型截图+断言） | 接线中（待承建轮领） |
| ②CoplayDev 先 spike 判定+四步判据包 | 决策呈报：@CEO 一句话裁「测」（判据包 §一） | 接线中（待 CEO 裁） |
| ③A* 三表法（Apache v2 可抄） | 任务单：@FluxVerse 承建位 M2 居民行走线（走路上班回家）算法底座 | 接线中（随转向令居民项） |
| ④Tiled/LDtk/两导入器功能知识入库 | 参照面入库（本件 §三·重评条件不变 parked） | 已闭环 |
| ⑤WFC/scenario-skills/wabbajack16 学习注记 | 判负留痕+观察位注记（§四） | 已闭环 |

- 更新记录：T0 骨架 → T1 README 8 件落盘+PackageCache 直证（勘正发生）→ T2 5 小件精读+官网 4 处 → T3 大件三精读+本地官方文档 2 件+许可门 PASS → 终稿 52 行。
- 防线二：两承重主张双源——①extras@3.1.3 在盘（packages-lock.json L86+PackageCache 目录树双证）②Unity-MCP 2021.3→6.x 要求（README Quickstart+wiki 双页同值）；重读磁盘态后收口。
