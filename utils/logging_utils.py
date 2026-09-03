"""Logging utility setup with console output formatting."""
import logging
import sys

def setup_logger(name: str = "OCR_Pipeline", level: int = logging.INFO) -> logging.Logger:
    """Configures structured console logging with custom format."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
