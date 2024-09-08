# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project folder into the container at /app
COPY . /app

# Expose port (if required)
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
