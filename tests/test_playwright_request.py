"""testing playwright_request file"""
import os
from unittest.mock import patch

import playwright.async_api
from playwright.async_api import Page
from selectorlib import Extractor

from playwright_request.browser_type import BrowserType
from playwright_request.error_page_detector import ErrorPageDetector
from playwright_request.playwright_request import PlaywrightResponse, PlaywrightRequest
from playwright_request.route_interceptor import RouteInterceptor

HEADLESS = os.environ.get("HEADLESS", "False").lower() == "true"
# 1. test Pi page at wikipedia
GOOD_URL = "https://en.wikipedia.org/wiki/Pi"
BAD_URL = "https://en.wikipedia.org/wiki/not/existing/page/here"


def test_playwright_response():
    """test PlaywrightResponse class"""

    resp = PlaywrightResponse(content="", html="", status_code=200)
    assert resp
    assert resp.status_code == 200

    resp = PlaywrightResponse.exception_response()
    assert isinstance(resp, PlaywrightResponse)
    assert resp.content == ""
    assert resp.html == ""
    assert resp.status_code == -1
    assert "Exception" in resp.exception_list
    assert not resp.error_list
    assert resp.extra_result is None


def test_playwright_request_constructor():
    """test constructor of class PlaywrightRequest"""
    requester = PlaywrightRequest()
    assert not requester.urls
    assert not requester.responses
    assert not requester.htmls
    assert not requester.status_codes
    assert not requester.elapsed_time


async def extra_func(page: Page) -> str:
    return "hello world" if page is not None else "hello"


async def test_playwright_request_extra_function():
    """test extra function"""
    # 1. test default extra function
    requester = PlaywrightRequest()
    res = await requester.extra_function(page=None)
    assert res is None

    # 2. test extra func
    requester = PlaywrightRequest(extra_async_function_ptr=extra_func)
    res = await requester.extra_function(page=None)
    assert res == "hello world"


def test_str_magic_method():
    """test __str__ magic method"""
    requester = PlaywrightRequest()
    txt = str(requester)
    assert isinstance(txt, str)
    assert "#URLS" in txt
    assert "STATUSES" in txt
    assert "ELAPSED" in txt


def test_request():
    """testing the request method"""
    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightRequest(browser=BrowserType.FIREFOX,
                                  headless=HEADLESS,
                                  route_interceptor=interceptor)
    # 1.3 get the responses
    responses = requester.get(urls=[GOOD_URL])
    # 1.4 test the results
    assert isinstance(responses, list)
    assert len(responses) == 1
    assert isinstance(responses[0], PlaywrightResponse)
    assert responses[0].status_code > 0
    assert responses[0].html
    # 1.5 save the html

    # 2. test with other browsers
    for t in (BrowserType.CHROMIUM, BrowserType.WEBKIT):
        req = PlaywrightRequest(browser=t,
                                headless=HEADLESS,
                                route_interceptor=interceptor)
        res = req.get([GOOD_URL])
        assert res[0].status_code > 0


def new_page_exception():
    """raise an exception when new_page is called"""
    raise ValueError("Exception: general mock exception for playwright")


@patch.object(playwright.async_api.BrowserContext, 'new_page')
def test_new_page_raises(mock_new_page):
    """inject an exception and test results"""
    # 1. mock the context
    mock_new_page.side_effect = new_page_exception

    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightRequest(browser=BrowserType.FIREFOX,
                                  headless=HEADLESS,
                                  route_interceptor=interceptor)
    # 1.3 get the responses
    responses = requester.get(urls=[GOOD_URL])
    assert responses[0].status_code == -1
    assert not responses[0].content
    assert responses[0].exception_list
    assert "Exception:" in responses[0].exception_list[0]


def goto_exception(url: str, timeout: int = 0):
    """raise an exception when goto is called"""
    raise ValueError(f"Exception: can't goto(url='{url}', timeout={timeout})")


def wait_for_load_state_exception(state: str = "", timeout: int = 0):
    """raise an exception when wait_for_load_state is called"""
    raise ValueError(
        f"Exception: can't wait_for_load_state(state='{state}', timeout={timeout})"
    )


@patch.object(playwright.async_api.Page, 'wait_for_load_state')
@patch.object(playwright.async_api.Page, 'goto')
def test_goto_and_wait_for_load_state_raises(mock_goto,
                                             mock_wait_for_load_state):
    """inject an exception and test results"""
    # 1. mock the context
    mock_goto.side_effect = goto_exception
    mock_wait_for_load_state.side_effect = wait_for_load_state_exception

    # 1.1 define an interceptor to speed up the request (avoiding images)
    interceptor = RouteInterceptor().set_default_exclusions().block_on()
    # 1.2 define the requester
    requester = PlaywrightRequest(browser=BrowserType.FIREFOX,
                                  headless=HEADLESS,
                                  route_interceptor=interceptor,
                                  await_for_networkidle=True,
                                  await_for_doom=True,
                                  await_for_load_state=True)
    # 1.3 get the responses
    responses = requester.get(urls=[GOOD_URL])
    assert responses[0].status_code == -1
    assert responses[0].exception_list
    assert len(
        responses[0].exception_list
    ) == 4  # goto(), await_for_load_state('networkidle'),await_for_load_state('doomcontentloaded') and await_for_load_state()
    assert all("Exception:" in x for x in responses[0].exception_list)


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
    requester = PlaywrightRequest(
        browser=BrowserType.FIREFOX,
        headless=HEADLESS,
        route_interceptor=None,
        await_for_networkidle=False,
        await_for_doom=False,
        await_for_load_state=False,
        error_page_detectors=[WikipediaErrorPageDetector()])
    # 2 get the response and test is OK
    responses = requester.get(urls=[GOOD_URL])
    assert responses[0].status_code // 100 == 2  # 2xx
    assert not responses[0].error_list
    assert responses[0].html

    # 3. get another response and test is BAD
    responses = requester.get(urls=[BAD_URL])
    assert responses[0].status_code // 100 == 4  # 4xx (for this case is 404)
    assert responses[0].error_list  # contains errors
    assert not responses[0].html  # the html is empty
    assert responses[0].content  # the content is complete
