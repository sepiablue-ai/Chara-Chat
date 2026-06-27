@echo off
setlocal

echo [MioTTS Setup] Starting MioTTS setup...

:: 1. Create third_party directory if not exists
if not exist "third_party" (
    mkdir third_party
)

:: 2. Clone MioTTS repository
if not exist "third_party\MioTTS" (
    echo [MioTTS Setup] Cloning MioTTS repository...
    git clone https://github.com/Aratako/MioTTS-Inference.git third_party\MioTTS
) else (
    echo [MioTTS Setup] MioTTS repository already exists.
)

cd third_party\MioTTS

:: 3. Check for uv and install dependencies
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [MioTTS Setup] "uv" command not found. Please install uv ^(https://docs.astral.sh/uv/^)
    exit /b 1
)

echo [MioTTS Setup] Syncing dependencies using uv...
call uv sync

:: 4. Generate preset
echo [MioTTS Setup] Generating preset for MioTTS...
set PRESET_NAME=04_calm_elegant
set PRESET_AUDIO=..\..\assets\audio\04_calm_elegant.wav

if exist "%PRESET_AUDIO%" (
    call uv run scripts\generate_preset.py --audio "%PRESET_AUDIO%" --preset-id "%PRESET_NAME%"
    if %errorlevel% equ 0 (
        echo [MioTTS Setup] Preset "%PRESET_NAME%" generated successfully.
    ) else (
        echo [MioTTS Setup] Failed to generate preset.
    )
) else (
    echo [MioTTS Setup] Reference audio not found at %PRESET_AUDIO%. Skipping preset generation.
)

cd ..\..
echo [MioTTS Setup] Done!
endlocal
