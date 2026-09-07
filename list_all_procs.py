# list_all_procs.py
import csv
import subprocess

res = subprocess.run(["tasklist", "/fo", "csv"], capture_output=True, text=True, errors="ignore")
reader = csv.reader(res.stdout.strip().splitlines())
header = next(reader, None)

procs = []
for row in reader:
    if len(row) >= 5:
        name = row[0]
        pid = row[1]
        session = row[2]
        mem = row[4]
        title = row[8] if len(row) > 8 else ""
        procs.append((pid, name, title, mem))

# Filtrar processos que rodam na sessao de usuario (Console)
print(f"Total de processos encontrados: {len(procs)}")
print("-" * 75)
for pid, name, title, mem in sorted(procs, key=lambda x: x[1].lower()):
    # Ignorar svchost / componentes do sistema
    if name.lower() not in ["svchost.exe", "system idle process", "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", "fontdrvhost.exe", "dwm.exe"]:
        print(f"PID: {pid:>5} | Nome: {name:<25} | Mem: {mem:<10} | Janela: {title}")
