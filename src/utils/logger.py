import os
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Define log levels with their corresponding colors for console output
LOG_COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[91m\033[1m",  # Bold Red
    "RESET": "\033[0m",  # Reset color
}

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)


# Custom formatter for colored console output
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        if levelname in LOG_COLORS:
            # Check if we're in a terminal that supports colors
            if sys.stdout.isatty():
                record.levelname = (
                    f"{LOG_COLORS[levelname]}{levelname}{LOG_COLORS['RESET']}"
                )
        return super().format(record)


# Custom formatter for log files (without colors)
class FileFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record)


# Initialize the logger
def setup_logger(
    name="dasher", log_level=logging.INFO, log_to_file=True, log_to_console=True
):
    """
    Set up and configure the logger.

    Args:
        name (str): Name of the logger
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
        log_to_file (bool): Whether to log to a file
        log_to_console (bool): Whether to log to the console

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create formatters
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%H:%M:%S"
    )

    file_formatter = FileFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Add file handler if requested
    if log_to_file:
        # Create a log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/dasher_{timestamp}.log"

        # Use RotatingFileHandler to limit file size
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3  # 5 MB
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logger()


# Module-specific loggers
def get_module_logger(module_name):
    """
    Get a logger for a specific module.

    Args:
        module_name (str): Name of the module

    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(f"dasher.{module_name}")


# Configure logger based on environment variables or .env file
def configure_from_env():
    """Configure the logger based on environment variables."""
    import os

    # Get log level from environment variable, default to DEBUG
    log_level_name = os.getenv("LOG_LEVEL", "DEBUG")
    log_level = getattr(logging, log_level_name, logging.DEBUG)

    # Get log to file setting from environment variable, default to True
    log_to_file = os.getenv("LOG_TO_FILE", "True").lower() in ("true", "1", "t")

    # Get log to console setting from environment variable, default to True
    log_to_console = os.getenv("LOG_TO_CONSOLE", "True").lower() in ("true", "1", "t")

    # Reconfigure the logger
    global logger
    logger = setup_logger(
        log_level=log_level, log_to_file=log_to_file, log_to_console=log_to_console
    )

    logger.info(
        f"Logger configured with level={log_level_name}, file={log_to_file}, console={log_to_console}"
    )


# Call configure_from_env when the module is imported
configure_from_env()
