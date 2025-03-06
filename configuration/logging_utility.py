import logging
import os
import glob
from datetime import datetime,timedelta

LOG_DIR="logs"
LOG_RETENTION_DAYS=2

def setup_logger(name,log_file,level=logging.INFO):
    os.makedirs(LOG_DIR,exist_ok=True)

    # create log filename with timestamp
    log_path=os.path.join(LOG_DIR,log_file)

    # create formatter
    formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

    # Create file handler
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(formatter)

    # create console handler
    console_handler=logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # create logger
    logger=logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

     # Delete old log files
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    return logger

def cleanup_old_logs(log_dir,retention_days):
    cutoff_time = datetime.now() - timedelta(days=retention_days)

    for log_file in glob.glob(os.path.join(log_dir,'*.txt')):
        file_time=datetime.fromtimestamp(os.path.getmtime(log_file))
        if file_time<cutoff_time:
            os.remove(log_file)
            print(f"Deleted old log file: {log_file}")

log_filename=f"app_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

logger=setup_logger('app_logger',log_filename)
