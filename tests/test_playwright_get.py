"""testing playwright_request file"""
import os
from unittest.mock import patch

import playwright.sync_api
from playwright.sync_api import Page
from selectorlib import Extractor

from playwright_request.browser_type import BrowserType
from playwright_request.error_page_detector import ErrorPageDetector
from playwright_request.playwright_get import PlaywrightGet
from playwright_request.playwright_response import PlaywrightResponse
from playwright_request.route_interceptor import RouteInterceptor

HEADLESS = os.environ.get("HEADLESS", "False").lower() == "true"
# HEADLESS = False
# 1. test Pi page at wikipedia
GOOD_URL = "https://en.wikipedia.org/wiki/Pi"
BAD_URL = "https://en.wikipedia.org/wiki/not/existing/page/here"


def test_playwright_get_constructor():
    """test constructor of class PlaywrightRequest"""
    requester = PlaywrightGet()
    assert not requester.url
    assert not requester.response
    assert not requester.html
    assert not requester.status_code
    assert not requester.elapsed_time


def extra_func(page: Page, name: str, value: float) -> str:
    return f"hello world {name}:{value}" if page is not None else "hello"


def test_playwright_get_extra_function():
    """test extra function"""
    # 1. test default extra function
    requester = PlaywrightGet()
    res = requester.extra_function(page=None)
    assert res is None

    # 2. test extra func
    requester = PlaywrightGet(extra_function_ptr=extra_func,
                              extra_kwargs={
                                  "name": "pi",
                                  "value": 3.1416
                              })
    res = requester.extra_function(page=True, **requester.extra_kwargs)
    assert res == "hello world pi:3.1416"


def test_str_magic_method():
    """test __str__ magic method"""
    requester = PlaywrightGet()
    txt = str(requester)
    assert isinstance(txt, str)
    assert "#URL" in txt
    assert "STATUS_CODE" in txt
    assert "ELAPSED" in txt


def test_get_fn():
    """testing the request method"""
    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightGet(browser=BrowserType.FIREFOX,
                              headless=HEADLESS,
                              route_interceptor=interceptor)
    # 1.3 get the responses
    response = requester.get(url=GOOD_URL)
    # 1.4 test the results
    assert isinstance(response, PlaywrightResponse)
    assert response.status_code > 0
    assert response.html
    # 1.5 save the html

    # 2. tests with other browsers
    for t in (BrowserType.CHROMIUM, BrowserType.WEBKIT):
        req = PlaywrightGet(browser=t,
                            headless=HEADLESS,
                            route_interceptor=interceptor)
        res = req.get(GOOD_URL)
        assert res.status_code > 0


def test_get_with_delay_before_goto():
    """testing the request method with delay before goto"""
    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightGet(browser=BrowserType.FIREFOX,
                              headless=HEADLESS,
                              route_interceptor=interceptor,
                              random_delay_before_goto=(0.161, 0.314))
    # 1.3 get the responses
    response = requester.get(url=GOOD_URL)
    # 1.4 test the results
    assert isinstance(response, PlaywrightResponse)
    assert response.status_code > 0
    assert response.html


def new_page_exception():
    """raise an exception when new_page is called"""
    raise ValueError("Exception: general mock exception for playwright")


@patch.object(playwright.sync_api.BrowserContext, 'new_page')
def test_new_page_raises(mock_new_page):
    """inject an exception and test results"""
    # 1. mock the context
    mock_new_page.side_effect = new_page_exception

    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightGet(browser=BrowserType.FIREFOX,
                              headless=HEADLESS,
                              route_interceptor=interceptor)
    # 1.3 get the responses
    response = requester.get(url=GOOD_URL)
    assert response.status_code == -1
    assert not response.content
    assert response.exception_list
    assert "Exception:" in response.exception_list[0]


def goto_exception(url: str, timeout: int = 0):
    """raise an exception when goto is called"""
    raise ValueError(f"Exception: can't goto(url='{url}', timeout={timeout})")


def wait_for_load_state_exception(state: str = "", timeout: int = 0):
    """raise an exception when wait_for_load_state is called"""
    raise ValueError(
        f"Exception: can't wait_for_load_state(state='{state}', timeout={timeout})"
    )


@patch.object(playwright.sync_api.Page, 'wait_for_load_state')
@patch.object(playwright.sync_api.Page, 'goto')
def test_goto_and_wait_for_load_state_raises(mock_goto,
                                             mock_wait_for_load_state):
    """inject an exception and test results"""
    # 1. mock the context
    mock_goto.side_effect = goto_exception
    mock_wait_for_load_state.side_effect = wait_for_load_state_exception

    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightGet(browser=BrowserType.FIREFOX,
                              headless=HEADLESS,
                              route_interceptor=interceptor,
                              await_for_networkidle=True,
                              await_for_doom=True,
                              await_for_load_state=True)
    # 1.3 get the responses
    response = requester.get(url=GOOD_URL)
    assert response.status_code == 500
    assert response.exception_list
    assert len(
        response.exception_list
    ) == 4  # goto(), await_for_load_state('networkidle'),await_for_load_state('doomcontentloaded') and await_for_load_state()
    assert all("Exception:" in x for x in response.exception_list)


class WikipediaErrorPageDetector(ErrorPageDetector):
    """class for detect errors at Wikipedia"""

    def build_extractor(self) -> Extractor:
        """build a simple selector for wikipedia"""
        return Extractor.from_yaml_string("\n".join([
            "not_exists:",
            "  xpath: '//*[contains(text(),\"Wikipedia does not have an article with this exact name.\")]'",
            "  type: Text"
        ]))


def test_with_error_page_detectors():
    """test for error detectors"""
    # 1. define a requester object
    requester = PlaywrightGet(
        browser=BrowserType.FIREFOX,
        headless=HEADLESS,
        route_interceptor=None,
        await_for_networkidle=False,
        await_for_doom=False,
        await_for_load_state=False,
        error_page_detectors=[WikipediaErrorPageDetector()])
    # 2 get the response and test is OK
    response = requester.get(url=GOOD_URL)
    assert response.status_code // 100 == 2  # 2xx
    assert not response.error_list
    assert response.html

    # 3. get another response and test is BAD
    response = requester.get(url=BAD_URL)
    assert response.status_code // 100 == 4  # 4xx (for this case is 404)
    assert response.error_list  # contains errors
    assert not response.html  # the html is empty
    assert response.content  # the content is complete
