# UTF-8 编码全链（幂等·静默）
# 用法（在 -Command 里一行前置，或 -File 脚本里 dot-source）：
#   . "C:\Users\sjs20\Desktop\FluxGroup\Tools\ps1\utf8.ps1"
#
# 背景：Codely CLI 以 `powershell.exe -NoProfile -Command` 启动 shell，
#       profile 不加载；PS 5.1 管道重定向下 Console.OutputEncoding 默认 CP936，
#       中文输出按 GBK 写出、被 UTF-8 侧解码 → 乱码。
#       本脚本把控制台 / 管道 / 子进程三层统一成 UTF-8。

try {
    $__utf8 = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = $__utf8
    [Console]::InputEncoding  = $__utf8
    $OutputEncoding = $__utf8
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'
    $PSDefaultParameterValues['Out-File:Encoding']    = 'utf8'
    $PSDefaultParameterValues['Set-Content:Encoding'] = 'utf8'
    $PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
    Remove-Variable __utf8 -ErrorAction SilentlyContinue
} catch {
    # 编码设置失败不得中断调用方脚本
}