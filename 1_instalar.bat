@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Pasta do projeto: %CD%
if not exist requirements.txt (
  echo ERRO: requirements.txt nao esta nesta pasta. Extraia o zip inteiro antes de rodar.
  goto fim_erro
)
set "PYCMD="
py --version >nul 2>nul && set "PYCMD=py"
if not defined PYCMD (
  python --version >nul 2>nul && set "PYCMD=python"
)
if not defined PYCMD (
  python3 --version >nul 2>nul && set "PYCMD=python3"
)
if not defined PYCMD (
  echo ERRO: nenhum comando do Python funcionou: py, python ou python3.
  goto fim_erro
)
echo Usando: %PYCMD%
%PYCMD% --version
if exist .venv rmdir /s /q .venv
echo.
echo [1/3] Criando ambiente .venv
%PYCMD% -m venv .venv
if errorlevel 1 (
  echo ERRO na etapa 1: o Python nao conseguiu criar o ambiente.
  goto fim_erro
)
if not exist ".venv\Scripts\python.exe" (
  echo ERRO na etapa 1: .venv\Scripts\python.exe nao foi criado.
  echo Conteudo da pasta .venv:
  dir /a .venv
  goto fim_erro
)
echo.
echo [2/3] Atualizando o pip
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo ERRO na etapa 2.
  goto fim_erro
)
echo.
echo [3/3] Instalando bibliotecas
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERRO na etapa 3.
  goto fim_erro
)
if not exist .env copy .env.exemplo .env
echo.
echo Instalacao concluida. Abra o arquivo .env no Bloco de Notas e cole sua chave.
pause
exit /b 0
:fim_erro
echo.
echo Copie tudo que apareceu nesta janela e mande para o Claude.
pause
exit /b 1
