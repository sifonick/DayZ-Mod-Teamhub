@echo off
rem Photograph the next 1000 objects and add them to the Object Finder.
rem Add  --push  after 1000 below to also upload them to GitHub.
cd /d "%~dp0..\..\.."
python tools\object-search\studio\run_batch.py 1000
pause
