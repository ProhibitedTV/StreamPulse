# Stage 1: Build stage
FROM python:3.9-slim AS build

# Set the working directory
WORKDIR /app

# Install dependencies for building (if any required)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies early to utilize Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage (runtime environment)
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the installed packages from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the application code
COPY . .

# Create a non-root user
RUN useradd -m myuser && chown -R myuser /app
USER myuser

# Expose the application port (use environment variable for flexibility)
EXPOSE 8000

# Default environment variable for the port (can be overridden at runtime)
ENV PORT=8000

# Run the application
CMD ["python", "src/main.py"]
