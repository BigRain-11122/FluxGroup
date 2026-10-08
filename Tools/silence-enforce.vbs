' silence-enforce.vbs - silent wrapper (U060: zero-window law)
' Runs Tools\silence-enforce.ps1 fully hidden via wscript //B //nologo chain.
Dim sh, f, cmd
Set sh = CreateObject("WScript.Shell")
f = sh.CurrentDirectory
If Right(f, 1) <> "\" Then f = f & "\"
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & f & "Tools\silence-enforce.ps1"""
sh.Run cmd, 0, False
