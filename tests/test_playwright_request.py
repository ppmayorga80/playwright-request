"""testing playwright_request file"""
from playwright_request.playwright_request import log_message, PlaywrightResponse, PlaywrightRequest


def test_log_message():
    """test log_message function"""
    log_message("hello", "info")
    log_message("hello", "warning")
    log_message("hello", "error")
    log_message("hello", "debug")
    log_message("hello", "other")


def test_playwright_response():
    """test PlaywrightResponse class"""

    resp = PlaywrightResponse(content="", html="", status_code=200)
    assert resp
    assert resp.status_code == 200

    resp = PlaywrightResponse.exception()
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

async def test_playwright_request_extra_function():
    """test extra function"""
    requester = PlaywrightRequest()
    res = await requester.extra_function(page=None)
    assert res is None

def test_str_magic_method():
    """test __str__ magic method"""
    requester = PlaywrightRequest()
    txt = str(requester)
    assert isinstance(txt, str)
    assert "#URLS" in txt
    assert "STATUSES" in txt
    assert "ELAPSED" in txt
