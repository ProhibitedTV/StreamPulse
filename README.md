# StreamPulse

**StreamPulse** is a dynamic real-time news feed and data display application that brings live updates, stock prices, global statistics, and more to your screen. Designed for streamers, news enthusiasts, and finance trackers, it’s perfect for displaying on streams or using as a live dashboard. 

## Key Features

- **Live News Updates**: Automatically pulls news from a wide variety of sources and displays them in a modern, intuitive layout.
- **Stock Price Tracker**: Provides real-time stock updates with price changes using reliable financial sources.
- **Sentiment Analysis**: Uses AI models locally (via Ollama) to analyze the tone of each news story.
- **World Stats**: Keeps track of global data like CO2 emissions, U.S. national debt, and other vital statistics.
- **Enhanced Visuals**: Features like animated loading screens, transparent backgrounds, and smooth transitions make StreamPulse visually engaging.
- **Easy Setup**: Can be run locally or using Docker for a smooth, quick setup, with customizable feeds and layouts.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up with Docker](#setting-up-with-docker)
3. [Using a Virtual Environment](#using-a-virtual-environment)
4. [Running the Application](#running-the-application)
5. [How StreamPulse Works](#how-streampulse-works)
6. [Folder Overview](#folder-overview)
7. [Contributing](#contributing)
8. [License](#license)

---

## Getting Started

You can run StreamPulse in two easy ways:

1. **Using Docker**: A containerized solution for quickly getting up and running without manual setup.
2. **Using Python**: A more hands-on approach using Python, with setup options for virtual environments.

Both options are quick and simple, so choose the one that suits you best.

### What You’ll Need

- **Python 3.7 or higher** (if not using Docker)
- **Docker** (for containerized deployment)
- **Ollama**: Required for sentiment analysis. Make sure it's running locally. Check out [Ollama's official site](https://ollama.com/) for details.

---

## Setting Up with Docker

Docker makes it easy to run StreamPulse without needing to install any dependencies.

### Steps:

1. **Build the Docker Image**:
   Navigate to the project folder in your terminal (or command prompt) and run:
   ```bash
   docker build -t stream-pulse .
   ```

2. **Run the Application**:
   Start the containerized version of StreamPulse by running:
   ```bash
   docker run -it stream-pulse
   ```

---

## Using a Virtual Environment

For those who prefer running StreamPulse directly on their machine, follow these steps.

### For Linux/Mac Users:

1. **Run the Setup Script**:
   In the terminal, navigate to the project folder and run:
   ```bash
   ./setup.sh
   ```

2. **Activate the Environment**:
   The setup script will take care of creating the environment and installing dependencies.

### For Windows Users:

1. **Run the Setup Script**:
   Open a command prompt and run:
   ```cmd
   setup.bat
   ```

2. **Activate the Environment**:
   The setup script will handle everything, and the application will be ready to run.

---

## Running the Application

Once set up (either with Docker or Python), the application will automatically start fetching and displaying news, stock prices, and stats. To customize which feeds are displayed, simply edit the configuration files in the `src/ui` folder.

To start the app, just run:

```bash
python src/main.py
```

---

## How StreamPulse Works

- **News**: Automatically fetches stories from configured RSS feeds and presents them in real-time.
- **Stock Prices**: Continuously updates stock prices from popular sources, displaying them in an animated ticker.
- **Sentiment Analysis**: Uses AI to assess whether news stories are positive, negative, or neutral.
- **World Data**: Displays real-time global statistics, including CO2 levels and U.S. national debt, updated regularly.

StreamPulse also features an animated loading screen that makes the data fetching process more engaging while it prepares the main interface.

---

## Folder Overview

Here's an overview of the project structure:

```
StreamPulse/
├── Dockerfile                  # Configuration for Docker setup
├── setup.sh                    # Linux/Mac setup script
├── setup.bat                   # Windows setup script
├── requirements.txt            # List of Python dependencies
├── src/                        # Application code
│   ├── api/                    # Modules for fetching data (news, stock prices)
│   ├── ui/                     # User interface components and layout controls
│   ├── utils/                  # Utility functions for background tasks
│   ├── main.py                 # Main application script
│   └── tests/                  # Unit tests for core features
└── README.md                   # This documentation
```

---

## Contributing

We welcome contributions! Whether you have suggestions for new features, want to help fix bugs, or improve the design, feel free to contribute. You can start by opening an issue or submitting a pull request on GitHub.

---

## License

StreamPulse is open-source software, licensed under the MIT License. This means you are free to use, modify, and distribute it, as long as you retain the original license.