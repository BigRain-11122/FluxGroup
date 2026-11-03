
- [2026-10-24 13:09:05] 界面类改动必须「构建→截图→看图」闭环：只靠代码推理会漏明显缺陷（网格底部裁切、订单板被切一半、占位标签压中央，全是截图后才发现）。取证法=Start-Process 启动 player（-screen-width 1280 -screen-height 720 -screen-fullscreen 0）→等 7s→SetForegroundWindow+CopyFromScreen 存 PNG→read_file 看图→Kill；每次版面改动改前/改后各一张对照。

- [2026-11-02 14:14:38] Mac 侧卡 rc=127 判读（2026-11-02 实测）：执行器用的是最小 PATH，里面只有 `/usr/bin/python3`；`python` 虽然存在（`~/.pyenv/shims/python`）但**不在 PATH**，所以本机卡写成 `python ...` 会瞬间 rc=127（0.0 秒、零产物）。规则：**跑在 bm-m 的卡一律写 `python3`**；对 Windows 机写 `python` 才对。判读口诀：rc=127 且 0.0 秒 = 命令根本没找到，不是脚本报错，别去改业务逻辑。
