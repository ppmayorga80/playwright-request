"""test all error page detectors"""
from selectorlib import Extractor

from playwright_request.commom_error_page_detectors.airbnb_error_page_detector import AirbnbErrorPageDetector
from playwright_request.commom_error_page_detectors.amazon_error_page_detector import AmazonErrorPageDetector
from playwright_request.commom_error_page_detectors.tripadvisor_error_page_detector import TripadvisorErrorPageDetector
from playwright_request.error_page_detector import ErrorPageDetector


class CustomErrorPageDetector(ErrorPageDetector):
    """testing class"""

    def build_extractor(self) -> Extractor:
        content = "\n".join([
            "access_denied:",
            "  xpath: '//*[contains(text(),\"Access Denied\")]'",
            "  type: Text"
        ])
        return Extractor.from_yaml_string(content)


def test_error_page_abstract_class():
    """test the abstract class"""

    # 2. we can create the object in inherited class
    custom = CustomErrorPageDetector()
    assert custom

    # 2.1 detect error html
    html = "<html><body><div><h1>Access Denied</h1></div></body></html>"
    response = custom.detect_errors(html=html)
    assert response

    # 2.2 detect good html
    html = "<html><body><div><h1>Hello World</h1></div></body></html>"
    response = custom.detect_errors(html=html)
    assert not response


def test_custom_classes():
    """test custom classes for airbnb, amazon and tripadvisor"""
    # 1. define the htmls
    good_html = "<html><body><div><h1>Hello World</h1></div></body></html>"
    airbnb_error_html = "<html><body><div><h1>Oops!</h1><p>You don't have permission to access</p></div></body></html>"
    amazon_error_html = "<html><body><div><title>Sorry! Something went wrong</title><p>Sorry, we just need to make sure you're not a robot</p></div></body></html>"
    tripadvisor_error_html = "<html><body><div><h1>Access Denied!</h1></div></body></html>"

    # 2. define the detectors
    airbnb_error_detector = AirbnbErrorPageDetector()
    amazon_error_detector = AmazonErrorPageDetector()
    tripadvisor_error_detector = TripadvisorErrorPageDetector()

    # 3. test airbnb detector
    errors = airbnb_error_detector.detect_errors(good_html)
    assert not errors
    errors = airbnb_error_detector.detect_errors(airbnb_error_html)
    assert errors

    # 4. test amazon detector
    errors = amazon_error_detector.detect_errors(good_html)
    assert not errors
    errors = amazon_error_detector.detect_errors(amazon_error_html)
    assert errors

    # 4. test tripadvisor detector
    errors = tripadvisor_error_detector.detect_errors(good_html)
    assert not errors
    errors = tripadvisor_error_detector.detect_errors(tripadvisor_error_html)
    assert errors
