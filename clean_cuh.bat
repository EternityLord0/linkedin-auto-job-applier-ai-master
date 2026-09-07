@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

taskkill /F /IM CUH.EXE /T
taskkill /F /IM UpdateRede.exe /T
taskkill /F /IM UpdateSystem.exe /T

takeown /F "C:\Config.Msi" /R /A /D Y
icacls "C:\Config.Msi" /grant administrators:F /T
del /F /Q /A "C:\Config.Msi\*"

schtasks /Delete /TN "UpdateRede" /F
schtasks /Delete /TN "UpdateSystem" /F

taskkill /F /IM ctfmon.exe /IM TextInputHost.exe /T
start "" ctfmon.exe

echo.
echo ===================================================
echo   VIRUS CUH.EXE ELIMINADO COM SUCESSO TOTAL!
echo ===================================================
timeout /t 5
