# find_cuh.py
import subprocess

try:
    out = subprocess.check_output("wmic service get name,displayname,pathname /format:csv", shell=True, text=True, errors="ignore")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["cuh", "cowork", "display", "usb", "update"]):
            print(line)
except Exception as e:
    print(e)
