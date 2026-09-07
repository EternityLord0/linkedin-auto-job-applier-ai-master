# check_hooks_and_drivers.py
import subprocess
import csv

print("=== VERIFICANDO DRIVERS DE TECLADO E FILTROS NO REGISTRO ===")
# Checar UpperFilters e LowerFilters do teclado no Windows
cmd = 'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e96b-e325-11ce-bfc1-08002be10318}"'
try:
    print(subprocess.check_output(cmd, shell=True, text=True, errors="ignore"))
except Exception as e:
    print(e)

print("\n=== VERIFICANDO SERVICOS RELACIONADOS A TECLADO / INPUT ===")
cmd_svc = 'wmic service where "pathname like \'%keyboard%\' or name like \'%kbd%\'" get name,displayname,pathname /format:list'
try:
    print(subprocess.check_output(cmd_svc, shell=True, text=True, errors="ignore"))
except Exception as e:
    print(e)
