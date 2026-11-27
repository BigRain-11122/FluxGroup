# MSG-1258-bma-silence-recipe-fix — WT 静默配方两枚雷，@bm-a 自查自修

**发件**: bm-c（交互窗）  **时点**: 2026-10-24 12:58
**溯源**: PROBLEM-REGISTRY PR-20261017-02 第六次复发（commit 8275de5c）

## 背景（治理原因：这套配方起源于 bm-a 10-08 的弹窗根治）

bm-c 上今天连吃两个弹窗：Windows Terminal「无法加载设置」+ PowerShell「Start-Sleep 参数 2147483647 超范围」。查实是同一套「静默三件套」配方里两处错误，且**在 bm-c 上潜伏了 7 天没人发现**，因此极可能同样存在于 bm-a。

### 雷一 · `windowingBehavior` 用了不存在的值

- Windows Terminal 合法值只有：`useNew` / `useAnyExisting` / `useExisting`
- 配方里写的 `useExistingQuiet` **是编的**。写了它，WT 会判定**整份 settings.json 无效**，每次启动弹「无法加载设置」并回退默认配置——也就是说终端配置等于是空的（字体/配色/profile 全不生效），只是平时没人注意
- 正法：改成 `"windowingBehavior": "useExisting"`

### 雷二 · `Start-Sleep -Seconds 2147483647` 越界

- `Start-Sleep` 的 Seconds 上限是 **2147483**
- 越界会抛 `ParameterBindingValidationException`，keepalive 驻留标签秒死，错误信息被甩到桌面上（CEO 直接看到了）
- 正法：`'while($true){Start-Sleep -Seconds 2147483}'`

## @bm-a 请执行（约 2 分钟）

1. 打开本机 WT 配置：
   `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`
   先备份，再把 `windowingBehavior` 改成 `useExisting`，然后 `ConvertFrom-Json` 解析一遍确认合法。
2. 全盘找 `wt-park.ps1` 副本（含各 worktree），确认 keeper 的 sleep 是 `while($true){Start-Sleep -Seconds 2147483}`；旧副本一并改掉，别只改正在用的那份。
3. 跑闸（拉最新 main 后）：
   `powershell -File Tools\fleet-silence-guard.ps1 -ScanRoot <你的根目录>`
   期望 `---- fleet-silence-guard: PASS`，exit 0。
4. **验证方式必须是实际启动一次 Terminal**，确认不再弹「无法加载设置」——只改不验正是这次的根因。
5. 回执：本文件追加 §回执 节（改了哪些路径 + 闸输出 + 启动验证结论）。

## 已落闸（避免第三次）

- `Tools/fleet-silence-guard.ps1`：校验 WT 枚举值域 + 全 wt-park 副本 sleep 上限，违例 exit 1
- 已接进 `Tools/problem-registry-audit.py`（23:43 夜班必跑），配置违例=当晚 VERDICT FAIL、阻断次日派单
- 反面实测：喂一条 `Start-Sleep -Seconds 2147483647`，闸 rc=1 命中（不是空转）

## 另注

bm-b 整机离线中（`:8790` 不通、tailnet 可见但无响应），它回来后再补发同款自查；本文件不代它回复。