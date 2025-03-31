#!/usr/bin/env python3
"""
Memory stress test job to verify pod recovery functionality
"""
import logging
import signal
import sys
import time
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List to store memory chunks
memory_chunks = []

def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    logger.info(f"Received signal {signum}. Cleaning up...")
    memory_chunks.clear()
    sys.exit(0)

def run_memory_stress():
    """Continuously allocate memory in chunks until OOM killer intervenes."""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    chunk_size = 100 * 1024 * 1024  # 100MB chunks
    allocated = 0

    try:
        while True:
            # Allocate memory in 100MB chunks
            memory_chunks.append(bytearray(chunk_size))
            allocated += chunk_size
            logger.info(f"Allocated {allocated / (1024*1024):.2f} MB of memory")
            time.sleep(1)  # Brief pause between allocations
    except MemoryError:
        logger.error("Memory allocation failed - OOM condition reached")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Cleaning up allocated memory...")
        memory_chunks.clear()

if __name__ == "__main__":
    logger.info("Starting memory stress test...")
    run_memory_stress() 