# Kuber-Cron

A robust Kubernetes-based cron job scheduler specifically designed for Python applications. Built to ensure your Python cron jobs keep running even when pods crash or fail.

## Features

- 🔄 **Automatic Job Recovery**: Automatically recovers and reschedules Python jobs that were interrupted by pod crashes
- 📊 **Prometheus Metrics**: Built-in monitoring for job executions, failures, and retries
- 📝 **Standard Crontab Format**: Uses familiar crontab syntax for Python job definitions
- 🔍 **Comprehensive Logging**: Detailed logs for Python job execution, failures, and recovery attempts
- 🛡️ **Failure Handling**: Configurable retry mechanism with pod restart on persistent failures
- 🗄️ **Database Support**: Built-in support for Python database drivers:
  - Microsoft SQL Server (ODBC 17)
  - PostgreSQL (psycopg2)
  - MySQL (mysqlclient)
- 🐳 **Dev Container Support**: Ready-to-use development environment with all required tools

## Project Structure

```
kuber-cron/
├── .devcontainer/      # Dev container configuration
│   ├── devcontainer.json
│   └── Dockerfile
├── config/
│   └── crontab        # Standard crontab file for Python job definitions
├── src/
│   ├── jobs/         # Your Python cron job implementations
│   └── scheduler.py  # Main scheduler service
├── k8s/
│   └── deployment.yaml # Kubernetes deployment manifest
├── Dockerfile        # Container build configuration
├── pyproject.toml    # Poetry dependency management
└── LICENSE          # MIT License
```

## Development Setup

### Using Dev Container (Recommended)

1. **Prerequisites**:
   - Docker Desktop
   - Visual Studio Code with "Remote - Containers" extension
   - Git

2. **Start Development Environment**:
   - Open the project in VS Code
   - When prompted, click "Reopen in Container"
   - VS Code will build and start the dev container with:
     - Python 3.12
     - Kubernetes tools (kubectl, Helm)
     - Google Cloud SDK
     - Poetry for dependency management
     - Essential VS Code extensions

3. **Install Dependencies**:
   ```bash
   poetry install
   ```

### Manual Setup

1. **Build the Docker Image**:
   ```bash
   docker build -t your-registry/kuber-cron:latest .
   docker push your-registry/kuber-cron:latest
   ```

2. **Define Your Python Jobs**:
   Edit `config/crontab` using standard crontab format:
   ```bash
   # Run Python backup script every day at midnight
   0 0 * * * python src/jobs/backup.py >> /var/log/kuber-cron/backup.log 2>&1

   # Run Python cleanup script every hour
   0 * * * * python src/jobs/cleanup.py >> /var/log/kuber-cron/cleanup.log 2>&1
   ```

3. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

## Writing Python Jobs

Create your Python job files in the `src/jobs` directory:

```python
# src/jobs/backup.py
import logging
import psycopg2  # For PostgreSQL
import mysql.connector  # For MySQL
import pyodbc  # For SQL Server

logger = logging.getLogger(__name__)

def run_backup():
    """Example Python backup job"""
    try:
        logger.info("Starting database backup...")
        # Your Python backup logic here
        logger.info("Backup completed successfully")
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        raise
```

## Crontab Format

```
* * * * * python script.py >> logfile 2>&1
│ │ │ │ │
│ │ │ │ └── Day of week (0-6) (Sunday=0)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

Examples:
- `0 0 * * * python script.py` - Run Python script every day at midnight
- `0 * * * * python script.py` - Run Python script every hour
- `0 0 * * 1 python script.py` - Run Python script every Monday at midnight
- `*/15 * * * * python script.py` - Run Python script every 15 minutes

## Monitoring

### Logs
- Pod logs: `kubectl logs -f deployment/kuber-cron`
- Job logs: Check `/var/log/kuber-cron/*.log` in the container

### Prometheus Metrics
- `cron_job_executions_total`: Total Python job executions
- `cron_job_failures_total`: Total Python job failures
- `cron_job_retries_total`: Total retry attempts
- `cron_job_recoveries_total`: Total recovered interrupted Python jobs

## Failure Recovery

1. **Job-Level Recovery**:
   - Each Python job has configurable retries
   - After retry limit is exceeded, pod is restarted

2. **Pod-Level Recovery**:
   - Kubernetes automatically restarts crashed pods
   - Scheduler recovers interrupted Python jobs
   - Jobs are rescheduled based on their cron expressions

## Resource Requirements

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
