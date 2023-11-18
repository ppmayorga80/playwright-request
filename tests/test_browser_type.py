"""testing file for playwright browser type"""
import pytest

from playwright_request.browser_type import BrowserType


def test_playwright_browser_type():
    """function to test all type values"""
    type_1 = BrowserType.FIREFOX
    type_2 = BrowserType.CHROMIUM
    type_3 = BrowserType.WEBKIT

    assert type_1.value == "FIREFOX"
    assert type_2.value == "CHROMIUM"
    assert type_3.value == "WEBKIT"

    type_x = BrowserType("CHROMIUM")
    assert type_x.value == "CHROMIUM"

    with pytest.raises(Exception):
        undef = BrowserType("NON-VALID-BROWSER-NAME")
        print(f"{undef} THIS WON'T BE PRINTED")
