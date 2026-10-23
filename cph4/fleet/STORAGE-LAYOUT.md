# 存储布局（2026-10-23 定）

> CEO 令：「能挪到 D 盘都挪，规划好文件目录，总文件夹还是 FluxGroup」。

## 一、总览

- **C 盘（工作树）**：`C:\Users\sjs20\Desktop\FluxGroup\` —— 只留代码、文档、`.git`
- **D 盘（重资产）**：`D:\FluxGroup\` —— 所有大体积内容

C 盘保留的 3 个入口全部是 **Junction**，读写透明，旧脚本/旧路径零改动。

## 二、C 盘目录（git 工作树）

| 路径 | 类型 | 指向 |
|---|---|---|
| `media\` | Junction | `D:\FluxGroup\media` |
| `gaming\` | Junction | `D:\FluxGroup\gaming` |
| `cph4\fleet\mv0001-handover\` | Junction | `D:\FluxGroup\cph4\fleet\mv0001-handover` |
| `cph4\`（其余）、`docs\`、`Tools\`、`.git\` | 实目录 | C 盘 |

## 三、D 盘目录

```
D:\FluxGroup\
├─ media\                 媒体资产 18 GB（BigStream / MUSIC / MV / meme）
├─ gaming\                游戏公司 50 GB（MiniGame 等，含 Unity Library）
├─ recon\                 逆向资产 14.4 GB（apk/data/tools/raw）
├─ cph4\fleet\mv0001-handover\   MV 素材 10 GB
├─ compute\ domain\ house\ life\ quant\ research\ fleet\ docs\ Tools\
│                         既有职能目录（历史沉淀）
└─ 软著申请材料\、根级文档   既有内容
```

其中 `D:\FluxGroup\media\recon` 是 Junction → `D:\FluxGroup\recon`（保持「逆向资产独立一级目录」）。

## 四、规则（以后照此执行）

1. **新增 >100MB 的内容一律写 D 盘**，C 盘只放源码/文档/配置。
2. 需要旧路径兼容时：先 `robocopy /E /MOVE`，再 `mklink /J` 回原位置。
3. 逆向/下载/解包默认落 `D:\FluxGroup\recon\{apk,data,tools,raw}`。
4. 迁移前核对两侧文件数（D ≥ C 才删 C），迁移后验证 Junction 可读。
5. 不动 `.git`、不改远端，迁移只影响本地路径。

## 五、本次迁移实测

- 释放 C 盘：约 **85 GB**（C 可用 977 → 1062 GB）
- D 盘占用：**115.7 GB**
- 校验：gaming 713,008 文件、mv0001-handover 1,042 文件、recon 9 APK，全部在 D 侧完整
- git 验证：根仓与 MiniGame 在 Junction 下 `git status/log` 正常