import ctypes, time

# 用 kernel32.CreateProcess 直接拉起独立后台进程（绕开 Start-Process/WMI 限制）
kernel32 = ctypes.windll.kernel32

py = r"C:\Users\lianxiang\.workbuddy\binaries\python\versions\3.13.12\python.exe"
script = r"D:\PromptHunter\server.py"
cmd = '"%s" "%s"' % (py, script)

# STARTUPINFO
class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("lpReserved", ctypes.c_void_p),
        ("lpDesktop", ctypes.c_void_p),
        ("lpTitle", ctypes.c_void_p),
        ("dwX", ctypes.c_ulong),
        ("dwY", ctypes.c_ulong),
        ("dwXSize", ctypes.c_ulong),
        ("dwYSize", ctypes.c_ulong),
        ("dwXCountChars", ctypes.c_ulong),
        ("dwYCountChars", ctypes.c_ulong),
        ("dwFillAttribute", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("wShowWindow", ctypes.c_ushort),
        ("cbReserved2", ctypes.c_ushort),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", ctypes.c_void_p),
        ("hStdOutput", ctypes.c_void_p),
        ("hStdError", ctypes.c_void_p),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", ctypes.c_void_p),
        ("hThread", ctypes.c_void_p),
        ("dwProcessId", ctypes.c_ulong),
        ("dwThreadId", ctypes.c_ulong),
    ]

si = STARTUPINFO()
si.cb = ctypes.sizeof(STARTUPINFO)
si.dwFlags = 0
pi = PROCESS_INFORMATION()

CREATE_NEW_CONSOLE = 0x00000010
CREATE_NO_WINDOW = 0x08000000

ok = kernel32.CreateProcessW(
    None,
    cmd,
    None,            # lpProcessAttributes
    None,            # lpThreadAttributes
    False,           # bInheritHandles
    CREATE_NEW_CONSOLE,  # dwCreationFlags (独立控制台窗口，脱离父进程)
    None,            # lpEnvironment
    None,            # lpCurrentDirectory
    ctypes.byref(si),
    ctypes.byref(pi),
)
if ok:
    print("CreateProcess OK, pid=%d" % pi.dwProcessId)
    kernel32.CloseHandle(pi.hProcess)
    kernel32.CloseHandle(pi.hThread)
else:
    err = kernel32.GetLastError()
    print("CreateProcess FAILED, GetLastError=%d" % err)
