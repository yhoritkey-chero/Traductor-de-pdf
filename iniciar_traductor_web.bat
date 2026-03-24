Hit:1 http://deb.debian.org/debian-security bullseye-security InRelease

Hit:2 http://deb.debian.org/debian trixie InRelease

Hit:3 http://deb.debian.org/debian trixie-updates InRelease

Hit:4 http://deb.debian.org/debian-security trixie-security InRelease

Hit:5 https://packages.microsoft.com/debian/11/prod bullseye InRelease

Reading package lists...[2026-03-23 17:44:01.429838] 

Reading package lists...[2026-03-23 17:44:02.183166] 

Building dependency tree...[2026-03-23 17:44:02.391525] 

Reading state information...[2026-03-23 17:44:02.391786] 

libxcb1 is already the newest version (1.17.0-2+b1).

libxcb1 set to manually installed.

libx11-6 is already the newest version (2:1.8.12-1).

libx11-6 set to manually installed.

Solving dependencies...[2026-03-23 17:44:02.693574] 

Some packages could not be installed. This may mean that you have

requested an impossible situation or if you are using the unstable

distribution that some required packages have not yet been created

or been moved out of Incoming.

The following information may help to resolve the situation:


The following packages have unmet dependencies:

 libcups2t64 : Breaks: libcups2 (< 2.4.10-3+deb13u2)

E: Unable to correct problems, you have held broken packages.

E: The following information from --solver 3.0 may provide additional context:

   Unable to satisfy dependencies. Reached two conflicting decisions:

   1. libcups2t64:amd64 is available in versions 2.4.10-3+deb13u2, 2.4.10-3+deb13u1

      but none of the choices are installable:

      - libcups2t64:amd64=2.4.10-3+deb13u2 is not selected for install because:

        1. libcups2:amd64=2.3.3op2-3+deb11u10 is selected for install

        2. libcups2t64:amd64=2.4.10-3+deb13u2 Breaks libcups2 (< 2.4.10-3+deb13u2)

      - libcups2t64:amd64=2.4.10-3+deb13u1 is not selected for install

   2. libcups2t64:amd64 is selected for install because:

      1. libgtk-3-0t64:amd64=3.24.49-3 is selected for install

      2. libgtk-3-0t64:amd64 Depends libcups2t64 (>= 1.7.0)

[17:44:02] ❗️ installer returned a non-zero exit code@echo off
echo ==============================================
echo Iniciando Traductor WEB (Streamlit)...
echo ==============================================
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo Instalando ambiente virtual y dependencias...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install pymupdf playwright pillow streamlit
    playwright install firefox
) else (
    call venv\Scripts\activate.bat
    pip install streamlit
)

echo Abriendo aplicacion en el navegador...
streamlit run streamlit_app.py
