import os
import json
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logger(name: str = None, log_to_console: bool = True, log_to_file: bool = True) -> logging.Logger:
    """Set up a logger with console and file handlers.
    
    Args:
        name: Logger name (defaults to root logger)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        
    Returns:
        Configured logger
    """
    # Get the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatters
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    
    # Add console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler
    if log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create rotating file handler
        log_file = os.path.join(logs_dir, 'app.log')
        file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)  # 10MB max size, 5 backups
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Set up the root logger when this module is imported
setup_logger()

if __name__ == "__main__":
    # Test the logger
    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
