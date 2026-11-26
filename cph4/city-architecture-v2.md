# 硅基城市 · 架构 v2（模块化重构，2026-11-26）

> CEO 令：「把这些顶层设计思路重构，并能模块化开发，从我们现在已有的基础上迭代。」
> 本件=**重构后的顶层设计 + 模块边界 + 迁移路线**。原则：**不重写、不换引擎、不引物理库**，
> 只把已有的东西按边界收拢，让"加一个系统"不再需要动主循环。

## 一、为什么重构（用实锚说话）

重构前 `src/main.ts` 的渲染循环里有 11 行手写调用，11 个模块用了 **5 种不同的 update 签名**：

```
daynight.update()                          // 无参
messengers.update(elapsed)                 // 只要世界时间
robots/residents/traffic/weather(dt, elapsed)
pedestrians/vehicles(dt, elapsed, hour)    // 还要城市小时
cameraRig.update(dt)                       // 相机单算
```

后果三条：①谁先跑靠书写顺序；②想给慢系统降频只能加 if；③加任何一个系统都要改主循环，
主循环逐步变成上帝类。**这是"能不能模块化"的真正卡点，不是目录好不好看。**

## 二、三层结构（依赖只许向下）

```
L3  play/       玩家、交互、镜头模式        ← 可读 L2/L1/L0，不许被下层 import
L2  sim/        智能体在场/相遇/需求         ← 读 L1；产出的轨迹交给数据面
L1  live|world/ 交通/行人/天气/建筑/居民外观  ← 只读 L0 与数据
L0  core/       内核：Frame / System / World / rng  ← 不 import 任何上层
```

**铁律**：`core` 不认识业务；`world/live` 不知道玩家存在；`play` 只写"玩家自己的意图"，
不写 NPC 状态（承 `city-foundation.md` 单一写入者矩阵）。

## 三、模块地图（现有文件 → 所在层）

| 层 | 现有文件 | 状态 |
|---|---|---|
| `core/` | `system.ts`（System/Frame 契约）、`world.ts`（注册表+帧预算） | ✅ 本轮新建 |
| `world/` | `city/layout`、`city/buildings`、`city/roads`、`city/masts`、`city/rooftops`、`city/landmarks-*`、`city/brainTower` | 已有，未搬目录 |
| `live/` | `live/daynight`、`live/weather`、`live/traffic`、`live/pedestrians`、`live/vehicles`、`live/dust`、`live/messengers` | 已有，已注册进内核 |
| `sim/` | `city/residents`（按拍回放）、`city/robots` | 已有；真正的 sim 在 BigLife 侧 |
| `play/` | `player/controller`（S1 可走切片） | ✅ 本轮新建 |
| 数据面 | `types.ts`、`data.ts`、`window.CITY_DATA` | 已有 |
| 后端协作 | BigLife `city_agents.py` / `city_bridge_export.py` | 已有（见 city-foundation.md） |

**注意：本轮不搬目录。** 搬目录会产生大面积 import 变更，收益只是"好看"；
先把**依赖方向**和**系统契约**立住，目录搬迁放到 P2 且单独一次提交。

## 四、System 契约（唯一新增抽象）

```ts
interface System {
  id: string;                  // 唯一，重复注册直接抛错
  layer: "world"|"sim"|"live"|"play"|"ui";
  hz?: number;                 // 0/省略=跟随渲染；30=逻辑帧；2=慢系统
  order?: number;              // 同层顺序，小的先跑
  nearOnly?: boolean;          // 预留给"按距离降级"
  update(f: Frame): void;      // Frame{dt, elapsed, hour, fps}
  dispose?(): void;
}
```

`World.tick()` 负责：按层→order 排序、按 `hz` 累计 dt、**一帧最多补一次**
（防卡顿后追帧把世界一口气推进，确定性优先）。

## 五、帧预算（本轮已生效）

| 系统 | hz | 理由 |
|---|---|---|
| 相机 / 玩家 / 天气 / 信使 / 河面反光 / 地标 | 跟随渲染 | 视觉连续性，降频会看出来 |
| 交通 / 行人 / 车辆 / 居民回放 | **30** | 位移不肉眼可辨，省一半逻辑帧 |
| 昼夜 / 屋顶灯带 | **2** | 本质是缓慢状态 |
| （预留）统计/审计类 | 0.2 | 未来按需 |

实测：包体 820.4 → **822.0 KB（+1.6KB）**；可走五项 PASS（5.01m / 60fps / 穿墙 0 / 报错 0）、
按拍回放 PASS（25/32 跨拍位移）。**降频没有带来可见回归。**

## 六、迁移路线（三期，每期可验收）

| 期 | 内容 | 验收 |
|---|---|---|
| **P1（本轮已完成）** | 内核 `core/`；11 行手写循环 → 12 个系统注册；`?play=1` 接入 | 可走五项 PASS；按拍回放 PASS；包体增量 <5KB |
| P2 | 目录按层归位（`world/`、`live/` 拆子目录）；`main.ts` 目标 <120 行 | 构建通过 + 两条回归 PASS + `main.ts` 行数达标 |
| P3 | 按距离降级：`nearOnly` 系统只在玩家 120m 内跑；远景转统计 | 连续走 5 个街区，帧率与内存不劣化 |

## 七、明确不做（防止重构变味）

1. **不引 ECS**：我们的实体量级（几十~几千）用不到，ECS 会让可读性变差；等真要上万实体再谈。
2. **不换引擎**：three.js 交付优势（单文件 file://）是护城河。
3. **不引物理库**：碰撞用城市自带 AABB（已实测 +2KB vs +2MB）。
4. **不搬目录当成果**：先立边界与契约，目录是副产品。

## 八、与既定契约的关系（不另起炉灶）

- 字段与所有权：`cph4/city-foundation.md`（单一写入者矩阵 / places / agent-loop / bridge）
- 交互层：`city-foundation.md` §九（`player-trace-v1`）
- 本件只新增**代码侧边界**，不改任何数据契约。
