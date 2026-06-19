# Use the official Python slim image as a base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies, adding gunicorn for a production server
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application files
COPY . .

# Inform Docker that the container listens on the port specified by Cloud Run
# Cloud Run ignores EXPOSE, but keeping it dynamic helps documentation
EXPOSE 8080

# CRITICAL FIX: Gunicorn must bind to the $PORT variable provided by Cloud Run
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT main:app"]
