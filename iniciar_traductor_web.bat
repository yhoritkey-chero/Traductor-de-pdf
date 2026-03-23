@echo off
echo ==============================================
echo Iniciando Traductor WEB (Streamlit)...
echo ==============================================
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo Instalando ambiente virtual y dependencias...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install pymupdf playwright pillow streamlit
    playwright install chromium
) else (
    call venv\Scripts\activate.bat
    pip install streamlit
)

echo Abriendo aplicacion en el navegador...
streamlit run streamlit_app.py
