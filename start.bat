@echo off
REM ===================================================================
REM  JK Classes Barnagar - start the website
REM  Just double-click this file.
REM ===================================================================

title JK Classes Barnagar - Website

echo.
echo   Starting the JK Classes website...
echo.

cd /d "%~dp0"

REM Install the two required packages the first time this is run.
python -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo.
echo   ================================================================
echo     Website      :  http://127.0.0.1:5000
echo     Admin panel  :  http://127.0.0.1:5000/admin/login
echo.
echo     Keep this black window open while using the website.
echo     Close it to stop the website.
echo   ================================================================
echo.

start "" http://127.0.0.1:5000
python app.py

pause
