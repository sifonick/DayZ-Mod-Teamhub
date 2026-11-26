@echo off
rem Photograph the next 100 objects and add them to the Object Finder.
rem Add  --push  after 100 below to also upload them to GitHub.
cd /d "%~dp0..\..\.."
python tools\object-search\studio\run_batch.py 100
pause
