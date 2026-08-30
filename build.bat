@echo off
setlocal
py -3 "%~dp0build.py"
if errorlevel 1 exit /b %errorlevel%
endlocal
