FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY scripts/requirements.txt /scripts/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /scripts/requirements.txt

# Copy scripts
COPY scripts/ /scripts/

# Make scripts executable
RUN chmod +x /scripts/*.py

# Create non-root user
RUN useradd -m -u 1000 reviewer && \
    chown -R reviewer:reviewer /scripts && \
    chown -R reviewer:reviewer /app

USER reviewer

# Expose port for Cloud Run
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/scripts

# Support both modes: CI/CD job mode and web server mode
# Default to web server for Cloud Run, but can be overridden for CI/CD
CMD ["python", "/scripts/web_server.py"] 