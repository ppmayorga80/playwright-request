"""file to define an amazon error page detector"""
import os.path

from selectorlib import Extractor

from playwright_request.error_page_detector import ErrorPageDetector


class AirbnbErrorPageDetector(ErrorPageDetector):
    """class aiming to detect airbnb error pages"""

    def build_extractor(self) -> Extractor:
        """build the extractor"""
        path = os.path.join(os.path.dirname(__file__),
                            "templates/airbnb_error_page_template.yml")
        extractor = Extractor.from_yaml_file(path)
        return extractor
