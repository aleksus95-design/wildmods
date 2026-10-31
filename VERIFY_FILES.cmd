@echo off
python "%~dp0verify_files.py" %*
set "MWVerifyResult=%errorlevel%"
pause
exit /b %MWVerifyResult%
