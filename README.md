# StreamPulse

StreamPulse is a dynamic news feed display application that fetches and displays live news from various RSS feeds, financial data, and other global stats in real-time. It is designed to be run locally, either using a Python virtual environment or in a Docker container for easier deployment and distribution.

## Features

- **Dynamic News Feed**: Fetch and display live news from multiple sources using RSS feeds.
- **Sentiment Analysis**: Leverage Ollama's local models for text analysis.
- **Stock Ticker**: Real-time stock price updates using financial APIs.
- **Global Stats**: Display global statistics such as CO2 emissions and US National Debt.
- **World Clock**: Show current time in multiple time zones.
- **Multithreaded Loading**: Feeds and stock data load simultaneously in the background, ensuring fast and efficient performance.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting up with Docker](#docker-setup)
3. [Setting up with Virtual Environment](#virtual-environment-setup)
4. [Running the Application](#running-the-application)
5. [Directory Structure](#directory-structure)
6. [Contributing](#contributing)

---

## Getting Started

StreamPulse can be run using Docker or a Python virtual environment. Choose one of the following methods depending on your environment.

### Prerequisites

- **Python 3.7+** (if not using Docker)
- **Docker** (if running in a container)
- **Ollama**: Ensure the Ollama instance is running locally on `http://localhost:11434`. For more information, visit [Ollama's official site](https://ollama.com/).

---

## Docker Setup

Running StreamPulse in a Docker container is the simplest way to get started. Docker will ensure all dependencies are automatically installed.

### Steps to Set Up:

1. **Build the Docker Image**:
   Open a terminal in the project root directory and run:
   ```bash
   docker build -t stream-pulse .
   ```

2. **Run the Docker Container**:
   After building the image, start the container with:
   ```bash
   docker run -it stream-pulse
   ```

Docker will automatically set up the environment, install dependencies, and start the application.

---

## Virtual Environment Setup

If you prefer to use a Python virtual environment, follow the instructions below.

### Linux/Mac Setup

1. **Run the Setup Script**:
   Open a terminal in the project root and execute:
   ```bash
   ./setup.sh
   ```

2. **Activate the Environment**:
   The script will set up a Python virtual environment and install dependencies. Afterward, the application will automatically run.

### Windows Setup

1. **Run the Setup Script**:
   In a command prompt or PowerShell window, run:
   ```cmd
   setup.bat
   ```

2. **Activate the Environment**:
   The script will create the virtual environment, install the dependencies, and start the application.

---

## Running the Application

Once the environment is set up using Docker or virtualenv, the application will start automatically. You can modify the RSS feeds and other settings in the `src/ui` directory.

For example, the application fetches data from multiple RSS sources and displays them in real-time using `tkinter`.

---

## Directory Structure

Here is an overview of the project directory structure:

```
StreamPulse/
├── Dockerfile                  # Docker configuration
├── setup.sh                    # Linux/Mac setup script
├── setup.bat                   # Windows setup script
├── requirements.txt            # Python dependencies
├── src/                        # Source code
│   ├── api/                    # API-related scripts (sentiment analysis, etc.)
│   ├── ui/                     # UI-related scripts
│   ├── utils/                  # Utility scripts, including threading
│   │   └── threading.py        # Threading utilities for running background tasks
│   ├── main.py                 # Main entry point for the application
│   └── tests/                  # Unit tests
└── README.md                   # Project documentation
```

---

## Contributing

Contributions are welcome! Feel free to submit issues, feature requests, or pull requests. Before contributing, ensure all changes are tested using `unittest`.

---

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.