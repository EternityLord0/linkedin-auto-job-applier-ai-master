# check_system.py
import subprocess
import json
import os

try:
    import psutil
    has_psutil = True
except ImportError:
    has_psutil = False

print(f"psutil available: {has_psutil}")

if has_psutil:
    suspicious = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            exe = proc.info.get('exe') or ''
            name = proc.info.get('name') or ''
            # Filter user processes
            if exe and ('AppData' in exe or 'Temp' in exe or 'Users' in exe):
                # Ignore Antigravity / IDE / git / node
                if not any(k in exe for k in ['Antigravity', 'npm', 'node', 'hermes', 'git']):
                    suspicious.append({
                        'pid': proc.info['pid'],
                        'name': name,
                        'exe': exe,
                        'cmdline': proc.info.get('cmdline')
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    print("\n--- SUSPICIOUS APPDATA / USER PROCESSES ---")
    for s in suspicious:
        print(f"PID: {s['pid']} | Name: {s['name']} | Exe: {s['exe']}")
else:
    # Use powershell Get-CimInstance without hanging
    cmd = 'powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like \'*AppData*\' } | Select-Object ProcessId, Name, ExecutablePath | ConvertTo-Json"'
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    print(res.stdout)
