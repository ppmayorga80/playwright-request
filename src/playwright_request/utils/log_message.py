"""log_message file definition"""
import logging


def log_message(msg: str, level: str = "info"):
    """logging message with a predefined level"""
    if level == "info":
        logging.info(msg)
    elif level == "warning":
        logging.warning(msg)
    elif level == "error":
        logging.error(msg)
    elif level == "debug":
        logging.debug(msg)
    else:
        logging.info(msg)
