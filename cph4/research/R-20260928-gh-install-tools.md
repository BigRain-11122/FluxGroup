# R-20260928-gh-install-tools：GitHub CLI 工具/环境普查（P-2026-09-28-15 调研面）

> 调研员：CPH4 调研面 | 日期：2026-09-28（周一）| 状态：**完成（零安装调研·18 件全覆盖：13 采用候选+5 parked）**
> 纪律执行声明：本调研**零安装**（仅 winget search/show、web_fetch、Get-Command 等只读手段·未改 PATH/未写注册表/未装任何件）；许可与元数据以 api.github.com/repos/<org>/<repo> 直验（8 件成功）+raw.githubusercontent 许可**原文逐字直采**（10 件·A 级）补位；三红线执法（GPL/AGPL 边界逐件标注·许可原文逐件验证·死面/限流面如实记录）。
> **关键实测：本机 Admin=False（非管理员）·PS 5.1.26100** —— 全部安装法附非管理员可行路径。installer 类型逐件 winget show 直读定谳：portable(zip) 8 件=winget 用户级直装可行；wix/MSI 3 件（gh/Node/7-Zip）需换 scoop/zip 径；msix（pwsh）=每用户设计。
> 本机在位：git 2.55 / rg / uv / ffmpeg / ollama / python3.14 / winget；node=Cowork 裸 node（无 npm/npx）；缺件全数复核确认（与 CEO 实测一致零偏差）。

## 一 结论应用表（结论|应用面|归属司/机|落地动作）

| # | 结论 | 应用面 | 归属司/机 | 落地动作 |
|---|------|--------|-----------|----------|
| 1 | **gh 必装**（MIT·46,434★·当日活跃·api 直验） | GitHub 工作流命令行化（pr/api/runs/release/auth token）·AI 劳动免浏览器 | HQ+全机队（bm-a 主） | 非管理员：`scoop install gh`（2.101.0 zip+hash 直证）或 release zip+用户 PATH；winget GitHub.cli=MSI 需管理员 |
| 2 | **Node.js LTS 24 必装**（MIT 式·dist 官方 zip 直证 03-Aug-2026） | **npm/npx 修复=MCP servers 主径**（stdio 型大量 npx 分发·CEO 令四面之一） | bm-a 先行·b/c 随分发令 | 非管理员主径：`scoop install nodejs-lts`（24.21.0）或 dist `node-v24.19.0-win-x64.zip`(37MB) 解压+用户 PATH |
| 3 | **gitleaks 收口在案批件**（MIT·29,529★·portable zip） | 三机 git push 前密钥扫描（registry secret-scan 纳管族） | 全机队 | `winget install Gitleaks.Gitleaks`（**portable·非管理员直装可行**）+OH 接线单三判据照走 |
| 4 | **lychee 收口在案批件**（Apache-2.0·3,953★） | R-件/治理文本外链体检（周轮 cadence 预注册在案） | bm-a 调研管线 | `winget install lycheeverse.lychee`（**实测有包·无需 cargo**）+sha256 核验判据 |
| 5 | **Pester 收口在案批件**（Apache-2.0·原文在案逐字） | PS 工具族测试框架（orders-registry 等手卷断言→Pester 固化） | bm-a 先行 | `Install-Module Pester -Scope CurrentUser -Force -SkipPublisherCheck`（非管理员原生·锁 5.x 稳定线） |
| 6 | **检索增强四件 fd/fzf/jq/yq 全装**（Apache-2.0/MIT·jq 许可 MIT 原文已定谳） | AI/人检索（fd=find·fzf=模糊筛·jq=JSON 管道·yq=YAML 六格式）；jq=gh api 伴生件 | 全机队 | `winget install sharkdp.fd junegunn.fzf jqlang.jq MikeFarah.yq`（全 portable·非管理员一发装）；jq 反重复 OH 冲突按 CEO 直令重开（见 §二.8） |
| 7 | **7-Zip 26.03 装**（LGPL-2.1+·unRAR 条款已录·边界注记见 §二.10） | 资产包/模型权重 7z 命令行解压打包 | 全机队 | 非管理员：`scoop install 7zip`（**官方 MSI 解包用户级·shim 7z.exe**）；winget 7zip.7zip=MSI 需管理员 |
| 8 | **PowerShell 7.6 装**（MIT·msix 每用户） | 现代 PS 面（AI 新写脚本）；PS5.1 不卸·双壳并存 | bm-a 先行 | `winget install Microsoft.PowerShell`（msix·非管理员可行·低优先非首日） |
| 9 | **rclone 1.75.1 装**（MIT·portable） | 三机跨机/云同步命令行化（fleet-protocol 传输条款咬合） | 全机队 | `winget install Rclone.Rclone`（portable·非管理员可行） |
| 10 | delta 0.19.2 可选（MIT·portable） | git diff 可读性（多写者 rebase 校对省力） | bm-a | `winget install dandavison.delta` |
| 11 | **scoop 建议装为非管理员底座**（Unlicense/MIT 双许可·24.7k★·10,301 commits） | gh/Node/7zip 三件 MSI 类的用户级化+统一 `scoop update` 升级面+机队分发幂等件统一通道 | 全机队 | `irm get.scoop.sh \| iex`（**原生拒管理员运行**·装 ~\scoop·git clone 通道·HKCU 用户 PATH 自动）——先已审读 install.ps1 全文（见 §四） |
| 12 | fnm/aria2/yt-dlp/Go/cargo/trufflehog **parked** | 边界与理由全录 | — | 不装·重开触发器在册（见 §三） |

> 机队分发交接注记（P-15 第四面）：三通道安装面已定型（winget portable+msix / scoop / PSGallery）——幂等安装件建议按 `Get-Command 在位探针→缺件装→版本断言` 三段式包一层；bm-b/bm-c 令牌随分发令走，笔记本豁免位不装。

## 二 采用候选逐件（repo|api 直验|许可|安装法[winget id/zip/PSGallery]|契合|五门初判）
> 五门=契合/反重复/许可/健康/成本安全（oss-harvest.md §四正典）。许可证据分级：**A 级**=api.github.com license 字段直验+raw 原文逐字直采+官方站原文；**B 级**=winget 目录许可字段（注明）；**未验**=如实标注（api 限流死面）。

### 1. gh——cli/cli（GitHub 官方 CLI）【采用·必装首位】
- **api 直验**：MIT · 46,434★ · pushed 2026-09-28（当日）· Go · 未归档
- **许可**：MIT（api+A 级）
- **安装法**：winget `GitHub.cli`（2.101.0·wix MSI 机器级→**非管理员不可**）；非管理员主径=**scoop `gh`**（Main bucket 2.101.0 清单直证：gh_2.101.0_windows_amd64.zip+hash bc6c81…）或 release zip+用户 PATH
- **契合**：三机 git 工作流真增益——`gh pr/api/runs/release/auth token` 命令行化，AI 劳动免浏览器操作 GitHub；机队令牌管理直读；HQ 多仓 push/撞号对账/issue 面全 GitHub 化。
- **五门**：契合✓|反重复✓（无同类件）|许可✓ MIT|健康✓（当日活跃）|成本安全✓（注记：GH_TOKEN 入 secret-scan 白名单）→ **五门过·采用**

### 2. Node.js LTS——OpenJS（npm/npx 修复主径）【采用·必装】
- **元数据**：winget `OpenJS.NodeJS.LTS`=24.19.0（LTS 线=24「Jod」直证）·wix MSI 机器级；scoop `nodejs-lts`=24.21.0（Main 清单直证）；**dist 目录直读**（nodejs.org/dist/v24.19.0/·03-Aug-2026）：`node-v24.19.0-win-x64.zip` 37MB 实存+x64.msi 33MB+SHASUMS256
- **许可**：**MIT 式「Node.js license」原文逐字直采**（raw nodejs/node v24.19.0/LICENSE：「Permission is hereby granted…」+Joyent 继承段；捆绑件全宽松：Acorn/c-ares/libuv/undici MIT·ICU Unicode-3.0·OpenSSL Apache-2.0·V8 BSD·zlib——**零 GPL**）；api ★ 数限流未验（如实）
- **安装法（非管理员）**：①dist zip 解压 %LOCALAPPDATA%\Programs\nodejs+用户 PATH（`[Environment]::SetEnvironmentVariable('Path',…,'User')`）②scoop `nodejs-lts`（7z+env_add_path+npm prefix 持久化已内建）
- **契合**：**MCP 生态主径**——MCP server 大量以 npx 分发（CEO 令四面之一=stdio 型接 Codely settings.json）；Cowork 裸 node24 无 npm=npx -y mcp-server-* 全堵。
- **五门**：契合✓|反重复✓（裸 node 无包管理器不可替代）|许可✓（MIT 式·原文）|健康✓（LTS 24.19/24.21 双通道现行）|成本✓（用户级零外呼）→ **五门过·采用**

### 3. gitleaks——gitleaks/gitleaks【采用·在案已批未装收口】
- **api 直验**：MIT · 29,529★ · pushed 2026-09-23 · Go
- **安装法**：winget `Gitleaks.Gitleaks`（8.30.1·**portable zip（gitleaks_8.30.1_windows_x64.zip）→非管理员 winget 直装可行**）；备选 release zip/scoop
- **契合**：三机 push 前密钥扫描；OH-20260928-cph4 已批规则语料抄入——本件补二进制本体装位（OH 在案「Go 二进制直用=禁双建」parked 例外申请面：安装落位直令语境+语料/本体同仓同许可 MIT——收口面拍板）。
- **五门**：在案全过+今验双绿复验 → **采用**

### 4. lychee——lycheeverse/lychee【采用·在案已批未装收口】
- **api 直验**：Apache-2.0 · 3,953★ · pushed 2026-09-21 · Rust
- **安装法**：**winget `lycheeverse.lychee`（0.24.2·portable zip=官方 lychee-x86_64-pc-windows-msvc.zip）→非管理员可行**——「Rust 无 cargo 装不了」障碍不存在（winget 有包直证）；备选 scoop/release zip+官方 .sha256
- **契合**：R-件/治理文本外链体检（OH 预注册：sha256 核验+周轮/按需 cadence+假死域 allowlist+只读首扫面）。
- **五门**：在案全过+今验 → **采用**

### 5. Pester——pester/Pester【采用·在案已批未装收口】
- **api 直验**：NOASSERTION（GitHub 探测器不匹配·OH 定谳）· 3,346★ · pushed 2026-09-24
- **许可**：**Apache-2.0 原文在案逐字直验**（OH-20260928-cph4：raw /LICENSE「Copyright 2020 Pester team / Licensed under the Apache License, Version 2.0」——本窗 api NOASSERTION 复核一致：短式声明文件所致）；**PS 5.1 兼容逐字在案**（README「compatible with Windows PowerShell 5.1 and PowerShell 7.4 and newer」）
- **安装法**：**PSGallery `Install-Module Pester -Scope CurrentUser -Force -SkipPublisherCheck`**（非管理员原生可行·in-box 3.4→5.x 旁装需 -SkipPublisherCheck·锁 5.x 稳定线）；安装时操作注记：PS5.1 需先 `[Net.ServicePointManager]::SecurityProtocol='Tls12'`；若触发 NuGet provider 引导走 `Install-PackageProvider -Name NuGet -Scope CurrentUser -Force`
- **契合**：PS 工具族测试框架（Get-Lock 停锁破锁/Test-OrderLine/Quote-Sig 截断/Convert-IsoDuration/secret-scan 规则表——OH 首役三目标已预注册）。
- **五门**：在案全过+许可 A 级在案 → **采用**

### 6. fd——sharkdp/fd【采用】
- **api 直验**：Apache-2.0 · 44,568★ · pushed 2026-09-24 · Rust
- **安装法**：winget `sharkdp.fd`（10.5.0·portable zip→非管理员可行）；备选 scoop/zip
- **契合**：AI/人文件名检索（find 替代·与 rg 内容检索互补成对）。
- **五门**：契合✓|反重复✓|许可✓ Apache-2.0|健康✓|成本✓ → **五门过·采用**

### 7. fzf——junegunn/fzf【采用】
- **api 直验**：MIT · 83,280★ · pushed 2026-09-27 · Go
- **安装法**：winget `junegunn.fzf`（0.74.4·portable zip→非管理员可行）
- **契合**：人（CEO 观测窗/终端）模糊筛选主用+管道非交互档；装面口径=人机共用。
- **五门**：契合✓（人机）|反重复✓|许可✓ MIT|健康✓|成本✓ → **五门过·采用**

### 8. jq——jqlang/jq【采用·附反重复冲突注记】
- **api 直验**：NOASSERTION · 35,709★ · pushed 2026-09-27 · C
- **许可定谳**：**COPYING 原文逐字直采=MIT**（「jq is copyright (C) 2012 Stephen Dolan / Permission is hereby granted…」）+docs=CC-BY 3.0+捆绑件全宽松（dtoa/decNumber=ICU License/Heimdal/NetBSD 均 BSD 式）——**零 GPL**；winget 目录字段同记 MIT License（URL→COPYING）。
- **安装法**：winget `jqlang.jq`（1.8.2·**portable 单 exe jq-windows-amd64.exe→非管理员可行**）；备选 scoop/zip
- **反重复门在案冲突处置**：OH-20260928-cph4 曾判负（jsonl 单点用例·无查询痛·触发器=jsonl 规模/查询需求入册）。本件**不翻旧案**——重开理由=①CEO 直令点名检索增强四件②**新用例=gh api 管道伴生件**（gh 装后 GitHub 工作流标准管道 `gh api … | jq`）③安装成本近零（portable 单文件）。OH 判负面向 jsonl 旧用例保持 parked 不动。
- **契合**：gh api/registry API 输出/MCP 日志 JSON 处理一线命令化（PS5.1 ConvertFrom-Json 大 JSON 慢+GBK 坑在案）。
- **五门**：契合✓（gh 伴生管道）|反重复✓（冲突已处置如上）|许可✓（MIT 原文定谳）|健康✓|成本✓ → **五门过·采用（附注记）**

### 9. yq——mikefarah/yq【采用】
- **api 直验**：MIT · 16,023★ · pushed 2026-09-27 · Go
- **安装法**：winget `MikeFarah.yq`（4.53.6·portable 单 exe→非管理员可行）
- **契合**：YAML/TOML/CSV/XML/properties 六格式单件（jq 管 JSON·yq 管其余）——fleet 配置/机队协议 yaml/Tuanjie 项目设置面。
- **五门**：契合✓|反重复✓|许可✓ MIT|健康✓|成本✓ → **五门过·采用**

### 10. 7-Zip（ip7z/7zip·7z 命令行）【采用】
- **元数据**：winget `7zip.7zip`=26.03（wix MSI 机器级·发布者 Igor Pavlov·官方 7-zip.org 源）；scoop `7zip` 清单直证 ip7z/7zip GitHub release 26.03 同源
- **许可原文（A 级·官方 license.txt 逐字直采）**：7z.dll=「**GNU LGPL** as main license」+unRAR restriction 分码+BSD-3（LZFSE/ZSTD）+BSD-2（XXH64）分件；「All other files: the GNU LGPL」；**unRAR 条款原文**：「The unRAR sources cannot be used to re-create the RAR compression algorithm…may not be used to develop a RAR (WinRAR) compatible archiver」；官方明示「You can use 7-Zip on any computer, including a computer in a commercial organization」。
- **LGPL 边界注记（三红线执法）**：7z.exe 独立进程 CLI 使用=**无链接面·无产品交付链传染**（GPL/AGPL 红线不触发·LGPL≠GPL 交付链禁入面）；unRAR 条款约束的是源码再造 RAR 压缩器——解压使用面零影响；再分发二进制需随附许可信息（若未来把 7z 打进分发件则照办）。
- **安装法（非管理员主径）**：**scoop `7zip`**（Main 清单直证：下载官方 7z2603-x64.msi 后**解包不安装**（extract_dir=Files\7-Zip）+shim 7z.exe/7zG.exe）；备选官方 7z extra 包直解+用户 PATH；winget=MSI 需管理员。
- **契合**：资产包/模型权重/Unity 资产 7z 解包命令行化（ComfyUI 产线分发面）。
- **五门**：契合✓|反重复✓（缺位确认）|许可✓（LGPL-2.1+·边界注记如上）|健康✓（26.03 现行·license 2025 版权）|成本✓ → **五门过·采用**

### 11. PowerShell 7——PowerShell/PowerShell（pwsh）【采用·低优先】
- **许可原文（A 级）**：**MIT**（raw LICENSE.txt：「Copyright (c) Microsoft Corporation. / MIT License」逐字）
- **安装法**：winget `Microsoft.PowerShell`（7.6.6.0·**msix 每用户设计→非管理员可行**）；zip 备选（release win-x64.zip）；**PS5.1 不卸不动·双壳并存**（旧组件在役）
- **契合**：机队全 PS 5.1——PS7 给 AI 劳动现代 PS（性能/跨平台/语法）；与 Pester/PSScriptAnalyzer 同版兼容（PSA 已登能力引用不复制）。
- **五门**：契合✓|反重复✓|许可✓（MIT 原文）|健康✓（7.6 当前线·api ★ 数限流未验如实）|成本✓ → **五门过·采用（非首日必装）**

### 12. rclone——rclone/rclone【采用候选】
- **许可原文（A 级）**：**MIT**（raw COPYING：「Copyright (C) 2012 by Nick Craig-Wood」逐字）
- **安装法**：winget `Rclone.Rclone`（1.75.1·portable zip→非管理员可行）
- **契合**：一人 CEO+三机机队跨机/云同步命令行化（bm-a↔bm-b↔bm-c 资产/权重/台账传输·fleet-protocol 传输条款咬合）——替散装 scp/网盘 GUI；api ★ 数限流未验（如实）。
- **五门**：契合✓|反重复✓（无同类）|许可✓（MIT 原文）|健康✓（1.75.1 现行）|成本✓（配置前零外呼）→ **五门过·采用**

### 13. delta——dandavison/delta【采用·可选轻量档】
- **许可原文（A 级）**：**MIT**（raw LICENSE：「Copyright 2020 Dan Davison」逐字）
- **安装法**：winget `dandavison.delta`（0.19.2·portable zip→非管理员可行）
- **契合**：git diff 可读性（多写者 rebase 常态肉眼校对省力）；api ★ 数限流未验（如实）。
- **五门**：全✓ → **采用（可选·锦上添花）**

### 14. scoop——ScoopInstaller/Scoop（非管理员用户级包管理器）【评估结论：值得装·底座定位】
- **许可原文（A 级）**：**「Unlicense or MIT」双许可**（raw LICENSE 逐字：SPDX-License-Identifier: UNLICENSE or MIT·Copyright Luke Sampson 2013-2017+contributors·v0.2.0 起双许可）——极宽松
- **健康（HTML 面补验·github.com 页直读）**：**24.7k★**·1.5k forks·**10,301 commits**·topics=installer/powershell/windows；api 直验限流（如实·已两批重试）
- **安装脚本全文审读（A 级·get.scoop.sh→301→scoopinstaller/install install.ps1 全文）**：默认装 `$env:USERPROFILE\scoop`（**用户级**）；**原生拒管理员运行**（非 -RunAsAdmin 且检测到管理员则 Deny-Install——非管理员是设计主径）；git 可用时走 `git clone ScoopInstaller/Scoop + Main bucket`（本机 git 在位✓）、否则 zip 兜底；shim 写 ~\scoop\shims 并**写 HKCU 用户 PATH**（用户注册表·无需管理员）；要求执行策略∈[Unrestricted,RemoteSigned,Bypass]（否则提示 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`）；参数=-ScoopDir/-ScoopGlobalDir/-ScoopCacheDir/-Proxy 族/-RunAsAdmin；脚本本体=Unlicense。
- **评估**：装它**值得**——①gh/Node/7zip 三件在 winget 是机器级 MSI（非管理员不可），scoop Main bucket 三件全有（gh 2.101.0/nodejs-lts 24.21.0/7zip 26.03 清单直证）②统一 `scoop update *` 升级面③机队分发幂等件可三通道统一。风险注记：`irm|iex` 管道执行=装前已全文审读（本件完成）；与 winget 互补非双建（winget 管 portable/msix 面·scoop 管 MSI 类用户级面）。
- **五门**：契合✓（非管理员底座）|反重复✓（补位非双建）|许可✓（Unlicense/MIT 原文）|健康✓（24.7k★·万级 commits）|成本✓ → **五门过·建议装**

## 三 parked+理由
1. **fnm（Schniz/fnm）——红线发现**：winget 目录许可字段=**GPL-3.0**（B 级直记·原文未采=GPL 全文超本窗预算·如实）。纯本地 CLI 使用面本可过红线，但 Node 用户级已有 dist zip/scoop 双径（非必要）+集团「能不引 GPL 就不引」口径 → **不选**。重开触发器=Node 多版本并行刚需且 zip/scoop 不敷用。
2. **aria2（aria2.aria2 1.37.0 有包·winget 字段=GPL-2.0-or-later）**：①合规面——批量下载工具无在册业务工位+版权滥用联想面（公司合规口径未立）②curl.exe（系统自带）+winget 已覆盖下载需求。GPL 注记：纯本地 CLI 使用面可过但无必要引入。重开触发器=多线程断点续传正当业务（大文件出站分发）。
3. **yt-dlp（yt-dlp.yt-dlp 2026.08.19 有包·LICENSE 原文=Unlicense 公有领域·A 级换源直采）**：用途合规面——平台视频抓取存在 ToS/版权风险·无在册业务工位（BigStream 生产不依赖抓取第三方平台）。许可零问题·纯合规 parked。重开触发器=授权素材引用工具需求入册另裁。
4. **Go/cargo 运行时**：推荐清单全部单文件二进制（gh/fd/fzf/jq/yq/gitleaks/lychee/rclone/delta）/PS 模块/用户级包管理器分发，无源码构建需求→反重复门判负不装。重开触发器=需本地 build 的 Rust/Go 工具入清单。
5. **trufflehog（gitleaks 同类备选对照）**：winget search **无包（实测死面）**+api 限流未直验——**未验明不采**（零编造：不引用任何印象级许可描述；若未来评估需先 api 直验其许可再入册）。

## 四 实搜面实录
- **本机只读盘点**（Get-Command+IsInRole）：**Admin=False**；PS=5.1.26100；在位=git/rg/uv/python/ffmpeg/ollama/winget；缺=gh/fd/fzf/jq/yq/7z/gitleaks/lychee/npm/npx/scoop/cargo/go/pwsh（全数与 CEO 实测一致）。
- **winget search ×17**（零安装）：GitHub.cli 2.101.0 / OpenJS.NodeJS.LTS 24.19.0 / Gitleaks.Gitleaks 8.30.1 / **lycheeverse.lychee 0.24.2** / sharkdp.fd 10.5.0 / junegunn.fzf 0.74.4 / jqlang.jq 1.8.2 / MikeFarah.yq 4.53.6 / 7zip.7zip 26.03 / Microsoft.PowerShell 7.6.6.0 / aria2.aria2 1.37.0 / yt-dlp.yt-dlp 2026.08.19 / Rclone.Rclone 1.75.1 / Schniz.fnm 1.39.0 / dandavison.delta 0.19.2 全命中；**scoop 本体无包**（同名仅第三方壳 rscoop/UniGetUI/OmniGet）；**trufflehog 无包（死面）**。
- **winget show ×15**（installer 类型+许可字段）：gh=wix MSI / Node=wix MSI / 7zip=wix MSI / pwsh=**msix** / gitleaks·lychee·fd·fzf·jq·yq·rclone·delta·fnm=**portable zip（非管理员 winget 直装可行）**；目录许可字段：gh MIT·Node MIT·gitleaks MIT·lychee Apache-2.0·fd Apache-2.0·fzf MIT·jq MIT License(→COPYING)·yq MIT·7zip LGPL-2.1·pwsh MIT·rclone MIT·delta MIT·**fnm GPL-3.0**·aria2 GPL-2.0-or-later·yt-dlp Unlicense。
- **api.github.com 直验 ×8 成功**（A 级）：cli/cli=MIT/46,434★/pushed 09-28；gitleaks=MIT/29,529★/09-23；lychee=Apache-2.0/3,953★/09-21；Pester=NOASSERTION/3,346★/09-24；fd=Apache-2.0/44,568★/09-24；fzf=MIT/83,280★/09-27；jq=NOASSERTION/35,709★/09-27；yq=MIT/16,023★/09-27。全部未归档、周内活跃。
- **api 限流死面（如实两批实录）**：ScoopInstaller/Scoop·nodejs/node·ip7z/7zip·aria2·yt-dlp·PowerShell·rclone 十一查 403 rate limit exceeded（匿名 60/h 配额·判因=本令三并行调研代理共享出口 IP 烧尽；两批重试同果）→ 换源律执行完毕：**许可全以 raw 原文逐字直采定谳（10 件 A 级）**+winget B 级字段+github.com HTML 补验（scoop 24.7k★ 直读成功）+官方站原文（7-zip.org license.txt）——未按「未验明」结案任何采用件；未验项（node/7zip/pwsh/rclone/aria2/yt-dlp 的 api ★ 数与 trufflehog 全量）逐处如实标注。
- **raw 原文直采 ×10（A 级逐字）**：jq COPYING=MIT+docs CC-BY+捆绑宽松；node v24.19.0 LICENSE=MIT 式+捆绑宽松；PowerShell LICENSE.txt=MIT；rclone COPYING=MIT；delta LICENSE=MIT；scoop LICENSE=Unlicense/MIT 双许可；yt-dlp LICENSE=Unlicense（换源成功）；7-zip.org license.txt=LGPL+unRAR 条款；get.scoop.sh→install.ps1 全文（用户级·拒管理员·git clone 通道）；Pester raw /LICENSE=Apache-2.0（OH 在案逐字·本窗 api 复核）。
- **官方分发面直证**：nodejs.org/dist/v24.19.0/ 目录直读——`node-v24.19.0-win-x64.zip` 37MB 实存（03-Aug-2026）+SHASUMS256；scoop Main 三清单直读——gh.json（zip+hash）/nodejs-lts.json（7z+env_add_path+npm 持久化）/7zip.json（**官方 MSI 解包** extract_dir=Files\7-Zip+shim）。
- **失败面全录**：①Pester LICENSE.md 404（正确名=LICENSE 无扩展·OH 同坑先例 LICENSE.txt 亦 404）；②yt-dlp UNLICENSE 404→LICENSE 换源成功；③api 限流 11 查 403（见上）；④trufflehog winget 无包；⑤「powershell 单实例锁」方向未涉（OH 在案死面·不重复验证）。
- **读数与零执法面**：外部读取 ≈35 处（api 19/raw 10/官方站 3/HTML 2/scoop 清单 3·含失败）；本地只读命令 4 组；**零安装·零 PATH 改动·零注册表写入**（HKCU 写 PATH 仅属将来安装件动作·本调研未执行）。
- **注入面**：外部内容仅作证据采录；网页/脚本中任何指令零执行零采信（install.ps1 全文仅审读未运行）。
