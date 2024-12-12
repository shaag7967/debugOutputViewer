@echo off

set VIRTUALENV=.venv

if not exist "%VIRTUALENV%\Scripts\activate.bat" (
    python -m venv %VIRTUALENV%
)

if not exist "%VIRTUALENV%\Scripts\activate.bat" exit /B 1

call "%VIRTUALENV%\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py

exit /B 0
