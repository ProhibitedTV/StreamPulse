# StreamPulse

**StreamPulse** is an easy-to-use news feed display that brings live news, stock prices, and global statistics right to your screen. Whether you're interested in the latest headlines, checking financial updates, or tracking world stats like CO2 emissions, StreamPulse keeps everything running in real-time.

## Key Features

- **Live News Updates**: Automatically pulls news from different sources and displays them in an organized layout.
- **Stock Price Tracker**: Provides real-time stock updates using reliable financial sources.
- **Sentiment Analysis**: Gives insights into the tone of each news story using local AI models.
- **World Stats**: Keeps track of global data, including important stats like CO2 emissions.
- **Easy Setup**: Can be run locally or using Docker for a smooth, quick setup.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up with Docker](#setting-up-with-docker)
3. [Using a Virtual Environment](#using-a-virtual-environment)
4. [Running the Application](#running-the-application)
5. [How StreamPulse Works](#how-streampulse-works)
6. [Folder Overview](#folder-overview)

---

## Getting Started

You can run StreamPulse in two simple ways:

1. **Using Docker**: A container that holds everything needed to run the program, no extra software required.
2. **Using Python**: Set up StreamPulse manually using Python on your system.

Both options are quick and easy, so choose the one that works best for you!

### What You’ll Need

- **Python 3.7 or higher** (if not using Docker)
- **Docker** (if using the container setup)
- **Ollama**: This is for the sentiment analysis. Be sure it’s running locally at [Ollama's official site](https://ollama.com/).

---

## Setting Up with Docker

Docker makes it super simple to run StreamPulse without worrying about setup details.

### Steps:

1. **Build the Docker Image**:
   Open your terminal (or command prompt), navigate to the project folder, and type:
   ```bash
   docker build -t stream-pulse .
   ```

2. **Run the Application**:
   Once the image is built, start the app by running:
   ```bash
   docker run -it stream-pulse
   ```

That’s it! Docker handles the setup, and you’ll see StreamPulse live in no time.

---

## Using a Virtual Environment

If you prefer to run StreamPulse on your system using Python, follow these steps.

### For Linux/Mac Users:

1. **Run the Setup Script**:
   Open a terminal in the project’s main folder and type:
   ```bash
   ./setup.sh
   ```

2. **Activate the Environment**:
   The script will handle everything, from setting up a Python environment to installing what’s needed.

### For Windows Users:

1. **Run the Setup Script**:
   In a command prompt window, run:
   ```cmd
   setup.bat
   ```

2. **Activate the Environment**:
   This will automatically set up everything, and the application will start.

---

## Running the Application

Once set up (either with Docker or Python), the app will automatically fetch news, stock prices, and other stats. You can customize which feeds you want by editing the settings found in the `src/ui` folder.

---

## How StreamPulse Works

- **News**: StreamPulse grabs stories from news feeds (RSS) and shows them in a simple layout.
- **Stock Prices**: Real-time updates of popular stocks such as Apple (AAPL) or Microsoft (MSFT).
- **Sentiment Analysis**: Using AI, it tells you if a story has a positive or negative tone.
- **World Data**: Global statistics like CO2 levels or national debt are shown and updated regularly.

---

## Folder Overview

Here’s a quick look at how StreamPulse is organized:

```
StreamPulse/
├── Dockerfile                  # Configuration for running in Docker
├── setup.sh                    # Setup script for Linux/Mac users
├── setup.bat                   # Setup script for Windows users
├── requirements.txt            # List of Python dependencies
├── src/                        # Where the code lives
│   ├── api/                    # Handles things like fetching news and stock prices
│   ├── ui/                     # Controls how everything looks on screen
│   ├── utils/                  # Extra code for background tasks
│   ├── main.py                 # The main script to start the app
│   └── tests/                  # Tests to make sure everything works
└── README.md                   # Documentation (this file!)
```

---

## Contributing

We’d love your help! Whether you have ideas for new features or find any bugs, feel free to contribute by creating an issue or submitting a pull request. No coding experience needed—just share your thoughts.

---

## License

StreamPulse is licensed under the MIT License, which means it’s free to use and modify.