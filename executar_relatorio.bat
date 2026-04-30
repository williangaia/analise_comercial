@echo off
set "BASE_DIR=D:\Analise_Comercial_Gustavo_Campos"

cd /d "%BASE_DIR%"

"C:\Program Files\Python313\python.exe" "%BASE_DIR%\main.py" >> "%BASE_DIR%\logs\app.log" 2>&1