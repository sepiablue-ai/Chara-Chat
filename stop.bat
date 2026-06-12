@echo off
chcp 65001 > nul
echo ============================================
echo   Stopping AI Services (Keep LMS Server)
echo ============================================

:: --- Load .env ---
if exist "%~dp0.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0.env") do (
        set "%%A=%%B"
    )
)

if not defined LM_STUDIO_PATH set "LM_STUDIO_PATH=C:\path\to\lms.exe"

:: --- [1] LM Studio: 繝｢繝・Ν繧｢繝ｳ繝ｭ繝ｼ繝峨・縺ｿ (VRAM隗｣謾ｾ) ---
echo [1/3] Unloading LM Studio model...
if exist "%LM_STUDIO_PATH%" (
    "%LM_STUDIO_PATH%" unload --all
    ping -n 4 127.0.0.1 > nul
) else (
    echo [Warning] LM Studio not found at %LM_STUDIO_PATH%
)

:: --- [2] ComfyUI ---
echo [2/3] Killing ComfyUI...
wmic process where "CommandLine like '%%ComfyUI%%main.py%%'" delete > nul 2>&1

:: --- [3] Irodori-TTS + app.py ---
echo [3/3] Killing TTS and app.py...
wmic process where "CommandLine like '%%gradio_app.py%%'" delete > nul 2>&1
wmic process where "CommandLine like '%%app.py%%'" delete > nul 2>&1
taskkill /f /im uv.exe > nul 2>&1

echo.
echo ============================================
echo   Done! LMS server still running.
echo   Check VRAM: nvidia-smi
echo ============================================
