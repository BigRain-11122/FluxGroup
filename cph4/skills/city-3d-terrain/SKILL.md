---
name: city-3d-terrain
description: 硅基生命城市 3D 线·地编专家技能：地面系统（32m chunk 分块·禁 Terrain 基线确认+高程触发器 ±2m 判据）、水系方案（InteractiveStylizedWater·MIT）、地面细节定序（材质分区→路面件自带标线→decal）、大世界流送（additive 首期/Addressables 三坑检查表+卡顿三律）。当在 City3D 做地面施工、地形处理、水系、贴花或城市扩容时使用。总控=`lowpoly-city-3d`；参数=`docs/lowpoly3d-implementation-params.md` §三。
---

# City 3D 地编专家

## 基线（R-03 落稿精化·2026-09-28）
- 地面=**32m chunk 平面分块**（16×16 for 512m 城），材质分区：路面/广场/草地/水底。
- **禁 Unity Terrain=定谳确认**（设计律[俯视平城无高程需求]+社区 C 级双源负面[移动端 10fps/WebGL instanced terrain 帧率不可用]+Synty 平面网格实查）。
- **高程触发器判据**：>±2m 连续起伏才启高程路径（chunk 顶点位移或 AD-015 台地件堆叠）——平城默认不触发。
- 数据桥：td-organic-data 1 格=8–16m（以 AD-022 路面件实测宽定标·Phase 0 锁定）。

## 水系方案（R-03 A+C 双源）
- **URP 2022.3 无内置水**：官方 com.unity.urp-water-system 停 preview·Unity 2021.3·URP 12·明示非官方支持→**禁装**。
- **主选=InteractiveStylizedWater**（MIT·43★·须开 Depth+Opaque Texture——URP Asset 两开关）；备选=Ameye 免费版（个人站 404·兼容矩阵待证）。装前过核验闸。
- **QuadMesh 绕序判例**（2026-09-29 赛博水 quads 实测）：程序生成 quad 三角形绕序反→法线朝下=单面渲染暗斑/近隐形——正法=统一绕序+法线朝上（「单面朝上律」）或双面材质；自建水面件先验法线方向再铺量。

## 地面细节定序（R-03）
1. 材质分区为主（渐变图集/纯色）；
2. AD-022 路面件自带车道标线/斑马线（优先用件不贴花）；
3. decal 点缀=URP Decal Projector **Screen Space 技术适配瓦片 GPU·禁 DBuffer**（官方文档）；顶点色不适细纹（推测级）。

## 大世界流送（R-03·5000m 参观端路径）
- **WASM 堆默认上限 2048MB→流送必选**。
- **首期（512m）=全场景进首包+additive 最稳**（禁过度工程）。
- 5000m 用 Addressables 须过**三坑检查表**：Content-Encoding 头／IndexedDB DataCaching／bundle 少而大。
- **卡顿三律**：allowSceneActivation 门控+激活分帧+shader 预热。
- 分区粒度=256–512m 扇区（推测·Phase 2 实测定标）。

## 施工 SOP
1. 画布：16×16 chunk 空物体网格（命名 chunk_r{y}_c{x}·prefab 化）。
2. 分区：按 td-organic-data 类别（ROAD/WATER/SAND/PLAZA/PARK）铺地面材质件。
3. 路网：数据驱动铺 SM_Env_Road_*（掩码→件选择·见程序化专家）。
4. 水系：WATER 格→InteractiveStylizedWater 平面+AD-015 岸线件。
5. 微起伏：AD-015 Terrain 件点缀（禁破坏路网对齐·±2m 内免高程）。

## 红线与坑律
- 数据驱动摆放·禁凭手感；引用=AD-NNN；chunk 级 prefab 化=流式前提；地面材质合批友好（渐变图集优先·禁每 chunk 独立材质）。

## 派工模板（后台专家智能体·按需复制即派）
「你是 City3D 地编专家智能体。工程=gaming\FluxVerse\City3D（URP）。任务：[具体地编任务]。基线=city-3d-terrain 技能 v3（32m chunk/禁 Terrain+±2m 高程触发器/InteractiveStylizedWater+QuadMesh 绕序律/细节定序/大世界流送三坑+卡顿三律）。证据件=cph4/research/R-20260928-lowpoly3d-03-terrain.md。改动走 Unity 工具或批建造 SOP；收口=定向提交+JPEG q88 证据图+帧率读数（若涉性能）。」
