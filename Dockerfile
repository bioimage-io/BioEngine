# Use an official slim Python 3.11 image
FROM --platform=linux/amd64 python:3.11.9-slim AS build


# Set the working directory
WORKDIR /app/

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo privileges
RUN groupadd -r bioengine && useradd -r -g bioengine --create-home bioengine \
    && usermod -aG sudo bioengine \
    && echo "bioengine ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/bioengine

# Copy requirements first for efficient layer caching
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies with --no-cache-dir to reduce image size
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application files last to leverage Docker's build cache
COPY . /app/

# Change ownership to the non-root user and ensure scripts are executable
RUN chown -R bioengine:bioengine /app/

# Switch to the non-root user
USER bioengine

# Default entrypoint for running the application
ENTRYPOINT ["python", "/app/start_hypha_service.py"]