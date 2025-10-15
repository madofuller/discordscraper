@echo off
REM Run batch historical export for all Discord channels

cd /d "%~dp0\.."

echo Starting Discord Historical Batch Export...
echo Output will be saved to: batch_export.log
echo.

REM Run in background and redirect output to log file
start "Discord Batch Export" /MIN python scripts/batch_historical_export.py > batch_export.log 2>&1

echo.
echo Export started in background!
echo To check progress: type batch_export.log
echo.
pause




