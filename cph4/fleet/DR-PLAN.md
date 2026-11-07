# 灾难恢复计划 2026-11-07T14:45:24

判定：**OK**｜RTO ≤ 30 分钟｜RPO ≤ 24 小时

## 天空是斜的假设：这台机器今天坏掉

队列与代码在 git，损失为 0；本地机时不重要。真正会丢的是**没有提交的改动**。

## 新机接管六步（≤30 分钟）

1. **装基础依赖**：`git / python3 / ffmpeg / ollama（winget 或 brew，见 bootstrap-machine.ps1）`
2. **拉控制面**：`git clone git@github.com:BigRain-11122/FluxGroup.git && cd FluxGroup`
3. **装模型**：`ollama pull qwen3.5:4b-mlx && ollama pull qwen3-embedding:0.6b`
4. **起常驻脉**：`python3 Tools/fleet/master_pulse.py --no-pull 冒烟一次，再 launchctl/kickstart 常驻`
5. **验三件事**：`COMMAND-BOARD.md 有数 / CEO-NEXT.md 有 top / cadence.py --check 为 PASS`
6. **接入机队**：`改 Tools/fleet-nodes.json 的本机 root，然后逐台 /poke 唤醒`

## 体检结果

- ✅ 关键文件在 git、配置可解析、备份在 RPO 内、队列可接管

## 备份状态

- 记录：2026-11-07T14:37:59
- 年龄：0.1 小时

## 已知不可恢复项（如实列）

1. 未提交的工作区改动（工作树共用导致）；
2. `state/` 下的运行时状态（按设计不进 git，可从队列与回执重建）；
3. 云端凭据与平台账号（在密码管理器里，不在此仓）。
