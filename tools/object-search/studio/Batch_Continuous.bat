@echo off
rem Photographs buildings, rocks and vehicles (no trees, bushes or plants) in batches of 200,
rem one batch after another until everything is done. After each batch the pictures go into
rem the Object Finder and are uploaded to GitHub, so Patch Atlas fills up as it runs.
rem
rem To stop: create a file called STOP.txt in this folder. The run finishes the batch it is on,
rem uploads it, and stops. (Closing this window stops at once; the batch in progress is lost.)
rem Leave the PC alone while it runs: anything covering the DayZ window ends up in the pictures.
setlocal
set "HERE=%~dp0"
cd /d "%~dp0..\..\.."
if exist "%HERE%STOP.txt" del "%HERE%STOP.txt"
set BATCH=0
set FAILS=0
:loop
if exist "%HERE%STOP.txt" goto stopped
set /a BATCH+=1
echo.
echo ==================== Batch %BATCH% (%DATE% %TIME:~0,5%) ====================
python tools\object-search\studio\run_batch.py 200 --only Structures,Rocks,Vehicles --push
if errorlevel 10 goto done
if errorlevel 1 goto failed
set FAILS=0
goto loop
:failed
set /a FAILS+=1
if %FAILS% GEQ 3 goto gaveup
echo The batch stopped with an error. Trying again in 30 seconds...
timeout /t 30 /nobreak >NUL
goto loop
:done
echo.
echo All buildings, rocks and vehicles have been photographed. Finished after %BATCH% batches.
goto end
:stopped
del "%HERE%STOP.txt"
echo.
echo Stopped because STOP.txt was found. Run this again to carry on where it left off.
goto end
:gaveup
echo.
echo Three batches in a row stopped with an error, so the run has stopped. Send Claude a screenshot.
:end
pause
