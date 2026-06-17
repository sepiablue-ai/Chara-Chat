@echo off
chcp 65001 > nul
echo ============================================
echo   Stopping AI Services
echo ============================================

:: Ollama is normally a shared local service, so this script leaves it running.

:: --- [1] ComfyUI ---
echo [1/3] Killing ComfyUI...
wmic process where "CommandLine like '%%ComfyUI%%main.py%%'" delete > nul 2>&1

:: --- [2] Irodori-TTS + app.py ---
echo [2/3] Killing TTS and app.py...
wmic process where "CommandLine like '%%gradio_app.py%%'" delete > nul 2>&1
wmic process where "CommandLine like '%%app.py%%'" delete > nul 2>&1
taskkill /f /im uv.exe > nul 2>&1

:: --- [3] Done ---
echo [3/3] Done. Ollama is still running.
echo.
echo ============================================
echo   Done!
echo   Check VRAM: nvidia-smi
echo ============================================
