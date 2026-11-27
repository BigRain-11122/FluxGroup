---
name: city-3d-assembly
description: 硅基生命城市 3D 线·装配专家技能：Synty POLYGON 装配范式（乐高式模块拼装·官方 75 demo=老师）、四阶段定式（blockout→验证→dress→优化）、prefab variants 律、多场景 additive 三坑、构图密度（Phase 0 demo 实测收口）。当在 City3D 做街区装配、场景编辑、建筑摆放或 demo 学习时使用。总控=`lowpoly-city-3d`；映射表=方案 §四。
---

# City 3D 装配专家

## 装配律（总控承接+R-05 落稿精化）
- **乐高式模块拼装**=Synty 官方正法（官方 demo 拷 B+官方《Modular Buildings》教程·R-05 A 证）；换色=挪 UV（R-02 A×2 承接·**坑：Tiling/Offset 连带错色——改前查共享图集归属**）。
- 数据驱动（td-organic-data 同源·禁手感）；引用=AD-NNN+一句话。
- **官方 demo 场景=老师+用法说明书**（R-20260929-synty-usage-doctrine A 证：demo=包体标配·官方当活文档维护·Sketchfab 公开预览·Starter Pack 自证「learning the Synty art style」）：75 个演示场景——**帧账已全量捕获在库**（`MiniGame/projects/P3D_Spike/P3D_Spike-staging/demo-study/` 156 帧·79 场景·三核心城市场景深读结论=48 包索引 §八），提炼范式再自建，禁从零发明；**开采节奏=用到该包再深读+挖毕落账**（资产利用律 §二·查账先于浏览）。
- 起步 6 包=AD-048 白盒→AD-022 街区→AD-015 植被→AD-042 人物→AD-010 粒子→AD-039 图标。

## 四阶段定式（R-05·B 教科书+C 双源同构）
1. **Blockout**：AD-048/AD-025 白盒件按结构锚摆（脑环 r40/三城 r180）——只摆体量与动线。
2. **玩法规+相机角验证**：相机三档过一遍构图再继续。
3. **Dress**：逐区替换成品件（AD-022 街区/AD-002 店面/AD-018 科幻件）+道具点缀。
4. **优化烘焙**：只烘 AO+Light Probes（灯光专家基线）。

## 组织与坑律
- **Chunk 化**：32m chunk=一个 prefab（chunk_r{y}_c{x}）——流式加载与复用前提。
- **Prefab variants 律**（R-05 A 证）：慎 apply 回写（变体覆盖基座）·删件用 deactivate 代删（保变体可回溯）。
- **多场景 additive 三坑**（R-05·大世界流式预用）：跨场景引用禁／光照与 NavMesh 数据按场景存／异步加载时序。
- **YAML 局部坐标陷阱**（P3D spike 实测）：AD-022 demo 场景 PrefabInstance 的 m_LocalPosition=局部坐标——裁街区/抄构图必须用引擎世界包围盒法，勿按 YAML 坐标直读。
- 撞名律（U272）+收件三查（U282）+JPEG q88 证据律照旧。
- **相机角双档参照**（R-05 C 级收敛·数学核验）：真等距 35.264°（=atan(1/√2)）与经典斜角 ~60° 双惯例档+90° 纯顶特殊档——参数单现选 50–60° 带位于经典斜角侧。

## 待证收口路径（Phase 0 仓内实测·网面零命中在案）
- Build 2.0 统一网格米数官方未公开→**仓内实测 SM_Env_Road_* bounding 收口**（1 格=8–16m 定标即此）。
- 每 32m chunk 构图密度→**75 个官方 demo 实测**取分布。

## 派工模板（后台专家智能体·按需复制即派）
「你是 City3D 装配专家智能体。工程=gaming\FluxVerse\City3D（URP）。任务：[街区装配任务]。基线=city-3d-assembly 技能 v3（四阶段定式·乐高式拼装·chunk prefab 化·variants 律·YAML 世界包围盒法·demo=说明书+按需开采落账）+映射表（方案 §四）。先读 cph4/research/R-20260928-lowpoly3d-05-assembly.md。收口=远/近双轨截图+多模态抽件体检+定向提交。」
