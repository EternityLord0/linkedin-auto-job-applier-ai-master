# get_exe_path.py
import ctypes
import ctypes.wintypes

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

kernel32 = ctypes.windll.kernel32

def get_process_path(pid):
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h_proc:
        return f"OpenProcess failed: {ctypes.GetLastError()}"
    
    buf = ctypes.create_unicode_buffer(1024)
    size = ctypes.wintypes.DWORD(len(buf))
    if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
        kernel32.CloseHandle(h_proc)
        return buf.value
    else:
        err = ctypes.GetLastError()
        kernel32.CloseHandle(h_proc)
        return f"QueryFullProcessImageName failed: {err}"

import subprocess, csv
lines = subprocess.run(['tasklist', '/fo', 'csv'], capture_output=True, text=True).stdout.splitlines()
for r in csv.reader(lines):
    if len(r) > 1 and r[0].upper().startswith("CUH"):
        pid = int(r[1])
        print(f"PID {pid} ({r[0]}): {get_process_path(pid)}")
