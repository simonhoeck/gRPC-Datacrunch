@echo off
title Die Bond Analyzer
color 0B
echo.
echo  ==========================================
echo   Die Bond Analyzer - Startup
echo  ==========================================
echo.

:: In den grpc-Ordner wechseln (relativ zur Batch-Datei)
cd /d "%~dp0grpc"

:: ── Python pruefen ──────────────────────────────────────────────────────────
echo  [1/3] Pruefe Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  FEHLER: Python nicht gefunden!
    echo  Bitte Python 3.10+ installieren: https://www.python.org/downloads/
    echo  "Add Python to PATH" bei der Installation aktivieren.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         %%v gefunden

:: ── Pakete installieren ─────────────────────────────────────────────────────
echo.
echo  [2/3] Pruefe Python-Pakete...
python -c "import flask, pymongo, dotenv" >nul 2>&1
if errorlevel 1 (
    echo         Pakete fehlen - installiere...
    pip install flask pymongo python-dotenv -q
    if errorlevel 1 (
        echo.
        echo  FEHLER: Paketinstallation fehlgeschlagen!
        echo  Bitte manuell ausfuehren: pip install flask pymongo python-dotenv
        echo.
        pause
        exit /b 1
    )
    echo         Pakete installiert.
) else (
    echo         Alle Pakete vorhanden.
)

:: ── .env pruefen ────────────────────────────────────────────────────────────
if not exist ".env" (
    echo.
    echo  WARNUNG: .env Datei nicht gefunden!
    echo  Kopiere .env.example nach .env und trage das MongoDB-Passwort ein.
    echo.
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  .env wurde aus .env.example erstellt - bitte Passwort pruefen.
        echo.
    )
)

:: ── Server starten ──────────────────────────────────────────────────────────
echo.
echo  [3/3] Starte Flask-Server...
echo.

:: Pruefen ob Port bereits belegt
netstat -an | findstr ":5001 " | findstr "LISTEN" >nul 2>&1
if not errorlevel 1 (
    echo  HINWEIS: Port 5001 ist bereits belegt.
    echo  Moegliche Ursache: Server laeuft bereits.
    echo.
    echo  Browser wird geoeffnet...
    timeout /t 1 /nobreak >nul
    start "" "http://localhost:5001"
    echo.
    echo  Druecke eine Taste zum Beenden...
    pause >nul
    exit /b 0
)

:: Browser nach 3 Sekunden oeffnen (im Hintergrund)
start "" cmd /c "timeout /t 3 /nobreak >nul && start \"\" \"http://localhost:5001\""

:: Server im Vordergrund starten (Fenster bleibt offen)
echo  ==========================================
echo   Server laeuft auf http://localhost:5001
echo   Dieses Fenster offen lassen!
echo   Beenden mit Strg+C
echo  ==========================================
echo.
python server.py

:: Wenn der Server beendet wird
echo.
echo  Server gestoppt.
pause
