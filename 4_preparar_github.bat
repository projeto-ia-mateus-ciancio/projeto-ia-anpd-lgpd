@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist para_github rmdir /s /q para_github
robocopy . para_github /E /XD .venv para_github __pycache__ .ipynb_checkpoints pdfs textos tests /XF .env resultados_para_o_claude.zip 5_agendar_extracao.bat rodar_agendado.bat "=4.0" >nul
if errorlevel 8 goto erro
if exist para_github\.env goto erro
echo.
echo Pronto. Envie para o GitHub SOMENTE o conteudo da pasta para_github.
echo A pasta nao contem sua chave da API.
pause
exit /b 0
:erro
echo Algo deu errado. Nao envie nada para o GitHub e fale com o Claude.
pause
exit /b 1
