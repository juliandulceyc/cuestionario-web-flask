@echo off
cd /d "c:\Users\USUARIO\Documents\Empresa"
echo Iniciando aplicacion de evaluacion de candidatos...
echo ========================================
call venv\Scripts\activate
python app.py
pause
