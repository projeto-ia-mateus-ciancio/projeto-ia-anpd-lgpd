@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
set "PROVEDOR=ollama"
set "OLLAMA_MODEL=qwen3:8b"
set "RODADAS=2"
if not exist "%PY%" (
  echo Rode primeiro o 1_instalar.bat.
  goto erro
)
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama nao encontrado. Instale em https://ollama.com/download e rode de novo.
  goto erro
)
echo [1/3] Baixando o modelo local (so na primeira vez, cerca de 5 GB)
ollama pull %OLLAMA_MODEL% || goto erro
echo [2/3] Conferindo PDFs e texto
"%PY%" src\baixar_pdfs.py || goto erro
"%PY%" src\extrair_texto.py || goto erro
echo [3/3] Extraindo com o modelo local
"%PY%" src\extrair_llm.py || goto erro
"%PY%" src\validar.py || goto erro
echo.
echo Extracao concluida. Agora rode o 3_avaliar.bat.
pause
exit /b 0
:erro
echo.
echo A etapa parou. Mande um print desta janela para o Claude.
pause
exit /b 1
