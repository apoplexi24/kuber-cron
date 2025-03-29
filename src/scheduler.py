import logging
import os
import signal
import sys
import importlib
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from kubernetes import client, config
from prometheus_client import Counter, start_http_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
JOB_EXECUTION_COUNTER = Counter('cron_job_executions_total', 'Total number of cron job executions')
JOB_FAILURE_COUNTER = Counter('cron_job_failures_total', 'Total number of cron job failures')
JOB_RETRY_COUNTER = Counter('cron_job_retries_total', 'Total number of cron job retries')
JOB_RECOVERY_COUNTER = Counter('cron_job_recoveries_total', 'Total number of recovered interrupted jobs')

class KubernetesCronScheduler:
    def __init__(self, namespace: str = "default"):
        self.scheduler = BackgroundScheduler()
        self.jobs: Dict[str, dict] = {}
        self.job_retries: Dict[str, int] = {}  # Track retries per job
        self.running_jobs: Dict[str, dict] = {}  # Track currently running jobs
        self.namespace = namespace
        self.state_file = "/var/run/kuber-cron/state.json"
        
        # Load Kubernetes configuration
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        self.k8s_client = client.CoreV1Api()
        self.pod_name = os.environ.get('HOSTNAME', 'unknown')
        
        # Create state directory
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        # Load previous state if exists
        self._load_state()
        
    def _load_state(self) -> None:
        """Load previous job state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.running_jobs = state.get('running_jobs', {})
                    logger.info(f"Loaded {len(self.running_jobs)} interrupted jobs from state")
        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
    
    def _save_state(self) -> None:
        """Save current job state to file."""
        try:
            state = {
                'running_jobs': self.running_jobs,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
    
    def load_jobs_from_crontab(self, crontab_path: str) -> None:
        """Load cron jobs from a crontab file."""
        with open(crontab_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            # Parse the crontab line
            schedule, command, log_file = self._parse_crontab_line(line)
            if schedule and command:
                job_name = self._get_job_name(command)
                self.add_job(job_name, {
                    'schedule': schedule,
                    'command': command,
                    'log_file': log_file,
                    'retries': 3  # Default retries
                })
        
        # Recover interrupted jobs
        self._recover_interrupted_jobs()
    
    def _parse_crontab_line(self, line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse a crontab line into schedule, command, and log file."""
        try:
            # Split the line into parts
            parts = line.split()
            
            # First 5 parts are the schedule
            if len(parts) < 6:
                logger.warning(f"Invalid crontab line: {line}")
                return None, None, None
                
            schedule = ' '.join(parts[:5])
            
            # Find the log redirection if it exists
            log_file = None
            command_parts = []
            
            for i, part in enumerate(parts[5:], 5):
                if part == '>>':
                    # Found log redirection
                    if i + 1 < len(parts):
                        log_file = parts[i + 1]
                        break
                elif part == '2>&1':
                    # Found stderr redirection
                    continue
                else:
                    command_parts.append(part)
            
            command = ' '.join(command_parts)
            
            return schedule, command, log_file
            
        except Exception as e:
            logger.error(f"Failed to parse crontab line: {line}, error: {str(e)}")
            return None, None, None
    
    def _get_job_name(self, command: str) -> str:
        """Generate a job name from the command."""
        # Extract the file path from the command
        # Example: python src/jobs/backup.py -> backup
        try:
            file_path = command.split()[-1]
            return os.path.splitext(os.path.basename(file_path))[0]
        except:
            return command.replace(' ', '_')[:50]  # Fallback to truncated command
    
    def _recover_interrupted_jobs(self) -> None:
        """Recover jobs that were running when the pod crashed."""
        for job_name, job_info in self.running_jobs.items():
            if job_name in self.jobs:
                logger.info(f"Recovering interrupted job: {job_name}")
                # Schedule the job to run immediately
                self.scheduler.add_job(
                    self._execute_job,
                    'date',
                    id=f"recovery_{job_name}",
                    args=[job_name],
                    replace_existing=True
                )
                JOB_RECOVERY_COUNTER.inc()
        
        # Clear the running jobs after recovery
        self.running_jobs = {}
        self._save_state()
    
    def add_job(self, job_name: str, job_config: dict) -> None:
        """Add a new cron job to the scheduler."""
        if job_name in self.jobs:
            logger.warning(f"Job {job_name} already exists. Updating...")
            self.scheduler.remove_job(job_name)
            
        self.jobs[job_name] = job_config
        self.job_retries[job_name] = 0  # Initialize retry counter
        self.scheduler.add_job(
            self._execute_job,
            CronTrigger.from_crontab(job_config['schedule']),
            id=job_name,
            args=[job_name],
            replace_existing=True
        )
        logger.info(f"Added job: {job_name}")
    
    def _execute_job(self, job_name: str) -> None:
        """Execute a cron job and handle failures."""
        job_config = self.jobs[job_name]
        try:
            logger.info(f"Executing job: {job_name}")
            
            # Mark job as running
            self.running_jobs[job_name] = {
                'start_time': datetime.now().isoformat(),
                'command': job_config['command']
            }
            self._save_state()
            
            # Prepare the command
            command = job_config['command']
            log_file = job_config.get('log_file')
            
            # Create log directory if it doesn't exist
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Prepare the process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE if not log_file else open(log_file, 'a'),
                stderr=subprocess.STDOUT if not log_file else open(log_file, 'a'),
                text=True
            )
            
            # Add timestamp to log if logging to file
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(f"\n=== Job started at {datetime.now()} ===\n")
            
            # Wait for the process to complete
            process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Job {job_name} executed successfully")
                if log_file:
                    with open(log_file, 'a') as f:
                        f.write(f"=== Job completed successfully at {datetime.now()} ===\n")
                JOB_EXECUTION_COUNTER.inc()
                self.job_retries[job_name] = 0
            else:
                raise Exception(f"Command failed with return code {process.returncode}")
            
        except Exception as e:
            logger.error(f"Job {job_name} failed: {str(e)}")
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(f"=== Job failed at {datetime.now()}: {str(e)} ===\n")
            JOB_FAILURE_COUNTER.inc()
            
            # Increment retry counter
            self.job_retries[job_name] += 1
            JOB_RETRY_COUNTER.inc()
            
            # Check if we've exceeded retry limit
            if self.job_retries[job_name] >= job_config.get('retries', 3):
                logger.error(f"Job {job_name} has exceeded retry limit. Restarting pod...")
                self._handle_job_failure(job_name)
            else:
                logger.info(f"Job {job_name} will be retried. Attempt {self.job_retries[job_name]} of {job_config.get('retries', 3)}")
        
        finally:
            # Remove job from running jobs
            if job_name in self.running_jobs:
                del self.running_jobs[job_name]
                self._save_state()
    
    def _handle_job_failure(self, job_name: str) -> None:
        """Handle job failures by potentially restarting the pod."""
        try:
            # Get the current pod
            pod = self.k8s_client.read_namespaced_pod(
                name=self.pod_name,
                namespace=self.namespace
            )
            
            # Delete the pod to trigger a restart
            self.k8s_client.delete_namespaced_pod(
                name=self.pod_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions()
            )
            
            logger.info(f"Pod {self.pod_name} deleted to handle job failure: {job_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle job failure: {str(e)}")
    
    def start(self) -> None:
        """Start the scheduler and health check server."""
        # Start Prometheus metrics server
        start_http_server(8000)
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Scheduler started")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        # Keep the main thread alive
        try:
            while True:
                signal.pause()
        except (KeyboardInterrupt, SystemExit):
            self._handle_shutdown()
    
    def _handle_shutdown(self, signum: Optional[int] = None, frame: Optional[object] = None) -> None:
        """Handle graceful shutdown."""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown()
        self._save_state()  # Save final state before exit
        sys.exit(0) 