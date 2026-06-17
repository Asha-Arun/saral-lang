@echo off
REM ═══════════════════════════════════════════════════════
REM Saral Language Installer — Windows 10/11
REM Version 1.0.0 "First Public Release"
REM Run as Administrator for best results
REM ═══════════════════════════════════════════════════════

title Saral Installer v2.0.0
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   🌿  SARAL v2.0.0 Windows Installer         ║
echo  ║   Simple programming for everyone            ║
echo  ╚══════════════════════════════════════════════╝
echo.

SET SARAL_DIR=%USERPROFILE%\Saral
SET PYTHON_CMD=python

REM ── Step 1: Check Python ─────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo     Python not found.
    echo     Please install Python from https://python.org
    echo     Make sure to check "Add Python to PATH" during install.
    echo.
    echo     After installing Python, run this installer again.
    pause
    exit /b 1
) ELSE (
    FOR /F "tokens=2" %%V IN ('python --version 2^>^&1') DO (
        echo     Python %%V found.
    )
)

REM ── Step 2: Create Saral folder ──────────────────────
echo.
echo [2/6] Creating Saral folder at %SARAL_DIR%...
if not exist "%SARAL_DIR%" mkdir "%SARAL_DIR%"
if not exist "%SARAL_DIR%\examples" mkdir "%SARAL_DIR%\examples"
echo     Folder created.

REM ── Step 3: Copy Saral files ─────────────────────────
echo.
echo [3/6] Installing Saral files...

IF NOT EXIST "saral.py" (
    echo     ERROR: saral.py not found.
    echo     Run this installer from the Saral folder.
    pause
    exit /b 1
)

copy "saral.py"      "%SARAL_DIR%\" >nul
copy "pipeline.py"   "%SARAL_DIR%\" >nul
copy "lexer.py"      "%SARAL_DIR%\" >nul
copy "parser.py"     "%SARAL_DIR%\" >nul
copy "ast_nodes.py"  "%SARAL_DIR%\" >nul
copy "codegen.py"    "%SARAL_DIR%\" >nul
copy "analyzer.py"   "%SARAL_DIR%\" >nul
copy "sourcemap.py"  "%SARAL_DIR%\" >nul
copy "errors.py"     "%SARAL_DIR%\" >nul
copy "ai_helper.py"  "%SARAL_DIR%\" >nul
copy "ai_config.py"  "%SARAL_DIR%\" >nul
copy "memory.py"     "%SARAL_DIR%\" >nul
copy "debugger.py"   "%SARAL_DIR%\" >nul
copy "__init__.py"   "%SARAL_DIR%\" >nul

IF EXIST "example.saral" copy "example.saral" "%SARAL_DIR%\examples\" >nul
IF EXIST "test_v2.saral"  copy "test_v2.saral"  "%SARAL_DIR%\examples\" >nul

echo     Files installed.

REM ── Step 4: Create saral.bat launcher ────────────────
echo.
echo [4/6] Creating 'saral' command...

SET LAUNCHER=%SARAL_DIR%\saral.bat
(
echo @echo off
echo python "%SARAL_DIR%\saral.py" %%*
) > "%LAUNCHER%"

REM Add Saral to PATH for this user
setx PATH "%PATH%;%SARAL_DIR%" >nul 2>&1
echo     'saral' command created.
echo     You may need to restart your terminal for it to work.

REM ── Step 5: Install Ollama ────────────────────────────
echo.
echo [5/6] Ollama (local AI engine)...
echo     Ollama lets Saral run AI completely offline and free.
echo     Download from: https://ollama.ai/download
echo.
set /p OPEN_OLLAMA="    Open Ollama download page now? (y/n): "
if /i "%OPEN_OLLAMA%"=="y" (
    start https://ollama.ai/download
    echo     After installing Ollama, open a terminal and run:
    echo     ollama pull llama3.2
)

REM ── Step 6: Create desktop shortcut ──────────────────
echo.
echo [6/6] Creating desktop shortcut...

SET SHORTCUT_VBS=%TEMP%\create_shortcut.vbs
(
echo Set WshShell = WScript.CreateObject^("WScript.Shell"^)
echo Set Shortcut = WshShell.CreateShortcut^("%USERPROFILE%\Desktop\Saral Interactive.lnk"^)
echo Shortcut.TargetPath = "cmd.exe"
echo Shortcut.Arguments = "/k python ""%SARAL_DIR%\saral.py"" --interactive"
echo Shortcut.WorkingDirectory = "%SARAL_DIR%"
echo Shortcut.Description = "Saral Programming Language"
echo Shortcut.Save
) > "%SHORTCUT_VBS%"
cscript //nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"
echo     Desktop shortcut created.

REM ── Done ─────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   Saral installed successfully!              ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  How to use Saral:
echo.
echo  1. Open a new terminal (Command Prompt or PowerShell)
echo  2. Type these commands:
echo.
echo     saral myfile.saral          Run a program
echo     saral --interactive         Type code live
echo     saral --generate            AI writes code
echo     saral --check myfile.saral  Check for errors
echo     saral --explain myfile.saral Explain code
echo     saral --version             Version info
echo     saral --status              Check AI status
echo.
echo  Example programs are in: %SARAL_DIR%\examples\
echo.
echo  To use AI features:
echo    1. Install Ollama from https://ollama.ai
echo    2. Run: ollama pull llama3.2
echo    3. Run: ollama serve  (keep this running)
echo.
pause
