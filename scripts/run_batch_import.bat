@echo off
REM Run batch import for all exported Discord channel data

cd /d "%~dp0\.."

echo Starting Discord Historical Batch Import...
echo Output will be saved to: batch_import.log
echo.

REM Run and redirect output to log file
python scripts/batch_import_all.py 2>&1 | tee batch_import.log

echo.
echo Import complete! Check batch_import.log for details.
echo.
pause




