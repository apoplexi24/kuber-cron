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
RUN mkdir -p /var/run/kuber-cron

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Copy source code
COPY src/ src/

# Copy crontab configuration
COPY config/crontab /etc/crontab

# Install dependencies without creating a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Run the scheduler
CMD ["python", "src/scheduler.py"] 