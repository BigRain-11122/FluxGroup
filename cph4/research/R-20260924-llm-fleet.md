# R-20260924-llm-fleet — 机队本地 LLM 拓扑调研与适配方案

> 溯源：CEO 令 2026-09-24 午后「调研最佳方案，然后适配我现在的情况，有独立显卡的机器群可以，除了笔记本总控电脑。」
> 产出方：CPH4 Labs（技术/架构底层全面负责·12:30 升格令）。性质：调研+适配方案；正典落位=token-economy §3.5；派工=P-49。
> 验证声明：机器实况=两司机队心跳双源实读（2026-09-24 13:17）；模型库=ollama.com/library/qwen3 实抓（2026-09-24）；qwen3 性能宣称=官方 README 原文转引（标 🟡 宣传级·判据以自测为准）。

## 一、家底实测（三物理 GPU 工作站 + 笔记本总控[排除] + 云）

| 机器（双源同盒） | CPU | RAM | GPU/VRAM | Ollama 实况（心跳 stack 字段） | 本地推理角色 |
|---|---|---|---|---|---|
| bm-a ≡ BG-A | 9950X 16C32T | 96GB（free 51%） | RTX 4070S 12GB（free 3.1GB·util 93%） | ✓ API up·qwen2.5:7b-instruct+14b+bge-m3 三件在盘 | **主服务位**（快线现役+深度线分时·token-economy §3.1） |
| bm-b ≡ BG-B | 3800X 8C16T | 23.9GB（free 9.6%=紧） | RTX 3070 8GB（free 2.3GB） | ✓ API up·qwen2.5:7b-instruct 已装+flash_warm=true（MiniGame OllamaServe 栈现役） | 快线位（现役·llm_assist 双机整合在册） |
| bm-c ≡ BG-C | 3950X 16C32T | 23.9GB（free 26%） | **free 12.9GB 级**（MiniGame 报「RTX 3070 16384MB」=型号读数矛盾待核·fleet 表「13GB 级型号待报」） | ✗ **未装（全队唯一空白）** | 快线位（本批新装） |
| 笔记本总控 | —（不在机队心跳面） | — | 按 CEO 令**排除** | **零部署**（豁免面） | 云端 API 消费端（速度优先律+笔记本散热/电池+CEO 桌面体验） |
| 云端 API | — | — | — | — | 并行全量不变（scheduling §0.1·CEO 指令=唯一变更通道） |

- 双源同盒判定：bm-a≡BG-A 既有正典；b.json（3800X/23.9GB/3070 8GB）字段与 bm-b（16T/RAM 紧）契合、c.json（3950X/32T）与 bm-c（32T/free 12.9GB）契合=同一物理机两家心跳（F2 探针「B/C 双源在线判定」同源）。
- GPU 型号读数矛盾（bm-c）：3070 无 16GB 版——判型走其机队协议补报（fleet-allocations bm-c 行已在册）；按 **12.9GB free 保守规划**。

## 二、调研结论（最佳方案四条）

1. **拓扑=每机 localhost 独立服务，非中央服务节点**。依据：机队形态=git 控制面+croc 数据面的**跨网松耦合**（无可靠共 LAN 实证）+内部面零服务器红线不变+单点故障面最小；中央 LAN 服务位（OLLAMA_HOST 网络化）=待 Tailscale 组网授权（B1 悬置件）后再评，非本批。每机 11434 本机自用，跨机零依赖。
2. **模型选型（Ollama 库实抓 2026-09-24）**：qwen3 系在库（37.8M 下载）——qwen3:4b **2.5GB**（256K ctx·2507 刷新版）/qwen3:8b **5.2GB**（40K ctx）/14b 9.3GB；官方 README：🟡「Qwen3-4B 可对标 Qwen2.5-72B-Instruct」「100+ 语言」「thinking/non-thinking 双模」。**判定=升级候选非即换**：12GB 级机→qwen3:8b 对照现役 qwen2.5:7b（足印近似 5.2 vs 4.7GB=drop-in）；8GB 机 bm-b（VRAM free 仅 2.3GB=紧）→qwen3:4b（2.5GB）更合身。判决走 T2+预注册判据（中文摘要质量盲评+时延 p95+VRAM 足印三轴），禁盲换禁空转双驻。
3. **配置标准全机统一**：infra-3 §3.3 机器级 Ollama 配置律（OLLAMA_KEEP_ALIVE=15m/NUM_PARALLEL=2/MAX_LOADED_MODELS=2/FLASH_ATTENTION=1/KV q8_0/CONTEXT_LENGTH=4096）——新装机照单执行；保温走 MiniGame OllamaServe 栈范式（flash_warm 文件旗·借算时 keepwarm.pause 释放阀=fleet §10 照旧）。
4. **禁空转预装律执法**：bm-c 装机正当性=其上 BigMoney 轮次在跑（r50 实况）+P-48 上下文管家试点扩面消费+GREEN-IDLE 闲置点名律（两夜绿灯点名）受益面=P3 离峰窗（03:00-07:00）本地批处理（池扩容/UGC 分类/年轮批量）=首选派活——装即有单，非空转。

## 三、适配方案：机队本地推理拓扑 v1（正典=token-economy §3.5）

| 位 | 机器 | 本批动作 | 消费面（禁空转锚） |
|---|---|---|---|
| 主服务位 | bm-a | 零改动（7b 现役+14b/bge-m3 在盘随消费线） | 居民城脑/年轮/llm_assist/管家 pilot |
| 快线位 | bm-b | 零改动（7b+保温现役）；升级候选=qwen3:4b 对照 | llm_assist+管家 pilot 扩面 |
| 快线位 | bm-c | **新装**：Ollama+qwen2.5:7b-instruct（全队同版本基线）+flash_warm | 其回测轮 llm_assist+管家试点扩面+闲置点名受益 |
| 豁免位 | 笔记本总控 | **零部署永禁**（CEO 令排除·常设法） | 云端 API 消费端（速度优先·「token 可以烧」原文锚定） |
| 深度位 | bm-a 14b 分时（在盘） | 随 v3 点居民问答启用（禁空转预装律） | — |
| 升级线 | 全队 | qwen3:8b（12GB 级）/qwen3:4b（8GB 级）对照评估=另立 T2 件（判据预注册·A/B 双跑·两周窗） | 判据=中文摘要盲评≥现役+时延不劣+足印合身 |

## 四、落地与派工（P-49）

1. **bm-c 装机**（转办@BigMoney·其机自装·栈范式引用 MiniGame OllamaServe 不复制）：Ollama 安装+qwen2.5:7b-instruct 拉取+§3.3 配置律+心跳 stack 字段起报——判据=`ollama list` 见 7b+本地调用 1 次成功（tokens: local 计数起）+心跳 ollama_api_up=true。
2. **版本正典**：全队快线基线=qwen2.5:7b-instruct（现状已 2/3 机在役·bm-c 补齐即 3/3）；模型版本变更=T2 登记（token-economy §3.1 标准服务律）。
3. **qwen3 对照件**（随 P-31/P-48 两周窗·非本批必成）：两型 A/B 判据预注册后跑——成立才换基线（结构性替换律：只认实测承接）。
4. **豁免登记**：笔记本总控=非机队成员豁免位（零本地部署）——fleet-allocations changelog+token-economy §3.5 双注记，未来任何「全机部署」类任务必过此豁免行。

## 五、不做什么（反过度工程）

- 不上分布式推理（vLLM 多机张量并行=7B/14B 级杀鸡用牛刀）；不做中央模型路由网关（向量路由判定已否=infra-3 同源）；不为笔记本装任何本地件（CEO 令直排）；不预装 14b 到 bm-c（禁空转·先补快线基线）；不动云端默认态（并行全量=CEO 指令唯一变更通道）。
