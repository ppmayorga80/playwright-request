"""The Playwright Response file class"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlaywrightResponse:
    """response class for playwright request class"""
    content: str
    html: str
    status_code: int
    exception_list: list = field(default_factory=list)
    error_list: list = field(default_factory=list)
    extra_result: Any = None

    def __str__(self):
        """common magic method for str"""
        text_ok = f"<{self.status_code} OK> 🟢"
        text_error = f"<{self.status_code} ERROR> 🔴 {self.error_list}"
        text = text_ok if (self.html and not self.error_list
                           and not self.exception_list) else text_error
        return text

    @classmethod
    def exception_response(cls) -> 'PlaywrightResponse':
        return cls(content="",
                   html="",
                   status_code=-1,
                   exception_list=["Exception"],
                   error_list=[],
                   extra_result=None)
