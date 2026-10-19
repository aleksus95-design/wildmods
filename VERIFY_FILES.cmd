@echo off
python "%~dp0verify_files.py" %*
exit /b %errorlevel%
