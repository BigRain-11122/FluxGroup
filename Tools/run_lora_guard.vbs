' run_lora_guard.vbs - 零窗口拉起 LoRA 护栏（计划任务只认这一层，避免直接起 powershell 闪黑窗）
Dim sh, cmd
Set sh = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""C:\Users\sjs20\Desktop\FluxGroup\Tools\lora_chain_guard.ps1"""
sh.Run cmd, 0, False
Set sh = Nothing