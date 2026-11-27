---
name: city-3d-procedural
description: 硅基生命城市 3D 线·程序化专家技能：散布双轨制（自写最小 scatter 主径+PrefabScatterTool 手涂补笔）、16 方向掩码→AD-022 路面件映射选择器、建筑足迹校验（XZ 半径法+Y Raycast）、Y 排序不承袭律（URP Decal）、扩展期参数化街区填充（结构锚内）、WFC 不引入判定。当在 City3D 做程序化散布、数据驱动摆放算法或城市扩展填充时使用。总控=`lowpoly-city-3d`；判定律=只做重复件分布不做城市结构。
---

# City 3D 程序化专家

## 判定律（CEO 令已定谳·不可破）
- **程序化只做「重复件分布」，不做「城市结构」**——一核一环三城/路网骨架=设计数据驱动，禁随机生成。

## 散布双轨制（R-06 落稿定谳·2026-09-28）
- **主径=自写最小 scatter**（数据驱动批摆+`Random.InitState` seed 确定性·A 证）——可控/可复跑/可对账，产出=chunk 级 prefab。
- **补笔=PrefabScatterTool**（MIT 双源验·v0.1.0/0.1.1 极早期·Editor 手涂件·无 seed/密度图/批量 API 证据）——只做编辑器手工补景，**不进 WebGL 包**；装前过核验闸。

## 数据→摆放算法（R-06 精化）
1. **道路件选择=16 方向掩码→AD-022 路件映射表**（N=1/E=2/S=4/W=8 的 3D 版·邻接掩码查 SM_Env_Road_* 对应件：直段/Crossing/T 路口/端头——C×2 社区参考+仓内锚件实测）。
2. **建筑足迹校验**：2D 半径法平移 XZ（候选=路 2 格内地格·校验半径<候选-路距离·2D 实错判例防重蹈）；**Y=Raycast 打地面高**（贴地摆放）。
3. **Y 排序 2D 律 3D 不承袭**（Unity Manual sprites-sort+SortingCriteria A×2 直读）：3D 遮挡靠深度缓冲自然正确；透明件（玻璃/光晕）走 URP Decal 或控件数控制。
4. 摆放输出=chunk 级 prefab（与装配专家对接·seed 固定可复跑）。

## 扩展期街区填充（R-06 剥离法）
- Procedural-City（Poofy1·MIT）：**剥其生成/路网层（结构层·判定律禁），只取参数面**——blockWidth→lot 细分·楼高 seed 随机+区位钳制——锚内填充用。
- **WFC 本期不引入**（mxgmn 原作直读：NP-hard 无恒完成保证；16 掩码已覆盖路件连通·邻接约束贫乏收益<成本）；强邻接素材族出现时重评。

## 派工模板（后台专家智能体·按需复制即派）
「你是 City3D 程序化专家智能体。工程=gaming\FluxVerse\City3D（URP）。任务：[散布/算法任务]。判定律铁则=只做重复件分布不做城市结构。基线=city-3d-procedural 技能 v2（散布双轨·16 掩码映射·足迹校验 XZ+Raycast·Y 排序不承袭·WFC 不引入）。证据件=cph4/research/R-20260928-lowpoly3d-06-procedural.md。产出=可复跑脚本+seed 固定+对账断言（件数/分布），收口=定向提交+截图证据。」
