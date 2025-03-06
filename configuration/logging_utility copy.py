import logging
import os
from datetime import datetime

def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger that writes to both console and file"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create a logger
log_file = f"logs/app_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logger = setup_logger('app_logger', log_file)