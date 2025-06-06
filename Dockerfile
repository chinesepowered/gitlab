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
    chown -R reviewer:reviewer /scripts

USER reviewer

# Set entrypoint
ENTRYPOINT ["python", "/scripts/ai_reviewer.py"] 