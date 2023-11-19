"""test log_message file"""
from playwright_request.utils.log_message import log_message


def test_log_message():
    """test log_message function"""
    log_message("hello", "info")
    log_message("hello", "warning")
    log_message("hello", "error")
    log_message("hello", "debug")
    log_message("hello", "other")
