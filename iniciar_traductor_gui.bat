@echo off
echo ==============================================
echo Iniciando Interfaz del Traductor de PDF...
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

echo Abriendo aplicacion...
python gui_app.py
