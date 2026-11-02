# 机队架构调研与链路 v3（2026-10-27）

> 用途：跨会话保留调研结论，避免下次重新查/重新拍架构。正典代码仍以仓库为准。

## 一、Qwen 版本谱系（2026-10 实况）

- **Qwen3.5**（2026-02/03）：0.8B/2B/4B/9B/27B 稠密；35B-A3B、122B-A10B、397B-A17B MoE。
- **Qwen3.6**（2026-04）：35B-A3B（4-16）、27B（4-22）。
- **Qwen3.8**（2026-08）：开源只有 **27B 稠密（VL，Apache-2.0，262K→1M）**、**Flash-Next**（约 180B 存储/6B 激活，Qwen Community License 1.0）、2.4T-A95B；其余 Max/Omni 仅 API。
- **Qwen4**：2026-09-22 仅命名，无权重、无日期，不能等。

**推论**：3.8 没有 4B/9B 小档；“全系一个家族”= 3.5 跑小档、3.6 跑 35B-A3B、3.8 跑 27B 质量档。同 repo/同 tokenizer 家族。

## 二、模型分配（质量/速度平衡，禁追最大）

| 机器 | 默认 | 按需 | 备注 |
|---|---|---|---|
| bm-m | Qwen3.5-9B（MLX，30–50 tok/s） | 3.8-27B（写作/审阅/看图） | 给 Xcode 留 ≥12GB |
| bm-a | 3.5-9B | — | 12GB 卡 |
| bm-b | 3.5-4B | 9B 短上下文 | 8GB 卡 |
| bm-c | 4B 哨兵；空闲 9B | — | 16GB 卡放不下 27B；渲染期零大模型 |
| bm-d | 3.6-35B-A3B（3B 激活） | 3.8-27B 离线质量批 | V100 无 FA/BF16，FP16+XFORMERS |

原则：4B 判断、9B 日常、35B-A3B 复杂、27B 按需质量件；先用最小档过黄金集，失败才升级；任务中途不换档。

## 三、GitHub 方案核验（星数/许可/结论）

| 项目 | 事实 | 结论 |
|---|---|---|
| MinIO | 社区版 2026 归档、UI 收费 | **不用** |
| SeaweedFS | 34.9k★ Apache-2.0，Go 跨平台 | 存储首选 |
| RustFS | 32k★ Apache-2.0，2026-09 1.0 GA | 备选/后续评估 |
| LiteLLM | MIT，18k+★，路由/fallback/预算 | 模型网关采用 |
| Kitsu / Zou | CGWire，AGPL，自托管；项目/集/镜/资产/任务/版本/审批 + API/Gazu | 生产状态层采用（内部自用） |
| OpenTimelineIO | ASWF，Apache-2.0，镜头/帧/媒体引用 | 时间线标准，替代自建 EDL |
| OpenAssetIO | ASWF，Apache-2.0，v1.0；有 ComfyUI 插件 | 资产版本/发布 |
| Hatchet | MIT，8.1k★，Python/TS/Go/Ruby | durable 编排候选（轻于 Temporal） |
| Restate | 单二进制，但 **BSL** | 观望（许可） |
| Temporal | 重，需 DB | 现在不用 |
| Netdata | 80k★ GPL-3.0，逐秒指标 | 基础设施监控 |
| GPUStack / exo / SkyPilot | Linux worker / MLX 多 Mac / K8s | 不适用 |
| Airflow / Dagster / AYON | 数据管道/重 DCC 平台 | 现在不上 |

## 四、链路 v3（三层分离）

```
生产层  Kitsu/Zou：项目/集/镜/资产/任务/状态/版本/审批
时间线  OTIO：镜头表、帧范围、媒体引用
资产层  OpenAssetIO（可选）：版本解析/发布/依赖
执行层  NATS 事件 + Python worker；长流程/可取消用 Hatchet
数据层  SeaweedFS：S3 + 哈希 + 原子完成标记
模型层  LiteLLM：fleet-fast/std/pro/brain
监控层  Netdata + 业务看板
```

流转：Kitsu 任务 ready → NATS 事件 → worker 领 → 产物写 SeaweedFS（临时→完成标记+哈希）→ 调 Kitsu API 建 version/挂预览/置 review → 人审 → 下游解锁。

## 五、关键工程结论

1. **审批是长期状态，不是租约**；10 分钟租约不能表达 3 天的人审。
2. **数据亲和是一等公民**：10GB 经 Tailscale 中继按 20–50Mbps 需 27–67 分钟；派活评分必须含“数据在哪”，大件走夜间。
3. **原子发布**：临时对象→校验→完成标记+sha256，下游只认完成标记。
4. **至少一次 + 幂等 + 栅栏 token = 有效一次**；不要宣称 exactly-once。
5. **控制面/数据面/生产面分离**；git 只做代码与命令台账，不做运行时队列。
6. **安全**：NATS accounts/ACL（命令只有主控能发）、S3 凭据、LiteLLM 按线预算；产物保留策略与备份演练。

## 六、三个尖刺（先验证再排期）

1. **Kitsu/Zou**：Docker 起服务；Gazu 建项目/集/镜/任务；API 改状态、建 version、挂预览；确认 webhook/轮询。
2. **OTIO**：现有镜头表生成 `.otio`；ffmpeg 按 OTIO 渲染一段；核对帧范围/时长。
3. **SeaweedFS**：Windows 单节点 S3；Python 上传/下载；验证临时对象→完成标记→哈希。

## 七、我此前的错误（留档）

- 选 MinIO（已归档）。
- 自研模型别名路由（重复 LiteLLM）。
- 把审批做成租约任务。
- 按能力派活却忽略数据亲和。
- 无原子发布、无取消、无 NATS 认证、无 GC/备份。
- 先 bm-a 起存储再迁 bm-d（浪费）。