@echo off
rem Uploads the Object Finder (page, search data and pictures) to GitHub so Patch Atlas can use it.
rem Double-click it after a batch has finished.
setlocal
cd /d "%~dp0..\..\.."
where git >NUL 2>NUL || (echo Git is not installed on the command line. Commit and push from GitHub Desktop instead. & pause & exit /b 1)
git rev-parse --is-inside-work-tree >NUL 2>NUL || (echo "%CD%" is not a Git repository. & pause & exit /b 1)
echo Repository: %CD%
for /f "delims=" %%B in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%B"
echo Branch: %BRANCH%
git remote get-url origin
echo.
echo Adding the Object Finder files...
rem only the folders that exist yet (model-images-photo appears after Update_Object_Finder.bat)
for %%P in (tools\object-search assets\model-images-cutout assets\model-images-photo assets\model-images-pa) do if exist "%%P" git add -A -- "%%P"
git check-ignore -q tools/object-search/index.html && echo WARNING: tools/object-search is ignored by a .gitignore file, so it cannot be uploaded.
git check-ignore -q assets/model-images-cutout/x.webp && echo WARNING: assets/model-images-cutout is ignored by a .gitignore file, so it cannot be uploaded.
git diff --cached --quiet && echo No new changes to commit. || git commit -m "Object Finder: page, search data and studio pictures"
echo.
echo Getting any changes from GitHub first...
rem --autostash keeps your other unsaved edits in this repo safe while it updates
git pull --rebase --autostash origin %BRANCH% || (echo Could not merge with GitHub. Nothing was uploaded; send Claude a screenshot. & pause & exit /b 1)
echo.
echo Uploading...
git push origin %BRANCH% || (echo The upload failed. Send Claude a screenshot. & pause & exit /b 1)
echo.
git status -sb | findstr /b "##"
echo Done. Patch Atlas will show the Object Finder and new pictures within a few minutes.
pause
