import os, ctypes, time

class _WIN32_FIND_DATAW(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("dwFileAttributes", ctypes.c_uint32),
        ("ftCreationTime", ctypes.c_int64),
        ("ftLastAccessTime", ctypes.c_int64),
        ("ftLastWriteTime", ctypes.c_int64),
        ("nFileSizeHigh", ctypes.c_uint32),
        ("nFileSizeLow", ctypes.c_uint32),
        ("dwReserved0", ctypes.c_uint32),
        ("dwReserved1", ctypes.c_uint32),
        ("cFileName", ctypes.c_wchar * 260),
        ("cAlternateFileName", ctypes.c_wchar * 14),
    ]

_k = ctypes.windll.kernel32
_k.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]; _k.GetFileAttributesW.restype = ctypes.c_uint32
_k.DeleteFileW.argtypes = [ctypes.c_wchar_p]; _k.DeleteFileW.restype = ctypes.c_int
_k.RemoveDirectoryW.argtypes = [ctypes.c_wchar_p]; _k.RemoveDirectoryW.restype = ctypes.c_int
_k.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]; _k.SetFileAttributesW.restype = ctypes.c_int
_k.FindFirstFileW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(_WIN32_FIND_DATAW)]; _k.FindFirstFileW.restype = ctypes.c_void_p
_k.FindNextFileW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_WIN32_FIND_DATAW)]; _k.FindNextFileW.restype = ctypes.c_int
_k.FindClose.argtypes = [ctypes.c_void_p]; _k.FindClose.restype = ctypes.c_int

INVALID = 0xFFFFFFFF
DIR = 0x10
RO = 0x1

def delete_tree(path):
    attrs = _k.GetFileAttributesW(path)
    if attrs == INVALID:
        return
    if not (attrs & DIR):
        if attrs & RO:
            _k.SetFileAttributesW(path, attrs & ~RO)
        _k.DeleteFileW(path)
        return
    fd = _WIN32_FIND_DATAW()
    h = _k.FindFirstFileW(path + "\\*", ctypes.byref(fd))
    if h == INVALID:
        _k.RemoveDirectoryW(path)
        return
    try:
        while True:
            raw = fd.cFileName
            name = raw.value if hasattr(raw, "value") else raw
            if name not in (".", ".."):
                delete_tree(path + "\\" + name)
            if not _k.FindNextFileW(h, ctypes.byref(fd)):
                break
    finally:
        _k.FindClose(h)
    cur = _k.GetFileAttributesW(path)
    if cur != INVALID and (cur & RO):
        _k.SetFileAttributesW(path, cur & ~RO)
    _k.RemoveDirectoryW(path)

base = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-deploy\images"
for d in ("twitter", "twitter-cat1", "twitter-cat2"):
    p = os.path.join(base, d)
    if os.path.exists(p):
        n = sum(1 for _, _, fs in os.walk(p) for _ in fs)
        t = time.time()
        delete_tree(p)
        print("删除 %s/ : %d 个文件, 用时 %.2fs, 仍存在=%s" % (d, n, time.time() - t, os.path.exists(p)))
    else:
        print("%s/ 不存在，跳过" % d)

print("--- 剩余内容 ---")
for x in sorted(os.listdir(base)):
    print("  ", x)
