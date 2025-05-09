@echo off
echo Setting up environment for Blockchain Donation Application...

REM Try to find Python 3.10 in common installation paths
set PYTHON_CMD=

REM Check if any python in PATH is 3.10
python -c "import sys; sys.exit(0) if sys.version_info.major == 3 and sys.version_info.minor == 10 else sys.exit(1)" 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto PYTHON_FOUND
)

REM Check common installation paths
if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    goto PYTHON_FOUND
)

if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_CMD=C:\Program Files\Python310\python.exe
    goto PYTHON_FOUND
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe
    goto PYTHON_FOUND
)

REM If Python 3.10 wasn't found automatically, ask user for path
echo Python 3.10 was not found in PATH or standard locations.
echo Please enter the full path to python.exe for Python 3.10 (e.g., C:\Path\To\Python310\python.exe):
set /p PYTHON_PATH=

if exist "%PYTHON_PATH%" (
    set PYTHON_CMD=%PYTHON_PATH%
    goto PYTHON_FOUND
) else (
    echo The specified path does not exist.
    echo Please install Python 3.10 or provide a valid path.
    pause
    exit /b 1
)

:PYTHON_FOUND
echo Found Python 3.10: %PYTHON_CMD%

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

echo Setup complete! Run the application with:
echo call venv\Scripts\activate
echo python app.py
pause 