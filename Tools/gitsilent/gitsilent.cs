// gitsilent - transparent git relay, GUI-subsystem + native CreateProcess (U060 silence)
// Why: GUI-subsystem apps (UGit/Electron, codely, etc.) spawn bare "git"; any
// console-subsystem helper would get a VISIBLE new console window on Win11
// (default terminal = Windows Terminal) = popup storm (CEO order 2026-10-08).
// Design: this relay is /target:winexe (GUI subsystem -> Windows never creates a
// console for it), and it forwards argv verbatim to the real system git with
// CREATE_NO_WINDOW + explicit STARTF_USESTDHANDLES so stdio flows through the
// inherited handles (works for pipe parents like UGit AND console parents).
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

class GitSilent
{
    private const uint CREATE_NO_WINDOW = 0x08000000;
    private const int STARTF_USESTDHANDLES = 0x00000100;
    private const uint STD_INPUT_HANDLE = unchecked((uint)-10);
    private const uint STD_OUTPUT_HANDLE = unchecked((uint)-11);
    private const uint STD_ERROR_HANDLE = unchecked((uint)-12);
    private const uint INFINITE = 0xFFFFFFFF;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct STARTUPINFO
    {
        public uint cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateProcessW(
        string lpApplicationName,
        StringBuilder lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetStdHandle(uint nStdHandle);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr GetCommandLine();

    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool DuplicateHandle(IntPtr hSourceProcessHandle, IntPtr hSourceHandle, IntPtr hTargetProcessHandle, out IntPtr lpTargetHandle, uint dwDesiredAccess, bool bInheritHandle, uint dwOptions);

    private const uint DUPLICATE_SAME_ACCESS = 2;

    // 2026-10-08 fix: std handles from ConPTY hosts are often NOT inheritable, so the
    // child git silently lost stdout (empty git log/show/diff, 0-byte > redirects).
    // Duplicate each handle into ourselves with the inheritable flag set before spawn.
    private static IntPtr MakeInheritable(IntPtr h)
    {
        if (h == IntPtr.Zero || h == (IntPtr)(-1)) return h;
        IntPtr dup;
        if (DuplicateHandle(GetCurrentProcess(), h, GetCurrentProcess(), out dup, 0, true, DUPLICATE_SAME_ACCESS))
        {
            return dup;
        }
        return h; // fall back to the original handle
    }

    private static string RealGitPath()
    {
        string[] candidates =
        {
            @"C:\Program Files\Git\cmd\git.exe",
            @"C:\Program Files\Git\bin\git.exe",
            @"C:\Program Files (x86)\Git\cmd\git.exe"
        };
        foreach (string c in candidates)
        {
            if (File.Exists(c)) return c;
        }
        return null;
    }

    // Strip our own exe token from the raw command line, keep the rest verbatim
    // (preserves the caller's original quoting exactly).
    private static string ForwardArgs(string rawCmdLine)
    {
        if (rawCmdLine.StartsWith("\""))
        {
            int close = rawCmdLine.IndexOf('"', 1);
            if (close >= 0 && close + 1 < rawCmdLine.Length)
            {
                return rawCmdLine.Substring(close + 1).TrimStart(' ', '\t');
            }
            return "";
        }
        int sp = rawCmdLine.IndexOf(' ');
        if (sp < 0) return "";
        return rawCmdLine.Substring(sp + 1).TrimStart(' ', '\t');
    }

    static int Main()
    {
        string realGit = RealGitPath();
        if (realGit == null) return 127;

        string raw = Marshal.PtrToStringUni(GetCommandLine());
        string fwd = ForwardArgs(raw);

        // Child command line: argv[0] = real git path (quoted), then verbatim args.
        StringBuilder cmdLine = new StringBuilder();
        cmdLine.Append('"').Append(realGit).Append('"');
        if (fwd.Length > 0) cmdLine.Append(' ').Append(fwd);

        STARTUPINFO si = new STARTUPINFO();
        si.cb = (uint)Marshal.SizeOf(typeof(STARTUPINFO));
        si.dwFlags = (uint)STARTF_USESTDHANDLES;
        si.hStdInput = MakeInheritable(GetStdHandle(STD_INPUT_HANDLE));
        si.hStdOutput = MakeInheritable(GetStdHandle(STD_OUTPUT_HANDLE));
        si.hStdError = MakeInheritable(GetStdHandle(STD_ERROR_HANDLE));

        PROCESS_INFORMATION pi;
        bool ok = CreateProcessW(
            null,
            cmdLine,
            IntPtr.Zero,
            IntPtr.Zero,
            true,               // bInheritHandles: std handles reach the child
            CREATE_NO_WINDOW,   // never a new console window
            IntPtr.Zero,        // inherit environment
            null,               // inherit current directory
            ref si,
            out pi);

        if (!ok) return 126;

        WaitForSingleObject(pi.hProcess, INFINITE);
        uint code;
        GetExitCodeProcess(pi.hProcess, out code);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return (int)code;
    }
}
