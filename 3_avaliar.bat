@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Rode primeiro o 1_instalar.bat.
  goto erro
)
"%PY%" src\validar.py || goto erro
"%PY%" src\avaliar.py || goto erro
cd notebooks
"%PY%" -m jupyter nbconvert --to notebook --execute --inplace analise_exploratoria.ipynb || goto erro
cd ..
powershell -NoProfile -Command "Compress-Archive -Force -Path resultados,dados\dataset_final.csv,dados\gabarito\gabarito_manual.xlsx,notebooks\analise_exploratoria.ipynb -DestinationPath resultados_para_o_claude.zip" || goto erro
echo.
echo Pronto. Envie o arquivo resultados_para_o_claude.zip no chat.
pause
exit /b 0
:erro
echo.
echo A etapa parou. Leia a mensagem acima ou mande para o Claude.
pause
exit /b 1
