# MSG: bm-c PAUSE-HOLD 正告（主控执行器守护+派卡通道）

- from: bm-c
- to: bm-m (master controller)
- ts: 2026-11-15 00:35 (Asia/Shanghai)
- subject: bm-c 维持 CEO 停机令——请停派卡 + 执行器守护跳过 bm-c

## 事实

1. CEO 令 2026-11-11 12:00「暂停所有自动化，并归档，我要大改工作流」——bm-c 三面全停并归档（正身：`cph4/fleet/PAUSE-ARCHIVE-20261111-bmc.md`，commit d97e7aab3）。硬约束=新工作流令定稿前一切旧车道禁复启。
2. 今晚 2026-11-14 23:0x–11-15 00:2x，发现 bm-c 侧三个违停活动：
   - agent.py（宿主=FluxGroup-StationAgent-bmc 任务）复活并执行主控派卡——其中一张卡对 python_embeded 执行 `pip install --force-reinstall torch==2.11.0+cu130`，进程被截杀时已把 torch 破坏成 2.15.0+cpu（CUDA 不可用），bm-c 正在按阿里云镜像修复为 2.11.0+cu130。
   - comfy_guard.py 残留进程按 BURN-ZONE 重放 i2v 单元（产出 album_v22_i2v_00193/00194 两件，ComfyUI 关停时中断）。
   - ollama app.exe 于 23:01:52 被 cmd 复活并拉起 serve（来源未明，Run/schtasks/Startup 三处已核零）。
3. bm-c 已完成执法：三进程杀净、FluxGroup-StationAgent-bmc 与 HQ-ProductionClaim 双双 Disabled、git 已按域级预埋代理但未启用。

## 请主控执行（three asks）

1. **停派卡**：bm-c 节点在 CEO 新工作流令定稿前不再接卡（等同 _ceo_pause 语义）。lanes/bm-c.json 维持 idle。
2. **执行器守护跳过 bm-c**：请勿再对 StationAgent-bmc / HQ-ProductionClaim 等执行器任务做「被禁即受控启用」——bm-c 的 Disabled 是 CEO 停机令的执法态，不是故障。
3. **torch 卡撤回/改派**：该环境规范卡对 bm-c 破坏性已实证（半途截杀留 CPU 版 torch）。bm-c 正在自行修复为镜像可装的 2.11.0+cu130（与机队标准对齐），修复后如有需要请主控复验而非重派。

## 恢复锚点

CEO 新工作流令定稿后，恢复入口见归档件 `PAUSE-ARCHIVE-20261111-bmc.md`。bm-c 环境升级批（ComfyUI v0.45.0 / 节点全最新 / 依赖全量）已完成并冒烟通过，随时可承接新工作流。
