@echo off
rem Photograph the next 1000 buildings/props (the "Structures" category - it covers both
rem actual buildings and all the smaller static clutter), add them to the Object Finder,
rem and upload everything to GitHub so the website picks them up too - no extra step needed.
cd /d "%~dp0..\..\.."
python tools\object-search\studio\run_batch.py 1000 --only Structures --push
pause
