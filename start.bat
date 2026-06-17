@echo off
chcp 65001 > nul
title Chara-Chat Launcher

echo ============================================
echo   Chara-Chat - Start
echo ============================================
echo.

:: --- Load .env ---
if exist "%~dp0.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0.env") do (
        set "%%A=%%B"
    )
)

:: --- Default values ---
if not defined OLLAMA_MODEL set "OLLAMA_MODEL=gemma4:12b-it-qat"
if not defined COMFYUI_PATH set "COMFYUI_PATH=C:\path\to\ComfyUI"
if not defined TTS_PATH set "TTS_PATH=C:\path\to\Irodori-TTS"
if not defined COMFYUI_GPU_ID set "COMFYUI_GPU_ID=0"
if not defined TTS_GPU_ID set "TTS_GPU_ID=0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: --- Log directory ---
set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f "tokens=1-6 delims=/: " %%a in ("%DATE% %TIME: =0%") do (
    set "TS=%%c%%a%%b_%%d%%e%%f"
)
set "LOGDIR=%~dp0logs\%TS%"
mkdir "%LOGDIR%"
echo Log directory: %LOGDIR%
echo.

:: --- [1] Ollama ---
echo [1/4] Checking Ollama...
where ollama > nul 2>&1
if errorlevel 1 (
    echo       [Error] ollama command was not found in PATH.
    echo       Install Ollama and make sure the model exists: %OLLAMA_MODEL%
    pause
    exit /b 1
)

call :wait_port 11434 Ollama 5
if errorlevel 1 (
    echo       Ollama is not responding. Starting ollama serve...
    start /b "" ollama serve > "%LOGDIR%\ollama_%TS%.log" 2>&1
    call :wait_port 11434 Ollama 30
)

echo       Verifying model: %OLLAMA_MODEL%
ollama show "%OLLAMA_MODEL%" > "%LOGDIR%\ollama_model_%TS%.log" 2>&1
if errorlevel 1 (
    echo       [Error] Ollama model not found: %OLLAMA_MODEL%
    echo       Run: ollama pull %OLLAMA_MODEL%
    pause
    exit /b 1
)
echo       http://localhost:11434
echo.

:: --- [2] ComfyUI ---
echo [2/4] ComfyUI Starting (Background) on GPU %COMFYUI_GPU_ID%...
set CUDA_VISIBLE_DEVICES=%COMFYUI_GPU_ID%
pushd "%COMFYUI_PATH%"
start /b "" .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --listen --fp8_e4m3fn-text-enc --disable-auto-launch > "%LOGDIR%\comfyui_%TS%.log" 2>&1
popd

:: --- [3] Irodori-TTS ---
echo [3/4] TTS Starting (Background) on GPU %TTS_GPU_ID%...
set CUDA_VISIBLE_DEVICES=%TTS_GPU_ID%
pushd "%TTS_PATH%"
start /b "" uv run python gradio_app.py --server-name 0.0.0.0 --server-port 7860 > "%LOGDIR%\tts_%TS%.log" 2>&1
popd

:: --- Wait for services ---
echo Waiting for services to be ready...
call :wait_port 8188 ComfyUI 60
call :wait_port 7860 Irodori-TTS 60
echo.

:: --- [4] Chara-Chat Engine ---
echo [4/4] Chara-Chat Engine (Gradio)...
cd /d "%~dp0"
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

echo.
echo ============================================
echo   Ready!
echo   Local:   http://localhost:8501
echo ============================================
echo.

"%~dp0venv\Scripts\python.exe" -u "%~dp0app.py" 2>&1 | powershell -NoProfile -Command "$input | Tee-Object -FilePath '%LOGDIR%\app_%TS%.log'"

pause

:: --- Wait port helper ---
:wait_port
set "_port=%1"
set "_name=%2"
set "_timeout=%3"
set /a "_count=0"
:wait_loop
powershell -NoProfile -Command "try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('127.0.0.1',%_port%); $t.Close(); exit 0 } catch { exit 1 }" > nul 2>&1
if %errorlevel%==0 (
    echo       [OK] %_name% port %_port% is ready.
    exit /b 0
)
set /a "_count+=1"
if %_count% geq %_timeout% (
    echo       [Timeout] %_name% port %_port% did not respond in %_timeout%s.
    exit /b 1
)
ping -n 2 127.0.0.1 > nul
goto wait_loop
