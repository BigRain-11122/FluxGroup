# bm-d 算力大脑 · 系统定案与显卡约束（2026-10-27）

> 背景：2026-10-27 CEO 问「我的算力大脑应该装什么系统」→ 席先推 Ubuntu Server 24.04 → CEO 回「不行 我还是会安排一些 window 软件的」并勾选剪辑/办公/AI 工具/游戏四类 → 改判 Windows 并给出约束面。本件=该轮评估的长期结论，供装机与后续会话引用。

## 一、硬件真相（对齐 2026-10-21 判负）

- bm-d 实配 = **3× V100 16G（48G 池）+ 双路 E5-269x v2（24C48T·只有 AVX，无 AVX2）+ 256G DDR3 ECC + 512G SSD + X9DR3-F（传统 BIOS·无 TPM 2.0）+ 板载 IPMI**。
- **P104/P102 已于 2026-10-21 16:5x 判负、未采购**（无官方驱动跑道／CUDA 13 弃 Pascal／PCIe 1.1 x4／FP16 1/64 无 Tensor Core）。凡见到「六卡机」「3×P104」的文档均为旧稿。

## 二、系统定案：Windows 10 IoT 企业版 LTSC 2021

判定依据（按排除法）：

| 版本 | 判定 | 原因 |
|---|---|---|
| Win10 22H2 专业版 | ✗ | 2025-10-14 已停止支持，24/7 联网机装它=永久不打补丁 |
| Win11 全系 | ✗ | 要求 TPM 2.0 + UEFI + 8 代以上 CPU；X9DR3-F 2013 年传统 BIOS 板三条全不满足，强装=更新面埋雷 |
| Windows Server 2022 | 备选 | 保到 2031-10，但授权成本 + UEFI/Secure Boot 要求存疑 + Store/编解码缺口 |
| Win10 企业版 LTSC 2021 | 备选 | 仅到 2027-01，到期又要动 |
| **Win10 IoT 企业版 LTSC 2021** | ✅ **定案** | 无 TPM/UEFI 要求、传统 BIOS 可装、官方生命周期 **2032-01**（IoT 版 10 年）、Win32 软件全兼容 |

配套硬约束：

- 驱动 **R580 是 Volta 最后一条分支**（2028-10 前安全更新），装后必须用组策略/`wushowhide` 掐死 Windows Update 的显卡驱动替换与自动重启。
- **CUDA 必须钉 12.8**：CUDA 13 已移除 sm_70（Volta）。
- CPU 无 AVX2 → 官方预编译 llama.cpp 跑不起来，必须自编：`-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=70 -DGGML_NATIVE=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF`。
- **禁 Ollama、禁 vLLM**（均弃 Volta）。

## 三、显卡约束（CEO 四类软件全勾后暴露的硬冲突）

1. **V100 是纯计算卡**：无显示输出、无 NVENC/NVDEC、TCC 模式下无 DirectX/OpenGL 渲染。
   - 能吃：办公/网盘/微信/AI 工具（ComfyUI、PyTorch、llama.cpp，CUDA 照算）。
   - 吃不了：游戏（出不了图）、剪映/达芬奇的 GPU 硬编与预览（无编解码引擎）。
2. **Windows 同机禁 GeForce + Tesla**：两族驱动包互不覆盖对方设备 ID，能跑通的都要手改 INF 强绑，一次更新就崩——与「不能返工」冲突，列为红线。
3. 要图形能力只能加 **Quadro 族**（RTX A2000 12G 或 A4000 16G，同属专业驱动线），且全卡切 WDDM；**必须先单卡验证驱动同存再上满三卡**。
4. 否则图形/游戏/硬编活留在 **bm-a（4070 SUPER，有显示输出+NVENC）**。
5. 512G 盘不够「系统 + 64G 模型（35B Q8 37G + 27B Q8）+ 剪辑/游戏缓存」，建议加 1–2T SATA SSD，模型与数据放 D 盘。
6. 桌面走板载 BMC 显卡（2D 够用），远程三轨 = UU（CEO 自己进桌面）+ RDP over tailscale + IPMI。

## 四、验收闸（装机后）

1. 3 卡 ECC Enabled + 72h Xid 零条；
2. 35B-A3B Q8 三卡层切跑通 + 质量回归题一次过（速度只记录，不设淘汰线——2026-10-21 判据换轨）；
3. 断电重启→服务自动拉起→手机浏览器可开对话页；
4. 跑一次 Windows Update 检查，确认没有显卡驱动被替换。