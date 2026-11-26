@echo off
rem Remakes the Object Finder pictures, catalogue and map files from the studio pictures you already have,
rem then uploads them to GitHub. Does not start the game.
cd /d "%~dp0..\..\.."
python tools\object-search\studio\run_batch.py --no-photos --push
pause
