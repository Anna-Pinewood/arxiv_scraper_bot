# Use the official Python 3.10 image as the base
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the source code, config.yaml file, and requirements.txt to the working directory
COPY src/ ./src/
COPY config.yaml ./
COPY requirements.txt ./

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "src/main.py"]