"""
Main scheduler service for kuber-cron
"""
import logging
import os
import signal
import sys
import time
from datetime import datetime
from crontab import CronTab
from prometheus_client import start_http_server, Counter, Gauge
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics
JOB_EXECUTIONS = Counter("cron_job_executions_total", "Total number of job executions")
JOB_FAILURES = Counter("cron_job_failures_total", "Total number of job failures")
JOB_RETRIES = Counter("cron_job_retries_total", "Total number of job retries")
JOB_RECOVERIES = Counter("cron_job_recoveries_total", "Total number of recovered jobs")
CPU_USAGE = Gauge("cron_cpu_usage_percent", "Current CPU usage percentage")

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}. Shutting down...")
    sys.exit(0)

def run_job(command):
    """Run a cron job and handle its output"""
    try:
        logger.info(f"Running job: {command}")
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Job completed successfully: {command}")
            JOB_EXECUTIONS.inc()
        else:
            logger.error(f"Job failed: {command}\nError: {stderr}")
            JOB_FAILURES.inc()
            
    except Exception as e:
        logger.error(f"Error running job {command}: {str(e)}")
        JOB_FAILURES.inc()

def should_run_job(job, now):
    """Check if a job should run at the given time"""
    try:
        # Parse the cron expression
        cron = CronTab(job.slices)
        
        # Check if the job matches the current time
        return cron.match(now)
    except Exception as e:
        logger.error(f"Error checking job schedule: {str(e)}")
        return False

def main():
    """Main scheduler function"""
    # Start Prometheus metrics server
    start_http_server(8000)
    logger.info("Started Prometheus metrics server on port 8000")
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load crontab
    crontab_path = "/etc/crontab"
    if not os.path.exists(crontab_path):
        logger.error(f"Crontab file not found at {crontab_path}")
        sys.exit(1)
        
    cron = CronTab(tabfile=crontab_path)
    logger.info(f"Loaded crontab from {crontab_path}")
    
    # Log crontab entries
    for job in cron:
        logger.info(f"Found cron job: {job}")
    
    # Main loop
    last_minute = -1
    while True:
        now = datetime.now()
        current_minute = now.minute
        
        # Only run jobs if we've moved to a new minute
        if current_minute != last_minute:
            logger.info(f"Checking jobs at minute {current_minute}")
            for job in cron:
                logger.info(f"Checking job: {job}")
                if job.is_enabled():
                    logger.info(f"Job is enabled: {job}")
                    if should_run_job(job, now):
                        logger.info(f"Job should run now: {job}")
                        run_job(job.command)
            last_minute = current_minute
        
        time.sleep(1)  # Check every second, but only run jobs on minute changes

if __name__ == "__main__":
    main() 