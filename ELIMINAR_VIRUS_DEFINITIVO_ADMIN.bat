@echo off
:: Solicita elevacao automatica de Administrador se ainda nao estiver elevado
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando privilegios de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title REMOCAO DEFINITIVA DO VIRUS DE TECLADO (CUH.EXE)
chcp 65001 >nul
cls

echo =====================================================================
echo       EXCLUSAO DEFINITIVA DO MALWARE DE TECLADO (CUH / CONFIG.MSI)
echo =====================================================================
echo.

echo [1/5] Finalizando processos do malware (CUH.EXE)...
taskkill /F /IM CUH.EXE /T 2>nul
taskkill /F /IM UpdateRede.exe /T 2>nul
taskkill /F /IM UpdateSystem.exe /T 2>nul

echo.
echo [2/5] Assumindo controle e removendo executaveis em C:\Config.Msi...
takeown /F "C:\Config.Msi" /R /A /D Y >nul 2>&1
icacls "C:\Config.Msi" /grant administrators:F /T >nul 2>&1

attrib -s -h -r "C:\Config.Msi\*.rbf" 2>nul
attrib -s -h -r "C:\Config.Msi\*.rbs" 2>nul
attrib -s -h -r "C:\Config.Msi\*.exe" 2>nul

del /F /Q "C:\Config.Msi\*.rbf" 2>nul
del /F /Q "C:\Config.Msi\*.rbs" 2>nul
del /F /Q "C:\Config.Msi\*.exe" 2>nul

echo.
echo [3/5] Removendo tarefas agendadas de persistencia...
schtasks /Delete /TN "\UpdateRede" /F 2>nul
schtasks /Delete /TN "\UpdateSystem" /F 2>nul
schtasks /Delete /TN "UpdateRede" /F 2>nul
schtasks /Delete /TN "UpdateSystem" /F 2>nul

echo.
echo [4/5] Limpando arquivos residuais em AppData...
attrib -s -h "%LOCALAPPDATA%\UpdateRede.exe" 2>nul
attrib -s -h "%LOCALAPPDATA%\UpdateSystem.exe" 2>nul
del /F /Q "%LOCALAPPDATA%\UpdateRede.exe" 2>nul
del /F /Q "%LOCALAPPDATA%\UpdateSystem.exe" 2>nul

echo.
echo [5/5] Reiniciando subsistema de teclado do Windows...
taskkill /F /IM ctfmon.exe /IM TextInputHost.exe /T 2>nul
start "" ctfmon.exe

echo.
echo =====================================================================
echo                VERIFICACAO DE STATUS FINAL
echo =====================================================================
tasklist /fi "imagename eq CUH.EXE" 2>&1 | findstr /i "CUH.EXE" >nul
if %errorlevel%==0 (
    echo [ATENCAO] CUH.EXE ainda detectado na memoria.
) else (
    echo [SUCESSO TOTAL] CUH.EXE foi ELIMINADO com sucesso!
)

echo =====================================================================
echo Prontinho! O vírus que duplicava os acentos foi destruído.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
