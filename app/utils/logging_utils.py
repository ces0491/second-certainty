# app/utils/logging_utils.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app_name="second_certainty", log_level=logging.INFO):
    """
    Set up application logging with file and console handlers.

    Args:
        app_name: Name of the application (used for the log file names)
        log_level: Logging level to use

    Returns:
        Logger instance configured with appropriate handlers
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates when reloading in development
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create file handler for general logs
    general_log_file = log_dir / f"{app_name}.log"
    file_handler = RotatingFileHandler(general_log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10 MB
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    # Create file handler for errors only
    error_log_file = log_dir / f"{app_name}_error.log"
    error_file_handler = RotatingFileHandler(error_log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10 MB
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    logger.addHandler(error_file_handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger


def get_logger(module_name):
    """
    Get a module-specific logger that inherits from the main application logger.

    Args:
        module_name: Name of the module requesting the logger

    Returns:
        Logger instance with the module name
    """
    return logging.getLogger(f"second_certainty.{module_name}")
