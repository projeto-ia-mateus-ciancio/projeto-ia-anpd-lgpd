@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
set "RODADAS=2"
set "GEMINI_MODEL=gemini-3.5-flash-lite"
if not exist "%PY%" (
  echo Rode primeiro o 1_instalar.bat.
  goto erro
)
"%PY%" src\baixar_pdfs.py || goto erro
"%PY%" src\extrair_texto.py || goto erro
"%PY%" src\extrair_llm.py || goto erro
"%PY%" src\validar.py || goto erro
echo.
echo Extracao concluida. NAO abra resultados\extracoes antes de terminar o gabarito.
pause
exit /b 0
:erro
echo.
echo A etapa parou. Leia a mensagem acima ou mande para o Claude.
pause
exit /b 1
