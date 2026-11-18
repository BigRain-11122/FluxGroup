# 本地大模型工作流（12GB 显存 / 64GB 内存）· 2026-11-09

## 一 先回答你最初的问题：要不要换模型？

**不用换。你已经装着最新一代了。**

你本地现有（实测）：

| 模型 | 大小 | 说明 |
|---|---|---|
| **qwen3.5:9b** | 6.6 GB | **最新一代，质量最好**——主力候选 |
| qwen3.5:4b | 3.3 GB | 平衡 |
| qwen3.5:2b | 2.7 GB | 最快 |
| qwen3:8b / 4b / 4b-instruct | 5.2/2.5/2.5 GB | 上一代，可删 |

外部可选（12GB 内）：`glm4:9b`(5.5GB)、`gemma3:12b`(8.2GB)、`deepseek-r1:14b`(9.0GB)、`phi4:14b`(9.1GB)。
**但你已经有 qwen3.5:9b，中文场景它是最优解，不需要再下。**

## 二 真正的问题：不是模型，是显存

实测（这台机器）：

```
显存总量      12282 MiB
被占          11.6 GB   ← 飞书 + Edge + 4×EdgeWebView + DSH + Tuanjie Hub
Ollama 重启后  仍只剩 333 MiB
```

**所以模型再对也跑不动。** 实测对照：

| 模型 | 需要显存 | 实测表现 | 结论 |
|---|---|---|---|
| qwen3.5:2b | 2.7 GB | 首次加载 214s，之后 **41.6 tok/s** | **GPU 通路正常** |
| qwen3.5:4b | 3.3 GB | 挤得进，可用 | 可用 |
| **qwen3.5:9b** | 6.6 GB | 塞不进 → 掉 CPU → **0.6 tok/s** | **当前状态不可用** |
| qwen3.5:27b | 17.5 GB | 走内存 → **单次 >20 分钟** | 只能夜间批量 |

**对照：早先显存空闲时，同一个 9b 只要 0.35 秒/次。**
⇒ **差别不在模型，在显存有没有腾出来。**

## 三 另一个坑（已修）：qwen3.5 是"思考型"模型

`num_predict=24` 时，模型把 24 个 token 全花在思考上，**返回空字符串**，我的代码当成"没命中"。
**必须先关掉思考（`think: false`）或给足 token。**

实测：关思考 2 秒/文档（3 题对 2）；开思考 47–75 秒（3 题对 1）。
**⇒ 这个任务上思考模式又慢又差，一律关掉。**

## 四 搭好的工作流

### 原则：**先看显存，再选模型**（不是先选模型）

| 空闲显存 | 用哪档 | 速度 |
|---|---|---|
| ≥ 8.8 GB | **qwen3.5:9b** | 全速（0.3s/次） |
| 5.4–8.8 GB | qwen3.5:4b | 快 |
| < 5.4 GB | qwen3.5:2b | 快，质量一般 |
| 夜间（关浏览器） | qwen3.5:9b 或 27b | 质量档 |

### 交付的两个工具

**`Tools/llm_workflow.py`** —— 日常入口
```bash
python Tools/llm_workflow.py --preflight    # 现在能跑哪一档
python Tools/llm_workflow.py --free         # 谁占着显存、关掉能省多少
python Tools/llm_workflow.py --warm auto    # 按预检结果预热并常驻 30 分钟
python Tools/llm_workflow.py --ask "问题"    # 用推荐档位问一句
python Tools/llm_workflow.py --batch <目录>  # 夜间批量
```

**`Tools/llm_router.py`** —— 两级级联（9b 跑全量 + 27b 抽样复核 + 结果缓存）
```bash
python Tools/llm_router.py --selftest
python Tools/llm_router.py --judge <文件>
```

## 五 你现在要做的两件事

**① 用之前先腾显存**（这是唯一真正卡住你的东西）
```
关闭：Edge 浏览器、飞书、Tuanjie Hub、以及 4 个 EdgeWebView 进程
→ 能释放约 8-10 GB
→ 之后 9b 可全速
```

**② 日常怎么用**
```
白天（浏览器开着）→ 用 2b/4b 档，跑得快但质量一般
晚上（关掉浏览器）→ 预热 9b，跑批量（文档判定、字段抽取）
```

## 六 诚实说明

- 本篇所有数字都是**这台机器上实测**的，不是榜单抄的。
- **27b 我下载了（17.5GB），但实测单次 >20 分钟，不适合交互式使用。** 留着做夜间批量，或者你想省磁盘就删掉。
- `qwen3:8b` / `qwen3:4b` / `qwen3:4b-instruct` 是上一代，**可以删**（省 10GB 磁盘，对显存无影响）。

## 七 复跑
```
python Tools/llm_workflow.py --preflight
python Tools/llm_workflow.py --free
```
