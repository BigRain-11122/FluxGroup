' run_lora_night.vbs - zero-window nightly LoRA chain (portraits -> train extras -> train female lead)
Dim sh, fso, ps, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ps = "C:\Users\sjs20\Desktop\FluxGroup\Tools\lora_night_train.ps1"
If Not fso.FileExists(ps) Then WScript.Quit 1
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps & """ -TrainFirst extras_v721,her_mv0001 -PortraitName her_mv0001 -PortraitTrigger h01 -PortraitCount 24"
sh.Run cmd, 0, False
