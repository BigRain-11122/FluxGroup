' InvisibleRunner.vbs - silent runner for scheduled tasks (group U060 pattern).
' Group copy for HQ-scheduled tasks (EvolutionTick etc). No window ever flashes.
' Usage: wscript.exe //B //nologo InvisibleRunner.vbs <exe> [args...]
' 2026-11-09 CEO zero-desktop-disturb law: launching a .cmd/.bat FILE directly
' triggers the Windows attachment manager "Open File - Security Warning" popup
' for unsigned high-risk extensions, MOTW or not (CEO caught it twice). Fix:
' route .cmd/.bat targets through cmd.exe /c <script> -- the script becomes an
' ARGUMENT instead of a shell-launched file, the attachment manager is never
' consulted. Window style 0 (hidden) kept.
Dim sh, args, i, a, target, isScript
Set sh = CreateObject("WScript.Shell")
args = ""
For i = 0 To WScript.Arguments.Count - 1
    a = WScript.Arguments(i)
    If InStr(a, " ") > 0 Or InStr(a, "&") > 0 Or InStr(a, "^") > 0 Or InStr(a, "=") > 0 Then
        If Left(a, 1) <> """" Then a = Chr(34) & a & Chr(34)
    End If
    args = args & " " & a
Next
If args = "" Then WScript.Quit 1
target = Mid(args, 2)
isScript = (InStr(LCase(target), ".cmd") > 0) Or (InStr(LCase(target), ".bat") > 0)
If isScript And Left(LCase(target), 5) <> "cmd /" And Left(LCase(target), 4) <> "cmd" Then
    ' first token is a bare .cmd/.bat path -> re-route via cmd.exe /c
    Dim sp, firstTok
    sp = InStr(target & " ", " ")
    If sp > 0 Then
        firstTok = Left(target, sp - 1)
        target = "cmd.exe /c " & firstTok & Mid(target, sp)
    End If
End If
WScript.Quit sh.Run(target, 0, True)
