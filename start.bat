@echo off
echo ==============================================
echo Iniciando Traductor de PDF...
echo ==============================================
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo Instalando ambiente virtual y dependencias...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install pymupdf playwright pillow
    playwright install chromium
) else (
    call venv\Scripts\activate.bat
)

if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "temp" mkdir temp

echo.
echo Coloque sus archivos PDF en la carpeta "input".
echo Presione cualquier tecla para iniciar la traduccion...
pause >nul

python pdf_translator.py

echo.
echo Proceso finalizado. Los PDFs traducidos se encuentran en la carpeta "output".
pause
