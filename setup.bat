@echo off

:: Create virtual environment in the current directory
python -m venv venv

:: Activate the virtual environment
call venv\Scripts\activate

:: Install dependencies from requirements.txt
pip install -r requirements.txt

:: Run the application
python src\main.py
