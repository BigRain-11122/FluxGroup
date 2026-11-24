# 本机算力上限实测（2026-11-18·零 swap 约束）

> 正身报告 = `cph4/fleet/SQUEEZE-MATRIX.md`；机读 = `cph4/fleet/state/gpu-squeeze.json`；
> 历史账 = `cph4/fleet/state/gpu-squeeze-history.jsonl`；压测台 = `Tools/fleet/gpu_squeeze.py`（自检 6/6）。

## 一、实测结论（并发解码 Σ，每配置 2–3 批取中位）

| 搭配 | 解码算力 tok/s | 判定 |
|---|---|---|
| 单条 4B@8k | 41.0（41.0 / 41.2 / 40.8） | 最稳基准 |
| 4B+2B | 57.0 | 零 swap |
| **8788 LoRA + 4B + 2B** | **56.4–61.5（48.6–64.2）** | **最好** |
| 上面再加 8B（四条） | 55.0（53.1–57.0） | 一条不涨 |
| 4B+9B | 35.0（34.8–35.2） | 比单条还低 |
| lora+4B+9B | 41.9 | 等于单条 |

- **三条车道到顶，卡在 GPU 不在内存**：第四条加不上去；5/6 车道只换来 swap 上升。
- **9B 是毒丸**：白吃 9GB，聚合反而低于单条 4B。任何"上大模型提吞吐"的想法在这台机器上不成立。
- ctx 2048 vs 8192 对吞吐没实质差别（61.5 vs 56.4），2048 波动更小。
- 全部配置过程内 swap 增长 0MB、换出 0 页；但累计 swap 被 5/6 车道尝试从 3.87GB 顶到 4.53GB（上限 5.12GB），清零只能重启。

## 二、推翻的旧数字

2026-11-17 记的「2 驻留 64.6 / 3 驻留 93.6 / 4 驻留 150.5 tok/s」**不是并发实测**，
是各车道单跑相加；同一天的「64 tok/s」档位注释同源失效。并发实测上限 60 左右。
KV 量化那半（FA=1 + q8_0 把 4B@128k 从 22.8 抬到 41.7）仍然成立。

## 三、测量方法上的四个坑（都让结论跑偏过）

1. **短输出量吞吐＝假数**：8788 车道用 64 token 上限被测成 5.2 tok/s，换 250 字长输出
   后是 25.8——差 5 倍全是量法错（墙钟被预填充与首字延迟吃掉）。
2. **卸载残留**：`ollama stop` 掉 9B 立刻开测，同一条 4B+2B 在轮1 被判换出 1484 页、
   轮2 归零。正法＝卸载后等空闲内存回落（`settle()`）再测。
3. **两条压测重叠**：单条 4B 从 41 掉到 33，极易被读成"机器变慢"。正法＝文件锁单实例。
4. **`launchctl submit` 会重入**，`nohup ... &` 随 shell 死。正法＝一次性 plist
   （RunAtLoad + KeepAlive=false）+ 文件锁；跑完 bootout 删 plist，别让它每次登录自跑。

## 四、8788 LoRA 车道的两个真 bug（已修）

1. `mlx_lm.server` 处理 `GET /v1/models` 会调 `scan_cache_dir()`，缓存目录不存在就抛
   `CacheNotFound` 把请求打死；launchd 不继承登录 shell 的 `HF_HOME`。正法＝启动脚本里
   显式钉 `HF_HOME`/`HF_HUB_CACHE` 并 `mkdir -p`。
2. Qwen3.5 思考默认开，`max_tokens` 全花在 thinking 上，`content` 返回 null。正法＝
   服务端 `--chat-template-args '{"enable_thinking": false}'` 默认关掉，别指望每个调用方记得。
3. 常驻方式 = launchd `com.fluxgroup.mlxlora`（KeepAlive），启动器
   `Tools/fleet/mlx_lora_server.sh` 自动挑最新 RUNS/*/best 适配器。

## 五、提示词口径（会退回助手腔的真因）

自己拼"写一条B站评论"喂 LoRA，出来的是「这里有一条既符合B站用户调性的评论，供你选择：
**选项一**…」。训练样本的 user 轮全是 `train_build.INSTRUCTIONS` 那三句，提示词不对版
等于没触发微调。正法＝`llm_client.lora_comment_prompt()` 复用同一批模板；
命令行用 `llm_client.py --lane lora --comment "<视频标题>"`。

## 六、落档改动

- `vram_ceiling.py` MODES 按实测重写：default = 4B@8192 + 2B@8192（去 9B）；
  max 改成 3 条（4B@32k + 2B@32k + 4B-dense@16k），注释里的 133–150 已废。
- `llm_client.py` 新增 `probe_lora()` / `generate_lora()` / `lora_comment_prompt()`
  与 `--lane lora`（OpenAI 协议与 ollama `/api/generate` 是两条独立车道）。
- 限制：`OLLAMA_KEEP_ALIVE=10m`，三条车道没人喂会掉回一条 4B。

## 七、同日发现的两条既有红（非本次改动引入）

1. RG-33：11-18 把 `GATEWAY_PORTS` 清空，但判据仍断言 8792 必须带令牌 → 现在无令牌也能
   打到 `100.75.133.10:8792` 并拿回 "Hello"。判据与配置打架，8792 算不算网关待裁决。
2. duties：D01 抽检 / E06 情况台账 / F04 磁盘分级三条 STALE，24h 零 DONE。

## 八、定案（CEO「不要问我 自己科学决策」后自行裁决）

1. **不重启清零 swap**：实测一次真三车道并发生成（240 token / 8.8s）期间 swap +0MB、
   换出 0 页、换入 507 页（≈2MB，正常代码/数据换入）。残留 5.9GB swap 是冷页，
   不被访问就不产生代价；判据只能是"生成过程中换出页=0 且 swap 不涨"，不是"swap 已用"。
   内存实况以 free+inactive+speculative 计（题面约 17GB 可用），单看 Pages free 会误判成 1.4GB。
2. **27B 不续传**：9B 已实测比单条 4B 还慢（35 vs 41）且白吃 9GB，27B 在 32GB 上必然与三条车道
   冲突；该 12GB 半截下载已于 2026-11-18 14:0x 按 CEO「用不着的可以删了」删除（代码零引用，仅 V100 硬件规划文档提到；要再用需重下）。
3. **评论长度上限从手感改成语料 P95**：3466 条 PASS 评论中位 22 / P90 70 / P95 86 / P99 111，
   只有 14% 超 60 字。第一版拍 60 把 14% 真评论判死，改 90。
4. **闸分两套口径**：viewer（观众评论，只限量与感叹号堆砌，质量交 comment_taste）
   vs reply（创作者回复，才用 voice_gate 禁感叹号/≤40 字）。混淆会把 LoRA 正确输出判死。
5. **清扫/探测必须自清场**：`vram_ceiling` 的 sweep/probe 会装 4B@32k 与 9B@8k，
   跑完停在 stop_all()，把机器留在"档位全失"状态——实锚：之后空闲掉到 0.33GB、
   social_learn 自检因内存不足判红。已加 `restore_tier()`：清扫结束按 state/MODEL-MODE 拨回。
6. **常驻要显式 keep_alive=6h**：服务端默认 10m，不钉住三条车道十分钟后就掉回一条。

## 九、并行的实测边界（CEO「继续压榨算力 并行」·2026-11-18 14:2x–14:4x）

**推理可以并行，训练不能。** 这是两条相反的结论，别互相套用。

| 场景 | 做法 | 实测 |
|---|---|---|
| 推理 | 不同模型分车道（8788 LoRA + 4B + 2B） | 41 → 56-63 tok/s（+46%），三条到顶，第四条不涨 |
| 训练 | 2 路并发（16层@224 + 8层@224） | 主训练 100 步从 9.5-10.0min 掉到 **14.2min（−45%）**，且换出 **12505 页/分** |
| 训练 | 3 路并发 | 换出 **6732 页/分**，看门狗当场撤线 |

原因是训练每路都要完整权重 + 优化器 + 激活，两路就把 32GB 的内存带宽和常驻挤满；
推理每条车道只需一次前向，交错能填满空闲带宽。所以：
- **训练一次只跑一路**，其余排队（`social_24x7` 的 TRAIN 阶段本来就串行，这条实测给它撑腰）
- **推理尽量多车道**，但三条是本机上限
- 并行训练的"省时间"是负的：慢 45% 换来一份还要再训 45% 才追平的产物

看门狗 = `Tools/fleet/train_guard.py`（换出>50/min 或 swap 涨>300MB 或可用<400MB 即撤线，自检 5/5）。
踩的坑：撤线动作原本还带一条写死的 pkill 模式，撤第三路时把第二路一起打死了——
**撤线只许认 label，不许按进程名模式匹配**。

## 十、CPU/GPU 到底还剩多少（2026-11-18 15:0x 实测）

取数方法（都不需要 sudo）：GPU 用 `ioreg -r -d 1 -w 0 -c IOAccelerator` 里的
`Device Utilization %`；CPU 用 `top -l 1 -n 0` 的 CPU usage 行。

- **GPU：训练时 Device Utilization 84%**（Renderer/Tiler 60%，GPU 侧统一内存 19.8GB 在用）→ 只剩约 16%
- **CPU：user 22% + sys 14% = 36% 忙，64% 空闲（约 6.4 核）**
- 管线本身几乎不吃 CPU：3.2 万条入库 3.4s、品味闸 2.6s、段位 0.6s → **空闲 CPU 在这条线上没有天然去处**，
  瓶颈是数据供给（采集受网络/浏览器限制，单车道）与内存，不是 CPU

**并发 2B 推理车道的实测代价**：持续压 7 分钟，2B 解码中位 33.7-34.4 tok/s，
训练 100 步间隔 9.6 → 10.4 分钟（约 +8%）。所以 GPU 余量是真能用，但——
真正把训练打垮的不是这条车道，而是**机队别处把 9B(9.2G)+4B(5G)+2B(3.1G)=17GB 装了回来**，
训练进程 rss 从 3.9GB 被换出到 0.43GB，9 分钟没落一个 checkpoint。

**因此立了训练独占机制**（事后清理不够，要在装载前挡住）：
- `train_run.sh` 写哨兵 `.codely-cli/state/TRAIN-EXCLUSIVE`，trap 里摘掉
- `llm_client.generate()` 检测哨兵 → 直接返 rc=5「训练独占中」，不装载
- `Tools/fleet/train_exclusive_guard.sh`（launchd `com.fluxgroup.trainlock`）每 30s 把任何已装载模型卸掉，
  兜住那些直接打 `/api/generate` 的调用方
- 踩坑：清扫器第一版在 launchd 下**什么也没卸**——PATH 里没有 ollama（在 `.homebrew/bin`），
  「脚本在跑、日志空白、job=running」就是假动作。同族坑：pyenv 解释器必须写绝对路径

## 十一、CPU 侧的两个负结果（2026-11-18 16:5x，别重复试）

1. **闸工位压不满 CPU**：出稿是 GPU 3-8 秒/条，过闸是 CPU 约 5 毫秒/条（1000:1）。
   即使把出稿改成"GPU 生产 + CPU 消费"三段流水、开 8 个闸工位，CPU 空闲仍 64-72%。
   想靠"多线程过闸"提高利用率是无效动作。
2. **0.5B CPU 车道技术上可行但作判官无效**：GGUF `qwen2.5:0.5b` + `num_gpu=0` 确实跑在
   CPU（98% CPU / 107 tok/s），但与五维品味闸的一致率只有 **11.7%** —— 它既不能替代闸也不能预筛。
   注意：ollama 的 **MLX 后端会忽略 `num_gpu=0`**（仍报 100% GPU），只有 GGUF 才走 llama.cpp 的 CPU 路径。

结论：本机 CPU 的合理用途是**数据搬运与解析**（入库/打码/去重/切片），量小的时候它天然空闲；
不要为了把利用率数字做上去而硬造 CPU 活。


## 2026-11-18 算力上限与满负荷训练（L1 迁入原文）
[2026-11-18 13:14:19] [2026-11-17] 算力上限与满负荷训练三事实：①**KV 量化是抬高上限的关键**：`OLLAMA_FLASH_ATTENTION=1`+`OLLAMA_KV_CACHE_TYPE=q8_0` 之前 4B@32k 掉到 22.8 tok/s，之后 4B@128k 41.7、9B@128k 24.8 且 swap 零增；②**并发聚合吞吐到三条车道就到顶（2026-11-18 重测推翻旧数）**：单条 4B@8k 41.0 / 三条（8788 LoRA+4B+2B）56–62 / 第四条 55（一条不涨，卡在 GPU）/ 4B+9B 只有 35（9B 白吃 9GB 反而更慢，旧记的 64.6·93.6·150.5 是各车道单跑相加不是并发实测，已废）→ 派活要跨模型分、且最多三条；三档切换=`Tools/fleet/vram_ceiling.py --apply default|max|train`（卸载+num_predict=1 预热钉 ctx，写 state/MODEL-MODE），正典=LOCAL-MODEL-CEILING-v1.json；③**全层 LoRA 不只是 OOM 也是 nan**（@128、lr 1e-5 与 3e-6 都 nan）＝4bit 基座全层适配在 mlx 上数值不稳，上限仍 16 层@224；跑到 590 步触发 swap(+1.3GB/空闲 393MB)时正法=停训+`--resume-adapter-file`+`--grad-checkpoint`+停 ollama 服务（它空转占 2.8GB）→ 空闲回 11GB、swap 不再增长；续训 iter400 76.9 > 原跑 iter500 62.4 > 末点 64.2，再次证明大集不能按末尾点或 val 选点。
