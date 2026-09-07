@echo off
:: Solicita elevacao de administrador se nao tiver
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando privilegios de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title Remocao Definitiva de Tarefas Agendadas Maliciosas
chcp 65001 >nul
echo ===================================================
echo     REMOVENDO TAREFAS AGENDADAS (ADMIN)
echo ===================================================
echo.

schtasks /Delete /TN "\UpdateRede" /F 2>nul
if %errorlevel%==0 (
    echo [SUCESSO] Tarefa \UpdateRede deletada!
) else (
    echo [INFO] Tarefa \UpdateRede ja nao existe ou ja foi removida.
)

schtasks /Delete /TN "\UpdateSystem" /F 2>nul
if %errorlevel%==0 (
    echo [SUCESSO] Tarefa \UpdateSystem deletada!
) else (
    echo [INFO] Tarefa \UpdateSystem ja nao existe ou ja foi removida.
)

echo.
echo ===================================================
echo   LIMPEZA CONCLUIDA COM SUCESSO!
echo ===================================================
pause
