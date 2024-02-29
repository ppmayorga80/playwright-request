"""The testing file for PlaywrightResponse class"""
from playwright_request.playwright_response import PlaywrightResponse


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


def test_playwright_response_str():
    """test the str magic method"""
    resp = PlaywrightResponse(content="", html="GOOD", status_code=200)
    text1 = str(resp)
    assert "OK" in text1

    resp = PlaywrightResponse(content="", html="", status_code=200)
    text1 = str(resp)
    assert "ERROR" in text1

    resp = PlaywrightResponse(content="",
                              html="GOOD",
                              status_code=200,
                              error_list=["ONE ERROR"])
    text1 = str(resp)
    assert "ERROR" in text1
