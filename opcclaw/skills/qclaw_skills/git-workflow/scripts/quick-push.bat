@echo off
REM Quick Push Script for Windows - Double-click to run
REM Usage: Edit the MESSAGE variable or pass as argument

setlocal

set "MESSAGE=%date:~0,4%-%date:~5,2%-%date:~8,2% %time:~0,8%"

echo === Git Quick Push ===
echo.

REM Check if in a git repo
git rev-parse --git-dir >nul 2>&1
if %errorlevel% neq 0 (
    echo Not in a Git repository!
    pause
    exit /b 1
)

REM Show status
echo Changes:
git status --short
echo.

REM Stage all
echo Staging all changes...
git add .
echo.

REM Commit with timestamp
echo Committing: %MESSAGE%
git commit -m "%MESSAGE%"
echo.

REM Push
echo Pushing to remote...
for /f "tokens=*" %%i in ('git branch --show-current') do set BRANCH=%%i
git push -u origin %BRANCH%
echo.

echo Done! Pushed to %BRANCH%
pause
