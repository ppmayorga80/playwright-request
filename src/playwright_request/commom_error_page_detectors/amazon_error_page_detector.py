"""file to define an amazon error page detector"""
import os.path

from selectorlib import Extractor

from playwright_request.error_page_detector import ErrorPageDetector


class AmazonErrorPageDetector(ErrorPageDetector):
    """class aiming to detect amazon error pages"""

    def build_extractor(self) -> Extractor:
        """build the extractor"""
        path = os.path.join(os.path.dirname(__file__),
                            "templates/amazon_error_page_template.yml")
        extractor = Extractor.from_yaml_file(path)
        return extractor

    def other_errors(self, html: str) -> list[str]:
        """detect other errors"""
        other_errors = []

        # 1. automated error detection
        text = "To discuss automated access to Amazon data please contact api-services-support@amazon.com"
        other_errors += [text] if text in html else []

        # 2. almost empty page
        text = "Your recently viewed items and featured recommendations"
        min_len = 240000
        other_errors += ["Almost empty page"
                         ] if (text in html) and (len(html) < min_len) else []

        return other_errors

    def detect_errors(self, html: str) -> list[str]:
        """detect errors"""
        # default errors defined by the extractor
        errors = super().detect_errors(html=html)

        errors += self.other_errors(html=html)
        # error from html content

        # return the errors
        return errors
