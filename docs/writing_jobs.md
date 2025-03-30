# Writing Jobs for Kuber-Cron

This guide explains how to write and configure Python jobs for Kuber-Cron.

## Job Structure

Jobs in Kuber-Cron are Python scripts that follow a simple structure:

```python
"""
Example job template
"""
import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_job() -> Any:
    """Main job function"""
    try:
        logger.info("Starting job...")
        # Your job logic here
        logger.info("Job completed successfully")
        return True
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_job()
```

## Example Jobs

### 1. CPU Stress Test Job

```python
"""
CPU stress test job to verify pod recovery functionality
"""
import logging
import multiprocessing
import time
from typing import Any

logger = logging.getLogger(__name__)

def cpu_intensive_task():
    """Simulate CPU-intensive work"""
    while True:
        # Perform CPU-intensive calculations
        _ = [i * i for i in range(10000)]
        time.sleep(0.1)  # Small delay to prevent complete CPU lock

def run_job() -> Any:
    """CPU stress test function"""
    try:
        logger.info("Starting CPU stress test...")
        
        # Start multiple CPU-intensive processes
        num_processes = multiprocessing.cpu_count() * 2
        processes = []
        
        for _ in range(num_processes):
            p = multiprocessing.Process(target=cpu_intensive_task)
            p.start()
            processes.append(p)
        
        # Let it run for 30 seconds
        time.sleep(30)
        
        # Cleanup processes
        for p in processes:
            p.terminate()
            p.join()
        
        logger.info("CPU stress test completed successfully")
        return True
    except Exception as e:
        logger.error(f"CPU stress test failed: {str(e)}")
        raise
```

### 2. Database Backup Job

```python
"""
Example database backup job
"""
import logging
import os
from typing import Any
import psycopg2

logger = logging.getLogger(__name__)

def run_job() -> Any:
    """Database backup function"""
    try:
        logger.info("Starting database backup...")
        
        # Database connection parameters
        db_params = {
            'dbname': os.environ.get('DB_NAME'),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'host': os.environ.get('DB_HOST'),
            'port': os.environ.get('DB_PORT', 5432)
        }
        
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Perform backup
        backup_file = f"/backups/db_{time.strftime('%Y%m%d_%H%M%S')}.sql"
        with open(backup_file, 'w') as f:
            cursor.copy_expert(f"COPY (SELECT * FROM your_table) TO STDOUT", f)
        
        logger.info(f"Backup completed successfully: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        raise
```

## Best Practices

1. **Logging**:
   - Use Python's logging module
   - Include timestamps in log messages
   - Log both successes and failures
   - Use appropriate log levels (INFO, ERROR, etc.)

2. **Error Handling**:
   - Use try-except blocks
   - Log detailed error messages
   - Clean up resources in finally blocks
   - Raise exceptions for critical failures

3. **Resource Management**:
   - Close database connections
   - Clean up temporary files
   - Release system resources
   - Use context managers (with statements)

4. **Configuration**:
   - Use environment variables
   - Don't hardcode credentials
   - Make paths configurable
   - Use configuration files when needed

5. **Performance**:
   - Monitor memory usage
   - Avoid infinite loops
   - Add timeouts to operations
   - Clean up background processes

## Job Configuration

Add your job to the crontab configuration in `k8s/deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kuber-cron-config
data:
  crontab: |
    # Run every minute
    * * * * * python src/jobs/your_job.py >> /var/log/kuber-cron/your_job.log 2>&1
```

## Environment Variables

Add required environment variables to the deployment:

```yaml
spec:
  containers:
  - name: kuber-cron
    env:
    - name: DB_HOST
      value: "your-db-host"
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
```

## Monitoring

Jobs can update Prometheus metrics:

```python
from prometheus_client import Counter, Gauge

# Define metrics
BACKUP_SIZE = Gauge('backup_size_bytes', 'Size of the backup in bytes')
BACKUP_DURATION = Gauge('backup_duration_seconds', 'Time taken for backup')

def run_job():
    start_time = time.time()
    try:
        # Your job logic
        backup_size = os.path.getsize(backup_file)
        BACKUP_SIZE.set(backup_size)
        BACKUP_DURATION.set(time.time() - start_time)
    except Exception:
        raise
```

## Testing Jobs

1. **Local Testing**:
   ```bash
   # Run job directly
   python src/jobs/your_job.py
   
   # Check logs
   cat /var/log/kuber-cron/your_job.log
   ```

2. **In Kubernetes**:
   ```bash
   # Execute job in pod
   kubectl exec -it deployment/kuber-cron -- python src/jobs/your_job.py
   
   # Check metrics
   kubectl port-forward deployment/kuber-cron 8000:8000
   curl localhost:8000/metrics
   ``` 