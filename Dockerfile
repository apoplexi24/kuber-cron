FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# Install database drivers and cron
RUN apt-get update && apt-get install -y \
    libpq-dev \
    default-libmysqlclient-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /var/run/kuber-cron && \
    mkdir -p /var/log/kuber-cron && \
    chmod 777 /var/log/kuber-cron

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Create source directories
RUN mkdir -p /app/src/jobs && \
    chmod 777 /app/src && \
    chmod 777 /app/src/jobs

# Copy source code
COPY src/ /app/src/

# Copy crontab configuration
COPY config/crontab /app/crontab

# Install dependencies without creating a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Ensure all Python scripts are executable and have correct permissions
RUN find /app/src -type f -name "*.py" -exec chmod 777 {} \; && \
    chown -R root:root /app/src

# Run the scheduler
CMD ["python", "src/scheduler.py"] 