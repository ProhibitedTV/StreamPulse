@echo off

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in the PATH. Please install Python before proceeding.
    exit /b 1
)

:: Check if the virtual environment already exists
if not exist "venv\Scripts\activate" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

:: Activate the virtual environment
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

:: Upgrade pip and setup tools
echo Upgrading pip, setuptools, and wheel...
pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Failed to upgrade pip and setuptools.
    exit /b 1
)

:: Install dependencies from requirements.txt
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

:: Run the application
echo Starting the application...
python src\main.py
if errorlevel 1 (
    echo Failed to start the application.
    exit /b 1
)

pause
