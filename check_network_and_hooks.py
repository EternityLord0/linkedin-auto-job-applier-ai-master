# check_network_and_hooks.py
import subprocess
import csv
import re

print("=== CONEXOES DE REDE ESTABELECIDAS (ESTABLISHED) ===")
netstat_out = subprocess.check_output("netstat -ano", shell=True, text=True, errors="ignore")
established = []
for line in netstat_out.splitlines():
    if "ESTABLISHED" in line:
        parts = re.split(r'\s+', line.strip())
        if len(parts) >= 5:
            proto, local, remote, state, pid = parts[0], parts[1], parts[2], parts[3], parts[4]
            established.append((pid, proto, local, remote))

# Pegar nomes de processos
tasklist_out = subprocess.check_output("tasklist /fo csv", shell=True, text=True, errors="ignore")
pid_to_name = {}
for row in csv.reader(tasklist_out.strip().splitlines()):
    if len(row) >= 2 and row[1].isdigit():
        pid_to_name[row[1]] = row[0]

for pid, proto, local, remote in established:
    name = pid_to_name.get(pid, "Desconhecido")
    # Ignorar processos comuns de desenvolvimento e navegadores conhecidos
    print(f"PID: {pid:>6} | Processo: {name:<25} | Local: {local:<22} | Remoto: {remote}")
