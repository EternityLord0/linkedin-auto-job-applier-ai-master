# final_check_persistence.py
import subprocess
import csv

print("1. Checando Tarefas Agendadas restantes:")
cmd_tasks = 'schtasks /query /fo csv /v'
try:
    out = subprocess.check_output(cmd_tasks, shell=True, text=True, errors="ignore")
    reader = csv.reader(out.strip().splitlines())
    header = next(reader, None)
    for r in reader:
        if len(r) > 8:
            task_name = r[1]
            task_run = r[8] if len(r) > 8 else ""
            if any(k in task_name.lower() or k in task_run.lower() for k in ["update", "rede", "cuh", "system32", "temp"]):
                if not any(ign in task_name.lower() for ign in ["onedrive", "opera", "google", "edge", "directx"]):
                    print(f"  Tarefa suspeita: {task_name} -> {task_run}")
except Exception as e:
    print(e)

print("\n2. Checando chaves Run no Registro:")
for hive in ["HKCU", "HKLM"]:
    cmd_reg = f'reg query "{hive}\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"'
    try:
        print(f"--- {hive} Run ---")
        print(subprocess.check_output(cmd_reg, shell=True, text=True, errors="ignore"))
    except Exception as e:
        print(e)
