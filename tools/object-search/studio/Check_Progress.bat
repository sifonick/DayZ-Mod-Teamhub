@echo off
rem Show how many objects already have a studio picture and how many are left,
rem for the same categories Batch_1000.bat photographs (buildings/props).
cd /d "%~dp0..\..\.."
python tools\object-search\studio\check_progress.py --only Structures
pause
