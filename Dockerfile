# Use a slim Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by OpenCV and TensorFlow
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and install Python packages
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full application
COPY . .

# Expose port (used by Railway)
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
