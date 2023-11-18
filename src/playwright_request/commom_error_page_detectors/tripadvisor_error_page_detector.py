"""file to define an tripadvisor error page detector"""
import os.path

from selectorlib import Extractor

from playwright_request.error_page_detector import ErrorPageDetector


class TripadvisorErrorPageDetector(ErrorPageDetector):
    """class aiming to detect tripadvisor error pages"""

    def build_extractor(self) -> Extractor:
        """build the extractor"""
        path = os.path.join(os.path.dirname(__file__),
                            "templates/tripadvisor_error_page_detector.yml")
        extractor = Extractor.from_yaml_file(path)
        return extractor
