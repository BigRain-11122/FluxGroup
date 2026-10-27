# OH-20260929-minigame — 开源收获轮·MiniGame 实体首片（City3D 工具径收账）

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40；本切片=2026-09-29（MiniGame 实体首片·补值守轮点名面·正典=cph4/oss-harvest.md v1.0）。本实体业务面=Biggame 产线（小游戏款包 G01-G17+吸嘟嘟上线链）+**City 3D 全面开工线**（CEO 令 09-28 22:5x「全面开工lowpoly…全量并行」·City3D-staging 真缺口清单八行在册）+Unity/Tuanjie 工程面。
- **反重复门基线**：①City3D 库内优先律（CEO 令「一定要好好利用我的lowpoly资产」）=48 包库内件主径不变——本窗候选全部为**缺口清单在册工具径**（库内无此能力才评估·真缺口判定已毕）；②Unity-MCP 三件/RoadArchitect 已在 P-2026-09-28-05 普查件与缺口清单点名（本片=正式五门收账非重复建档）；③cph4/README 注册表零撞。
- **实搜面（4 处 A 源直验·采时 2026-09-29 ~11:1x）**：①api.github.com/search q=RoadArchitect+unity=5 件（MicroGSD 原版 989★·MIT·pushed 2020-08-25 stale／**FritzsHero fork 365★·MIT·pushed 2026-09-28 当日**）；②api.github.com/search q=InteractiveStylizedWater=mozankatip/InteractiveStylizedWater 43★·**MIT**·pushed 2023-05-05；③缺口清单原文直读（City3D-staging/library-utilization-map.md ①②两线）；④两仓许可字段 API 直验。

## 一 五门评估

### 1. FritzsHero/RoadArchitect（MIT·365★·工具径·Phase 2 消费）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | City3D 缺口①真缺口判定原文「复杂立交/异形路口=Phase 2 RoadArchitect 工具径评估」——主径 AD-022 八件族 8m 正交骨+曲段折线逼近技法（≤15° 转角）在库内已锁；**复杂立交/匝道**=库内零能力→本件=运行时道路网生成/编辑工具（节点/样条/匝道/交叉自动建面）。「替谁省什么」=Phase 2 若上立交→手工建模每座 vs 工具参数化 |
| 2 反重复 | 过 | 普查件 P-2026-09-28-05 已点名在册（本片=五门正式收账）；库内 48 包零道路网生成工具（缺口清单实勘）；与 Tiled/WFC 族（地图拼接）不同域（那是 2D 图块·这是 3D 道路网）零撞 |
| 3 许可 | 过 | **MIT**（API license 直验·fork 全继承上游 MicroGSD MIT） |
| 4 健康 | 过（带注记） | 365★·72 forks·**pushed 2026-09-28（采时当日）**=活跃维护 fork；注记=上游 MicroGSD 原版 989★ 但 2020 年后 stale 6 年——**采 FritzsHero 维护版·上游注记留痕** |
| 5 成本/安全 | 过 | 纯本地 Unity 工具零网络；Phase 2 才开窗评估接入（零当前成本）；URP 兼容性=开窗首验判据（缺口清单参数单 URP 定谳后一切工具须过 URP 桥） |

### 2. mozankatip/InteractiveStylizedWater（MIT·43★·工具径·观察位）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | City3D 缺口②真缺口判定原文「水面 shader：48 包无水面材质件（仅 AD-015 岸线件）→ InteractiveStylizedWater（MIT·43★·装前过核验闸·工具径）」——硅基城黄浦江带（city-layout-data WATER=565 格）需要可交互风格化水面；「替谁省什么」=水面 shader 自研（波纹/岸边泡沫/反射）整线 vs 成品参照 |
| 2 反重复 | 过 | 缺口清单点名在册；库内零水面材质（实勘）；自研线=活性方案波②③的发光条 shader 同族技法——本件=成品参照+可用件候选双位 |
| 3 许可 | 过 | **MIT**（API license 直验） |
| 4 健康 | **观察（如实注记）** | 43★·pushed 2023-05-05（**2 年+ 无维护**）——健康门缓活如实降档：不直装主干、按「学实现+必要处抄」定位（CEO「能抄就抄」边界内）+装前过核验闸（缺口清单原话） |
| 5 成本/安全 | 过 | 本地 shader 包零网络；WebGL 面=装前判据（活性方案红线：VFX Graph 禁入 WebGL 演出面——本件须验 WebGL 构建兼容再入） |

## 二 采用→落点（2 件全 Phase 2 工具径·认领后收账）

1. **RoadArchitect（FritzsHero 维护版）**→落点=City3D Phase 2 立交/匝道窗的工具径候选：开窗判据三件（URP 桥兼容/节点-样条 API 可编程性/WebGL 构建体积影响）——缺口清单 ① 真缺口行注记「本片收账·Phase 2 消费」。
2. **InteractiveStylizedWater**→落点=水面 shader 窗参照件：学其波纹+岸沫实现（MIT 可抄）+WebGL 兼容验后定直装/学实现——缺口清单 ② 真缺口行同款注记。

## 三 parked+下窗指针

- parked：MicroGSD 上游原版（989★·stale 6 年·维护版优先原则）；RoadBuilder 同族未验（下窗按需）。
- 下窗：①Phase 2 开窗时两判据件回执；②MiniGame 第二刀=运营接入面（微信小游戏云开发/性能分析工具族）按吸嘟嘟上线链需求续挖。
