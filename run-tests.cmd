@echo off
title Run SauceDemo UI Tests
cd /d "%~dp0"
echo ================================================
echo   Running UI tests against http://localhost:3000
echo   Extra args are passed through, e.g.:
echo       run-tests.cmd -m smoke
echo ================================================
echo.
".venv\Scripts\python.exe" -m pytest %*
echo.
echo Done. Report folder: reports\allure-html
echo Open it with: allure open reports\allure-html
if not "%NO_PAUSE%"=="1" pause
