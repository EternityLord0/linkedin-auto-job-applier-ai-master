# inspect_targets.py
import csv
import subprocess

cmd = "wmic process get processid,name,executablepath /format:csv"
output = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
reader = csv.reader(output.strip().splitlines())

for row in reader:
    if len(row) >= 3:
        node, exe, name, pid = row[0], row[1], row[2], row[3] if len(row) > 3 else ""
        if any(k in name.lower() for k in ["cuh", "usb", "update", "rede", "key", "display", "cowork"]):
            print(f"PID: {pid} | Name: {name} | Path: {exe}")
