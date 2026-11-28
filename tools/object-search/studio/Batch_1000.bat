@echo off
rem Photograph the next 1000 buildings/props (the "Structures" category - it covers both
rem actual buildings and all the smaller static clutter) and add them to the Object Finder.
rem Add  --push  after 1000 below to also upload them to GitHub.
cd /d "%~dp0..\..\.."
python tools\object-search\studio\run_batch.py 1000 --only Structures
pause
