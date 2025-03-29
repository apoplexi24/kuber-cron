FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Create state directory
RUN mkdir -p /var/run/kuber-cron

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY config/crontab /etc/crontab

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the scheduler
CMD ["poetry", "run", "python", "-m", "src.scheduler"] 