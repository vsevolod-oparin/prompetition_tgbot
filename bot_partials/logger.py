import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

DEFAULT_BACKUP_COUNT = 100
MAX_BYTES_IN_LOG = 5 * 1024 * 1024
LOGGER_TAG = 'bot'

def init_logging():
    date_format = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt=date_format,
        level=logging.INFO
    )
    logger = logging.getLogger('httpx')
    logger.setLevel(logging.WARNING)

# Set up file handler with rotation
def produce_logger(
        log_file: Union[str | Path],
        max_bytes: int = MAX_BYTES_IN_LOG,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        logger_tag: str = LOGGER_TAG) -> logging.Logger:
    file_handler = RotatingFileHandler(
        log_file,  # The name of the log file to write to
        mode='a',  # The mode to open the file ('a' for append)
        maxBytes=max_bytes,  # The maximum size of the log file before rotation
        backupCount=backup_count,  # The number of old log files to keep (archived)
        encoding=None,  # The encoding to use for the log file (None for default)
        delay=False  # Whether to delay the file opening until the first log message is emitted
    )

    date_format = '%Y-%m-%d %H:%M:%S'
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt=date_format
    )
    file_handler.setFormatter(log_formatter)

    logger = logging.getLogger(logger_tag)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger

# Example log messages
if __name__ == '__main__':
    logger = produce_logger('logs/bot.log', 5_000_000)
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
