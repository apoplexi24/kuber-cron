# Kuber-Cron Technical Architecture

## Overview

Kuber-Cron is a Kubernetes-native cron job scheduler designed for Python applications. It provides robust job scheduling with automatic recovery, monitoring, and logging capabilities.

## Components

### 1. Scheduler Service (`src/scheduler.py`)

The core component that manages cron job execution:

- **Crontab Parser**: Uses `python-crontab` to parse and validate cron expressions
- **Job Executor**: Manages job execution using Python's `subprocess` module
- **Metrics Server**: Exposes Prometheus metrics on port 8000
- **Signal Handler**: Manages graceful shutdown on SIGTERM/SIGINT

```python
def main():
    # Start metrics server
    start_http_server(8000)
    
    # Load crontab
    cron = CronTab(tabfile="/etc/crontab")
    
    # Main scheduling loop
    while True:
        for job in cron:
            if job.is_enabled() and job.is_valid():
                schedule = job.schedule(now)
                if schedule.get_next():
                    run_job(job.command)
        time.sleep(60)
```

### 2. Kubernetes Deployment

The deployment configuration (`k8s/deployment.yaml`) defines:

- **Pod Specification**: Container image, resource limits, probes
- **Volume Mounts**: ConfigMap for crontab, emptyDir for logs
- **Environment Variables**: Namespace configuration
- **Resource Limits**: CPU and memory constraints

```yaml
spec:
  containers:
  - name: kuber-cron
    image: kuber-cron:latest
    resources:
      limits:
        cpu: "500m"
        memory: "512Mi"
    volumeMounts:
    - name: config-volume
      mountPath: /app/config
    - name: logs-volume
      mountPath: /var/log/kuber-cron
```

### 3. Monitoring System

Prometheus metrics exposed:

- Job execution counters
- Failure tracking
- Retry monitoring
- CPU usage metrics

```python
# Prometheus metrics
JOB_EXECUTIONS = Counter('cron_job_executions_total', 'Total number of job executions')
JOB_FAILURES = Counter('cron_job_failures_total', 'Total number of job failures')
JOB_RETRIES = Counter('cron_job_retries_total', 'Total number of job retries')
JOB_RECOVERIES = Counter('cron_job_recoveries_total', 'Total number of recovered jobs')
CPU_USAGE = Gauge('cron_cpu_usage_percent', 'Current CPU usage percentage')
```

## Job Execution Flow

1. **Job Loading**:
   - Read crontab configuration from ConfigMap
   - Parse and validate cron expressions
   - Initialize job schedules

2. **Scheduling**:
   - Check job schedules every minute
   - Calculate next execution time
   - Trigger jobs when scheduled

3. **Execution**:
   - Spawn job process using subprocess
   - Capture stdout/stderr
   - Write to job-specific log files
   - Update Prometheus metrics

4. **Error Handling**:
   - Log job failures
   - Increment failure counters
   - Handle process errors
   - Manage resource constraints

## Container Image

The Docker image (`Dockerfile`) is built with:

- Python 3.12 base image
- Database drivers (ODBC, PostgreSQL, MySQL)
- Poetry for dependency management
- Application code and configuration

```dockerfile
FROM python:3.12-slim
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2
# Install database drivers
RUN apt-get install -y \
    libpq-dev \
    default-libmysqlclient-dev
# Install Poetry and dependencies
RUN curl -sSL https://install.python-poetry.org | python3 -
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev
```

## Security Considerations

1. **Resource Isolation**:
   - Container runs with limited privileges
   - Resource quotas prevent DoS
   - Separate log volumes per job

2. **Error Handling**:
   - Failed jobs don't affect scheduler
   - Resource limits prevent cascading failures
   - Graceful shutdown handling

3. **Monitoring**:
   - Real-time metrics exposure
   - Job failure tracking
   - Resource usage monitoring

## Future Improvements

1. **Job Recovery**:
   - Implement job state persistence
   - Add retry policies per job
   - Support for job dependencies

2. **Scaling**:
   - Distributed job execution
   - Leader election for HA
   - Job queue management

3. **Monitoring**:
   - Enhanced metrics
   - Grafana dashboards
   - Alert management 