@echo off
chcp 65001 >nul
echo ---------------------------------------------------
echo Exterminando processos maliciosos...
echo ---------------------------------------------------
taskkill /F /IM UpdateRede.exe /IM UpdateSystem.exe /T 2>nul

echo ---------------------------------------------------
echo Removendo tarefas agendadas de persistencia...
echo ---------------------------------------------------
schtasks /Delete /TN "UpdateRede" /F 2>nul
schtasks /Delete /TN "UpdateSystem" /F 2>nul

echo ---------------------------------------------------
echo Excluindo arquivos executaveis ocultos...
echo ---------------------------------------------------
attrib -s -h "%LOCALAPPDATA%\UpdateRede.exe" 2>nul
del /F /Q "%LOCALAPPDATA%\UpdateRede.exe" 2>nul

attrib -s -h "%LOCALAPPDATA%\UpdateSystem.exe" 2>nul
del /F /Q "%LOCALAPPDATA%\UpdateSystem.exe" 2>nul

echo ---------------------------------------------------
echo Limpando chaves do Registro (Run)...
echo ---------------------------------------------------
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "UpdateRede" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "UpdateSystem" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DriverNetwork" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "System32" /f 2>nul

echo ---------------------------------------------------
echo Reiniciando servico de teclado do Windows...
echo ---------------------------------------------------
taskkill /F /IM ctfmon.exe /IM TextInputHost.exe /T 2>nul
start "" ctfmon.exe

echo ---------------------------------------------------
echo Verificacao de status final:
echo ---------------------------------------------------
if exist "%LOCALAPPDATA%\UpdateRede.exe" (
    echo [ALERTA] UpdateRede.exe ainda existe!
) else (
    echo [SUCESSO] UpdateRede.exe foi DELETADO!
)

if exist "%LOCALAPPDATA%\UpdateSystem.exe" (
    echo [ALERTA] UpdateSystem.exe ainda existe!
) else (
    echo [SUCESSO] UpdateSystem.exe foi DELETADO!
)

schtasks /Query /TN "UpdateRede" 2>&1 | findstr /i "UpdateRede" >nul
if %errorlevel%==0 (
    echo [ALERTA] Tarefa UpdateRede ainda existe!
) else (
    echo [SUCESSO] Tarefa agendada UpdateRede foi ELIMINADA!
)

schtasks /Query /TN "UpdateSystem" 2>&1 | findstr /i "UpdateSystem" >nul
if %errorlevel%==0 (
    echo [ALERTA] Tarefa UpdateSystem ainda existe!
) else (
    echo [SUCESSO] Tarefa agendada UpdateSystem foi ELIMINADA!
)

echo ---------------------------------------------------
echo CONCLUIDO!
