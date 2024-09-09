#!/bin/bash

# Function to display error messages
error_exit() {
    echo "$1" 1>&2
    exit 1
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    error_exit "Python 3 is not installed. Please install Python 3 to continue."
fi

# Check if virtual environment exists, if not, create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || error_exit "Failed to create virtual environment."
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || error_exit "Failed to activate virtual environment."

# Upgrade pip, setuptools, and wheel
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel || error_exit "Failed to upgrade pip or install necessary tools."

# Install dependencies from requirements.txt
echo "Installing dependencies..."
pip install -r requirements.txt || error_exit "Failed to install dependencies."

# Run the application
echo "Starting the application..."
python src/main.py || error_exit "Failed to start the application."

# Done
echo "Setup complete."
