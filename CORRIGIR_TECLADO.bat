@echo off
title Corrigir Teclado e Remover Acento Duplo
chcp 65001 >nul

:: Auto-elevacao de Administrador
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Solicitando permissao de Administrador...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

echo ========================================================
echo   CORRIGINDO TECLADO E REMOVENDO VIRUS DO ACENTO DUPLO
echo ========================================================
echo.

echo [1/4] Finalizando processos do malware (UpdateSystem / UpdateRede)...
taskkill /F /IM UpdateSystem.exe /T 2>nul
taskkill /F /IM UpdateRede.exe /T 2>nul
taskkill /F /IM iexpress.exe /T 2>nul

timeout /t 1 >nul

echo [2/4] Deletando executaveis maliciosos...
del /F /Q "C:\Users\usuario\AppData\Roaming\UpdateRede.exe" 2>nul
del /F /Q "C:\Users\usuario\AppData\Roaming\UpdateSystem.exe" 2>nul
rmdir /S /Q "C:\Users\usuario\AppData\Roaming\SetupFiles" 2>nul

echo [3/4] Removendo entradas de inicializacao do registro...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "System32" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DriverNetwork" /f 2>nul

echo [4/4] Reiniciando subsistema de teclado do Windows...
taskkill /F /IM ctfmon.exe /T 2>nul
taskkill /F /IM TextInputHost.exe /T 2>nul
start ctfmon.exe

echo.
echo ========================================================
echo   CONCLUIDO COM SUCESSO!
echo   O teclado foi restaurado e os acentos estao normais.
echo ========================================================
echo.
pause
