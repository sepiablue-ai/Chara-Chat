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
if not defined LM_STUDIO_PATH set "LM_STUDIO_PATH=C:\path\to\lms.exe"
if not defined COMFYUI_PATH set "COMFYUI_PATH=C:\path\to\ComfyUI"
if not defined TTS_PATH set "TTS_PATH=C:\path\to\Irodori-TTS"
if not defined COMFYUI_GPU_ID set "COMFYUI_GPU_ID=0"
if not defined TTS_GPU_ID set "TTS_GPU_ID=0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: --- 繝ｭ繧ｰ繝輔か繝ｫ繝菴懈・ + 繧ｿ繧､繝繧ｹ繧ｿ繝ｳ繝・---
set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f "tokens=1-6 delims=/: " %%a in ("%DATE% %TIME: =0%") do (
    set "TS=%%c%%a%%b_%%d%%e%%f"
)
set "LOGDIR=%~dp0logs\%TS%"
mkdir "%LOGDIR%"
echo Log directory: %LOGDIR%
echo.

:: --- [1] LM Studio: 繧ｵ繝ｼ繝舌・襍ｷ蜍・---
echo [1/4] LM Studio server starting (Background)...
start /b "" "%LM_STUDIO_PATH%" server start > "%LOGDIR%\lms_server_%TS%.log" 2>&1
ping -n 6 127.0.0.1 > nul

:: --- LM Studio: 繝｢繝・Ν繝ｭ繝ｼ繝・---
echo       Loading model
start /b /wait "" "%LM_STUDIO_PATH%" load google/gemma-4-12b-qat --gpu=max --context-length 4096 --parallel 1 > "%LOGDIR%\lms_load_%TS%.log" 2>&1
echo       http://localhost:1234
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

:: --- [4] 繧ｵ繝ｼ繝薙せ襍ｷ蜍募ｾ・■ (繝昴・繝育｢ｺ隱・ ---
echo Waiting for services to be ready...
call :wait_port 8188 ComfyUI 60
call :wait_port 7860 Irodori-TTS 60
echo.

:: --- [5] Chara-Chat Engine ---
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

:: --- 繝昴・繝亥ｾ・■繧ｵ繝悶Ν繝ｼ繝√Φ ---
:wait_port
set "_port=%1"
set "_name=%2"
set "_timeout=%3"
set /a "_count=0"
:wait_loop
powershell -NoProfile -Command "try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('127.0.0.1',%_port%); $t.Close(); exit 0 } catch { exit 1 }" > nul 2>&1
if %errorlevel%==0 (
    echo       [OK] %_name% port %_port% is ready.
    goto :eof
)
set /a "_count+=1"
if %_count% geq %_timeout% (
    echo       [Timeout] %_name% port %_port% did not respond in %_timeout%s.
    goto :eof
)
ping -n 2 127.0.0.1 > nul
goto wait_loop

