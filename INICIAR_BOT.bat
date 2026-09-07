@echo off
chcp 65001 >nul
title LinkedIn Auto Job Applier AI
cd /d "%~dp0"

echo ===================================================
echo        LINKEDIN AUTO JOB APPLIER AI
echo ===================================================
echo.
echo [1] Iniciar Bot de Candidaturas (main.py)
echo [2] Iniciar Dashboard Web (web_server.py)
echo [3] Iniciar Ambos (Bot + Dashboard)
echo [4] Publicar Post de IA no LinkedIn (publish_post.py)
echo [0] Sair
echo.
set /p opt="Escolha uma opcao [1-4] (Padrao: 1): "
if "%opt%"=="" set opt=1

if "%opt%"=="1" goto run_bot
if "%opt%"=="2" goto run_dashboard
if "%opt%"=="3" goto run_both
if "%opt%"=="4" goto run_post
if "%opt%"=="0" exit
goto run_bot

:run_bot
echo.
echo ---------------------------------------------------
echo Ativando ambiente virtual e iniciando Bot...
echo ---------------------------------------------------
call .venv\Scripts\activate
python main.py
goto end

:run_dashboard
echo.
echo ---------------------------------------------------
echo Iniciando Dashboard Web em http://127.0.0.1:5000...
echo ---------------------------------------------------
call .venv\Scripts\activate
start http://127.0.0.1:5000
python web_server.py
goto end

:run_both
echo.
echo ---------------------------------------------------
echo Abrindo Dashboard em nova janela e iniciando Bot...
echo ---------------------------------------------------
start "LinkedIn Dashboard Web" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate && start http://127.0.0.1:5000 && python web_server.py"
call .venv\Scripts\activate
python main.py
goto end

:run_post
echo.
echo ---------------------------------------------------
echo Iniciando Publicador de Posts no LinkedIn...
echo ---------------------------------------------------
call .venv\Scripts\activate
python publish_post.py
goto end

:end
echo.
echo Execucao finalizada. Pressione qualquer tecla para fechar...
pause >nul
