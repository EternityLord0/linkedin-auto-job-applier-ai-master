# list_config_msi.py
import os
import subprocess

try:
    print(subprocess.check_output('dir "C:\\Config.Msi" /a', shell=True, text=True, errors="ignore"))
except Exception as e:
    print("Erro no dir:", e)
