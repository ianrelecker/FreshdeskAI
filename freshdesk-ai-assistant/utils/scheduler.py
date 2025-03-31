import os
import json
import logging
import time
from datetime import datetime
from typing import Callable, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Scheduler for running periodic tasks."""
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Task scheduler initialized")
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Get poll interval from config (default to 5 minutes)
        self.poll_interval = self.config.get('app', {}).get('poll_interval_seconds', 300)
    
    def add_job(self, func: Callable, job_id: str, seconds: int = None, **kwargs) -> None:
        """Add a job to the scheduler.
        
        Args:
            func: Function to call
            job_id: Unique identifier for the job
            seconds: Interval in seconds (defaults to poll_interval from config)
            **kwargs: Additional arguments to pass to the function
        """
        if seconds is None:
            seconds = self.poll_interval
        
        trigger = IntervalTrigger(seconds=seconds)
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )
        logger.info(f"Added job '{job_id}' with interval {seconds} seconds")
    
    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler.
        
        Args:
            job_id: Unique identifier for the job
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job '{job_id}'")
        except Exception as e:
            logger.error(f"Error removing job '{job_id}': {str(e)}")
    
    def shutdown(self) -> None:
        """Shut down the scheduler."""
        self.scheduler.shutdown()
        logger.info("Task scheduler shut down")


# Global scheduler instance
_scheduler = None

def get_scheduler() -> TaskScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def setup_ticket_processing_jobs() -> None:
    """Set up jobs for ticket importing and processing."""
    from freshdesk.ticket_importer import run_importer
    # Removed automatic response generation
    
    scheduler = get_scheduler()
    
    # Add job for importing tickets only
    scheduler.add_job(run_importer, 'import_tickets')
    
    # Note: Response generation is now manual only, triggered by user action
    
    logger.info("Ticket processing jobs set up (automatic response generation disabled)")


if __name__ == "__main__":
    # Test the scheduler
    def test_job():
        logger.info(f"Test job running at {datetime.now()}")
    
    scheduler = get_scheduler()
    scheduler.add_job(test_job, 'test_job', seconds=10)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
