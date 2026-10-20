@echo off
echo Searching for PLECS processes...

taskkill /F /IM PLECS.exe >nul 2>&1

if %errorlevel%==0 (
    echo All instances of PLECS.exe have been killed.
) else (
    echo No instances of PLECS.exe were found.
)

pause