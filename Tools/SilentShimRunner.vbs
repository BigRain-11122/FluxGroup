' SilentShimRunner.vbs - hidden runner + gitsilent PATH prepend (U060 machine silence)
' Drop-in replacement for InvisibleRunner.vbs in scheduled-task actions.
' Same proven hidden-chain semantics (args joined, re-quoted when needed, hidden
' run, true exit code propagated) PLUS one prepend: the gitsilent git shim dir
' goes to the FRONT of the process PATH so every bare 'git' spawn downstream
' (codely session internal git, loop scripts, etc.) resolves to the silent
' GUI-subsystem relay instead of flashing a Windows Terminal window.
' Root cause: console-less parents (codely.exe etc.) spawning console tools get
' one VISIBLE Windows Terminal per command on Win11 (CEO order 2026-10-08).
Dim sh, args, i, a, p
Set sh = CreateObject("WScript.Shell")
p = sh.Environment("PROCESS")("Path")
sh.Environment("PROCESS")("Path") = "C:\Users\sjs20\tools\gitsilent;" & p
args = ""
For i = 0 To WScript.Arguments.Count - 1
    a = WScript.Arguments(i)
    If InStr(a, " ") > 0 Or InStr(a, "&") > 0 Or InStr(a, "^") > 0 Or InStr(a, "=") > 0 Then
        If Left(a, 1) <> """" Then a = Chr(34) & a & Chr(34)
    End If
    args = args & " " & a
Next
If args = "" Then WScript.Quit 1
WScript.Quit sh.Run(Mid(args, 2), 0, True)
