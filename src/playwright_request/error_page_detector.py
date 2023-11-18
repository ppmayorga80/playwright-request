"""error page detector file"""
from abc import ABC, abstractmethod
from selectorlib import Extractor


class ErrorPageDetector(ABC):
    """error page detector abstract class
    in order to implement this class you must inherit this class and define the
    build_extractor method usually with a yml file template
    the results of the extract method must contain all possible errors you want to detect
    for example:
    www.amazon.com gives you a html content when detects a robot or when something is wrong
    in this case the template.yml should look like:
    error_on_title:
        xpath: '//title[contains(text(),"Sorry! Something went wrong")]'
        type: Text
    robot_detection:
        xpath: '//p[contains(text(),"Sorry, we just need to make sure you") and contains(text(),"re not a robot")]'
        Type: Text
    """

    def __init__(self):
        self.extractor: Extractor = self.build_extractor()

    @abstractmethod
    def build_extractor(self) -> Extractor:
        """build the extractor, example:
        return Extractor.from_yaml_file("template.yml")
        """

    def detect_errors(self, html: str) -> list[str]:
        """detect error on html
        returns the list of json strings detected with the extractor
        or empty list in case not errors are detected

        :param html: the input html content to be analyzed
        """
        raw_data = self.extractor.extract(html)
        error_flags = [f"{{'{k}':'{v}'}}" for k, v in raw_data.items() if v]
        return error_flags
