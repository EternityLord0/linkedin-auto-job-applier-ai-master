# get_parent.py
import subprocess

cmd = "wmic process where processid=22152 get name,commandline,executablepath,parentprocessid /format:list"
try:
    print(subprocess.check_output(cmd, shell=True, text=True, errors="ignore"))
except Exception as e:
    print(e)
