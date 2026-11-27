' Run-Hidden.vbs - launch a command with no console window.
' ASCII only. Used so scheduled tasks never flash a black window on the CEO desktop.
Set sh = CreateObject("WScript.Shell")
If WScript.Arguments.Count = 0 Then WScript.Quit 2
cmd = ""
For i = 0 To WScript.Arguments.Count - 1
  If i > 0 Then cmd = cmd & " "
  cmd = cmd & WScript.Arguments(i)
Next
sh.Run cmd, 0, False
