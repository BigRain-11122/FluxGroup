# 龙卷风 D0.5 前置资产·机队调度实战令（2026-11-10）

> 令源：CEO 2026-11-10「先测试一波这个流程，让主控去分发任务，机队合作」。
> 测试目标：验证 AI-FLEET-DISPATCH-v1 的原子卡拆解→机队并行→主控监督全链。
> 项目：mv0002《龙卷风》（Tier S·邝盛·时间负片档）。

## 一、本批原子卡清单（主控 supply_batch 按此铺卡进 PRODUCTION-QUEUE）

| 卡 ID | 任务 | 机器 | needs | 交付物 | 验收 |
|---|---|---|---|---|---|
| LZ-A2.5-hermv2 | her_mv0002 LoRA 验证烧 4 张试烧图（随机 seed，触发词 hermv2） | bm-a | gpu | lora-eval/her_mv0002/test_{1-4}.png | 脸对锚 dHash≥0.85 |
| LZ-A2.6-hermv2 | her_mv0002 LoRA gate 盲评（4 张试烧图逐格打分） | bm-m | cpu | lora-eval/her_mv0002/verdict.json | ≥3/4 同一人 |
| LZ-B1.1-rainstreet | 写场景设定卡：暴雨街头（夜·冷蓝灰·霓虹反光·湿地面） | bm-m | cpu | scenes/rainstreet-card.json | 色温基线定 |
| LZ-B1.1-rooftop | 写场景设定卡：天台（夜·城市远景·风大·栏杆） | bm-m | cpu | scenes/rooftop-card.json | 色温基线定 |
| LZ-B1.1-indoor | 写场景设定卡：室内（男主房间·台灯暖·窗外雨） | bm-m | cpu | scenes/indoor-card.json | 色温基线定 |
| LZ-C1.1-umbrella | 写道具设定卡：雨伞（2001 台北·折叠伞·黑/深蓝） | bm-m | cpu | props/umbrella-card.json | 年代考据过 |
| LZ-C1.1-letter | 写道具设定卡：信纸/歌词手稿（钢笔字·揉过·部分撕） | bm-m | cpu | props/letter-card.json | 年代考据过 |
| LZ-E1.1-tornado | 龙卷风风格常量库定稿（暴雨蓝灰×冷调×胶片感·替代琥珀暖调） | bm-m | cpu | prompts/style-constants-tornado.json | lint 零否定 |

## 二、依赖关系

- LZ-A2.5 与 LZ-B1.1/C1.1/E1.1 **全部并行**（无相互依赖）
- LZ-A2.6 依赖 LZ-A2.5 完成
- 全部完成后触发下一批（B2 场景 KF + C2 道具 KF——需 GPU + LoRA gate PASS）

## 三、主控动作

1. 读取本令（order_watch 阶段当轮最高优先）
2. supply_batch 按 §一 清单生成 8 张原子卡写入 PRODUCTION-QUEUE（跨工作树处方：worktree from origin/main）
3. 各机 lane_agent 自动认领（bm-a 认 GPU 卡、bm-m 认 CPU 卡）
4. closer.py 2min 轮验交付物在盘
5. 全齐后主控汇总 D0.5 就绪状态呈报

## 四、验收

- 本批 8 卡全部 DONE + 交付物在盘 = 流程测试 PASS
- 任何卡 >2h 无回执 = 主控 STALLED-WORKER 介入
- A2.6 gate FAIL = 打回重训或调触发词（禁盲放）
