"""
CPU stress test job to verify pod recovery functionality
"""
import logging
import multiprocessing
import os
import psutil
import signal
import sys
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TOTAL_CPU = psutil.cpu_count(logical=True)  # Total number of CPU cores

def cpu_intensive_task(core_id: int):
    """Simulate CPU-intensive work on a specific core"""
    try:
        # Set process affinity to specific core
        proc = psutil.Process()
        proc.cpu_affinity([core_id])
        
        logger.info(f"Starting CPU stress on core {core_id} at 100%")
        
        while True:
            # Infinite loop with complex calculations
            while True:
                # Nested infinite loops for maximum CPU usage
                while True:
                    # Complex mathematical operations
                    result = 0
                    for i in range(10000000):  # Much larger range
                        result += (i * i * i * i) / (i + 1)  # More complex calculation
                
    except Exception as e:
        logger.error(f"Error in CPU stress task on core {core_id}: {str(e)}")
        raise

def run_cpu_stress() -> Any:
    """
    CPU stress test function that will:
    1. Start CPU-intensive processes on all available cores
    2. Run indefinitely until interrupted
    """
    try:
        logger.info(f"Starting continuous CPU stress test on {TOTAL_CPU} cores...")
        processes = []
        
        # Start many more processes than cores for maximum stress
        for i in range(TOTAL_CPU * 4):  # Quadruple the number of processes
            p = multiprocessing.Process(
                target=cpu_intensive_task,
                args=(i % TOTAL_CPU,)  # Wrap around to available cores
            )
            p.start()
            processes.append(p)
            logger.info(f"Started process on core {i % TOTAL_CPU}")
        
        # Wait indefinitely
        while True:
            for p in processes:
                if not p.is_alive():
                    logger.error("A CPU stress process died unexpectedly")
                    raise Exception("CPU stress process died")
        
    except Exception as e:
        logger.error(f"CPU stress test failed: {str(e)}")
        raise
    finally:
        # Cleanup processes
        for p in processes:
            p.terminate()
            p.join()

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}. Cleaning up...")
    # Terminate all child processes
    for child in multiprocessing.active_children():
        child.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the stress test
    run_cpu_stress() 