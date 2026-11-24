@echo off
setlocal
echo Starting DayZ 4 m terrain exporter...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Export-HeightMaps.ps1" %*
set "result=%errorlevel%"
pause
exit /b %result%
