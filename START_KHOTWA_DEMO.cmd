@echo off
cd /d "%~dp0"
set "DEMO_PYTHON=outputs\final-env-20261124\Scripts\python.exe"
if not exist "%DEMO_PYTHON%" set "DEMO_PYTHON=.venv\Scripts\python.exe"
if not exist "%DEMO_PYTHON%" set "DEMO_PYTHON=python"
"%DEMO_PYTHON%" scripts\launch_demo.py
if errorlevel 1 pause
