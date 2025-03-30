"""
CPU stress test job to verify pod recovery functionality
"""
import logging
import multiprocessing
import time
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cpu_intensive_task():
    """Simulate CPU-intensive work"""
    while True:
        # Perform CPU-intensive calculations
        _ = [i * i for i in range(10000)]
        time.sleep(0.1)  # Small delay to prevent complete CPU lock

def run_cpu_stress() -> Any:
    """
    CPU stress test function that will:
    1. Start multiple CPU-intensive processes
    2. Run for a specified duration
    3. Potentially crash the pod due to resource exhaustion
    """
    try:
        logger.info("Starting CPU stress test...")
        
        # Start multiple CPU-intensive processes
        num_processes = multiprocessing.cpu_count() * 2  # Double the CPU cores
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

if __name__ == "__main__":
    run_cpu_stress() 