# Getting Started with Kuber-Cron

This guide will help you set up and run Kuber-Cron in your Kubernetes environment.

## Prerequisites

- Docker Desktop
- Kubernetes cluster (local or remote)
- Python 3.9 or higher
- Poetry (Python package manager)

## Development Setup

### Using Dev Container (Recommended)

1. **Prerequisites**:
   - Visual Studio Code with "Remote - Containers" extension
   - Docker Desktop
   - Git

2. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
   cd kuber-cron
   ```

3. **Start Development Environment**:
   - Open the project in VS Code
   - When prompted, click "Reopen in Container"
   - VS Code will build and start the dev container with:
     - Python 3.12
     - Kubernetes tools (kubectl, Helm)
     - Poetry for dependency management
     - Essential VS Code extensions

4. **Install Dependencies**:
   ```bash
   poetry install
   ```

### Manual Setup

1. **Install Dependencies**:
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install project dependencies
   poetry install
   ```

2. **Build the Docker Image**:
   ```bash
   docker build -t kuber-cron:latest .
   ```

3. **Load the Image into Your Cluster**:
   ```bash
   # For Kind clusters
   kind load docker-image kuber-cron:latest
   
   # For other clusters, push to a registry
   docker tag kuber-cron:latest your-registry/kuber-cron:latest
   docker push your-registry/kuber-cron:latest
   ```

## Deployment

1. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. **Verify the Deployment**:
   ```bash
   kubectl get pods -l app=kuber-cron
   kubectl logs -f deployment/kuber-cron
   ```

## Configuration

### Crontab Format

The crontab configuration follows the standard crontab format:

```
* * * * * python script.py >> logfile 2>&1
│ │ │ │ │
│ │ │ │ └── Day of week (0-6) (Sunday=0)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

Example configurations:
```bash
# Run every minute
* * * * * python src/jobs/job.py >> /var/log/kuber-cron/job.log 2>&1

# Run every hour
0 * * * * python src/jobs/hourly.py >> /var/log/kuber-cron/hourly.log 2>&1

# Run at midnight
0 0 * * * python src/jobs/daily.py >> /var/log/kuber-cron/daily.log 2>&1
```

### Resource Limits

The default resource limits are:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

Adjust these values in `k8s/deployment.yaml` based on your workload requirements.

## Monitoring

The service exposes Prometheus metrics on port 8000:

- `cron_job_executions_total`: Total number of job executions
- `cron_job_failures_total`: Total number of job failures
- `cron_job_retries_total`: Total number of job retries
- `cron_job_recoveries_total`: Total number of recovered jobs
- `cron_cpu_usage_percent`: Current CPU usage percentage

Access metrics at: `http://pod-ip:8000/metrics`

## Logs

View logs using:
```bash
# Follow pod logs
kubectl logs -f deployment/kuber-cron

# View specific job logs
kubectl exec -it $(kubectl get pod -l app=kuber-cron -o jsonpath='{.items[0].metadata.name}') -- cat /var/log/kuber-cron/job.log
``` 