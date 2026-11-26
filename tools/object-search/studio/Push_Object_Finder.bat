@echo off
rem Uploads the Object Finder (page, search data and pictures) to GitHub so Patch Atlas can use it.
rem Double-click it after a batch has finished.
cd /d "%~dp0..\..\.."
where git >NUL 2>NUL || (echo Git is not installed on the command line. Commit and push from GitHub Desktop instead. & pause & exit /b 1)
echo Adding the Object Finder files...
git add tools/object-search assets/model-images-cutout assets/model-images-pa
git diff --cached --quiet && (echo Nothing new to upload. & pause & exit /b 0)
git commit -m "Object Finder: page, search data and studio pictures"
echo Getting any changes from GitHub first...
git pull --rebase || (echo Could not merge with GitHub. Nothing was uploaded; ask Claude to help. & pause & exit /b 1)
echo Uploading...
git push || (echo The upload failed. & pause & exit /b 1)
echo.
echo Done. Patch Atlas will show the new pictures within a few minutes.
pause
