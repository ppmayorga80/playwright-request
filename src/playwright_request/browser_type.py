"""file with class able to describe 3 types of playwright browsers"""
from enum import Enum


class BrowserType(Enum):
    """class to enum browser types"""
    FIREFOX = "FIREFOX"
    CHROMIUM = "CHROMIUM"
    WEBKIT = "WEBKIT"
