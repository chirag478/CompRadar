# CompRadar - Lightweight Zero-Dependency Container
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Set default port
ENV PORT=5000

# Expose service port
EXPOSE 5000

# Start server
CMD ["python", "server.py"]
