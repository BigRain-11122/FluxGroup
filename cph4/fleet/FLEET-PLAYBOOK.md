# FLEET-PLAYBOOK v1.0 — 机队共享流程手册与经验库

> 法源：CEO 2026-11-06 令「机队间好的经验和记忆也要互相分享，还有流程」。
> 地位：全队共享的操作智慧正典——各机私有记忆里的判例、坑修、好做法，提炼成跨机可用的流程，上链人人可读。
> 维护律：各机学到新东西（好经验或坏教训）→ 先发 cross-talk CT 帖 → 被采纳后折入本册对应章节。本册永远在迭代。

## 一、代理管理（全机队）

### 常驻代理翻转法（代码更新后必须做的）

**何时须翻转**：git 上 agent.py / lane_agent.py 有新提交，而你的常驻代理还在跑旧码。
**为什么**：`--loop` 进程不热载——代码在盘上但它吃的是启动时的版本（11-04/11-05 两日三起实锚）。

```
步骤 1：确认没有 GPU 训练子进程在飞（vb_build / vb_train_card）
        有 → 先等它结束（Job-Object 连坐律：杀父进程=杀全树）
        没有 → 直接下一步
步骤 2：杀常驻 python（命令行含 agent.py --node <你的节点>）
步骤 3：什么都不用做——every:1m 的计划任务 1 分钟内自动带新码重启
步骤 4：验证——跑 loop_liveness 或看 agent-push.log 出现新行
```

### 回执自动上链（v3 --sparse -f 法）

agent.py push() 前无条件 `git add -A -f --sparse -- <前缀>`。
- `--sparse` 让稀疏锥外自有件入索引
- `-f` 穿透 .gitignore
- 前缀免疫中文文件名（八进制转义坑）
- **不修则你的回执滞留本地，主控对你半盲**（bm-b 60+ 回执滞留一整天实锚）

### 代理冻结克隆病（11-05 实锚）

本地杂牌提交堵死 ff-only pull → 落后数百提交 → 新码永远不生效。
修法：`git branch -f backup` 留牌 → `git reset --hard origin/main` → 杀常驻让任务重启。

## 二、GPU 纪律（全机队）

### 单车道律

一张卡同时只跑一个训练/烧制任务（不并行 i2v + LoRA + TTS）。

### 显存释放三件套（训练前必做）

1. 杀 `llama-server.exe`
2. 杀 `ollama.exe` 守护进程（**只杀 llama-server 不够**——守护会拉回挤显存）
3. 禁用 `MiniGameOllamaServe` + `MiniGameOllamaKeepWarm` 双任务

训练完成后：删 `keepwarm.pause` + enable 双任务 = 恢复。

### 长批续阀（5 分钟任务）

哨兵 12h 阀 TTL 自动删阀 → 文本模型钉回常驻 → TTS 慢 15 倍。
正法：`FluxGroup-ValveKeep` every:5m（`Tools/valve-keep.ps1`：touch pause + 杀 llama-server）。

### 8G 卡模型槽律

- **常驻槽必须是 4B**（qwen3.8:4b / 4.9GB / 77 tok/s）
- 7B 会被下一拍 REPINNED 拉回并挤爆显存（实测）
- 14B 只准离线批量独占（7.7GB 满载）
- 切换器 = `Tools/model_slot.py`

## 三、下载供给（全机队）

### aria2 16 连接律

OpenSLR 等镜像按连接限速（单连接 0.02-0.06MB/s）→ **aria2 -x16** 实测 12.7 倍提速。

### aria2 预分配双陷阱

1. **「文件满额」=假象**——aria2 预分配全尺寸文件，从下载第一秒起大小就等于期望值。
   **唯一完成判据 = .aria2 控制文件消失**。
2. **零洞陷阱**——预分配缺块=零填充区，python tarfile 读到零块=合法归档结尾，
   extractall rc=0 但只解出第一个洞之前的内容。**完整性=解出量对账**。

### 自愈下载范式

S4U every:15m 任务 + 实例内 13 分钟看门狗（断点续传、完成自停）。
现成模板：`bm-d-ISO-Pull` / `bm-b-VoiceCorpus-Pull`。

## 四、语音微调管线（全机队）

### 流程

```
语料入库（RIGHTS.json + 白名单） → 切片（voice_corpus_prep.py 2-12s 段）
→ SoVITS s2 微调（vb_train_card.py → vb_build.py 20ep）
→ 参考音择优（vb_pickref.py 三闸：身份≥0.65 + 转写自洽≥0.90 + hf_ratio≥0.010）
→ 出厂 QC（voicebank_say.py ASR 回读+亮度+噪声底）
```

### 关键教训

- **中文（AISHELL-3）切片窗默认 10s 即可**——指令式短句有清晰停顿
- **英文（LibriTTS）切片窗必须 25s**——连续朗读无 -35dB 静音间隙，默认 3-10s 窗会整段丢弃
- **重跑前必清 `VB_ROOT/<voice>/` 与 `_m4a/<voice>/`**——多跑残留会引发 SEG-DROP 级联
- **身份闸用 ERES2NetV2 说话人嵌入**（GPT-SoVITS 自带），**禁用基频闸**（八度错误=错杀实锚）
- **参考音是质量总开关**——坏参考念错字且整句丢，好参考 ASR 0.981

## 五、质量出厂闸（全机队）

正身 = `cph4/fleet/quality/DE-AI-SPEC-v1.md`（28 条四域）。

### 声音面反 AI 味四层
1. 真人语料（非纯合成）
2. SoVITS 微调（非端到端 TTS 直出）
3. 参考音三闸（身份+转写+亮度）
4. 切片禁 loudnorm（保自然 LRA 与停顿密度）

### 人脸面
- DreamShaperXL / SDXL 系 = AI 脸重灾区，**禁入产线只许草稿**
- 升级路径 = qwen-image 四件套 + 真人脸 LoRA
- 对照板 = `Tools/fleet/asset_board.py`（确定性拼板，防挑图作弊）

## 六、仓库卫生（全机队）

### 稀疏执行克隆写大目录律

**一律走 `git add -A -f --sparse`，勿把大目录（如 queue-receipts/ 766 件）进稀疏锥**——全物化必挂。
拉取面零额外成本：只 un-skip 本机已落盘件，他机收据保持 skip-worktree 不物化。

### 日志轮转

`repo-slim.ps1` 内置 `fleet/**/*.log > 20MB → 保留尾 5MB`（`oversight-run.log` 曾 4.37GB 实锚）。

### 主仓不可直接跑命令

主仓落后 origin 数千提交 + 2617 脏件 → **用干净克隆**（FleetAgent / FleetRuntime）跑一切。
CAS 外科推送用 `--sparse -f` 前缀法，**路径参数必须正斜杠**（反斜杠=根树垃圾条目实锚）。

## 七、机队通信（全机队）

### 通道全景

| 通道 | 用途 | 谁消费 |
|---|---|---|
| 令总线（OB-*.json） | CEO 令广播+车道自领 | 全机 |
| Cross-talk（CT-*.md） | 问题/判例/经验/流程 | 全机·主控日扫 |
| Need-work（state/need-work/） | 没活喊话 | 主控 2s P0 响应 |
| WORK-RULES（jsonl） | 主控本地小模型执行 | bm-m 脉 |
| Backlog（PRODUCTION-BACKLOG） | 申报池 | 主控晋升或 worker 自晋升 |
| NATS 心跳 | 节点存活+资源 | 主控 |

### 有则改之无则加勉律

看到别机的 CT 帖：**有同病→当班修+回帖**；**无同病→回帖「已查，本机无此问题」**。
不回帖=没看过=违令。

## 八、Windows/PowerShell 陷阱（全机队）

| 坑 | 正法 |
|---|---|
| PS 传 python -c 剥内嵌双引号 → NameError | 用 `print(1)` 不用 `print("...")` |
| PS heredoc 传 python -c 被吞引号 → SyntaxError | 复杂 python 一律写临时 .py 再执行 |
| 中文路径 git status 八进制转义 → pathspec 不匹配 | 前缀式 add，勿逐路径收集 |
| BOM（PS Out-File -Encoding utf8）→ python json.load 抛错 | 一律 `[IO.File]::WriteAllText(path, txt, UTF8Encoding($false))` |
| `$LASTEXITCODE` 假信号（.ps1 调用后残留旧值） | 每次使用前显式清零 `$global:LASTEXITCODE = $null` |
| 进程探测自匹配（命令行含目标串） | 探测一律排自身 PID |
| bg 任务包装器剥 cmd /c 壳 → 裸 &/&& ParserError | 原生命令链写 .cmd 裸路径调用 |
| PS 变量名大小写不敏感 | 不同变量禁止同名不同大小写 |
| multiprocessing spawn 重 import | 必须 `if __name__ == "__main__"` 守卫 |
| modelscope snapshot_download 卡死 | curl `-C -` 直链 resolve/master |

## 九、模型与算力配置（全机队）

| 机 | GPU | CPU | 角色 | 模型槽 |
|---|---|---|---|---|
| bm-a | RTX 4070 SUPER 12G | 94G RAM | CEO 工作机（夜窗 GPU） | 白天让路 09-19 |
| bm-b | RTX 3070 8G | 24G RAM | 声音车道+小 GPU | 4B 常驻 |
| bm-c | RTX 3070 16G | 24G RAM | GPU 产线（KF/i2v/训练） | — |
| bm-d | V100×3 48G | 256G RAM | 算力大脑（待入网） | CUDA 12.8·禁 Ollama |
| bm-m | M1 Pro 无 CUDA | 32G RAM | 主控+文本+iOS | qwen 4B 本地 |