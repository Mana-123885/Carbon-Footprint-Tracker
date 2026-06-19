# Use the official Python slim image as a base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the backend requirements file first to leverage Docker cache
COPY backend/requirements.txt ./backend/

# Install dependencies, adding gunicorn for a production server
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

# Copy the rest of the application files (frontend and backend)
# .dockerignore will ensure we don't copy the local SQLite DB or venv
COPY . .

# Set working directory to backend so paths resolve correctly
WORKDIR /app/backend

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
