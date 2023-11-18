"""playwright request file"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import async_playwright, Page

from playwright_request.browser_type import BrowserType
from playwright_request.error_page_detector import ErrorPageDetector
from playwright_request.route_interceptor import RouteInterceptor


def log_message(msg: str, level: str = "info"):  # pragma: no cover
    """logging message with a predefined level"""
    if level == "info":
        logging.info(msg)
    elif level == "warning":
        logging.warning(msg)
    elif level == "error":
        logging.error(msg)
    elif level == "debug":
        logging.debug(msg)
    else:
        logging.info(msg)


@dataclass
class PlaywrightResponse:
    """response class for playwright request class"""
    content: str
    html: str
    status_code: int
    exception_list: list = field(default_factory=list)
    error_list: list = field(default_factory=list)
    extra_result: Any = None

    @classmethod
    def exception(cls) -> 'PlaywrightResponse':
        return cls(
            content="",
            html="",
            status_code=-1,
            exception_list=["Exception"],
            error_list=[],
            extra_result=None
        )


class PlaywrightRequest:
    """class to implement request with playwright"""

    def __init__(self,
                 browser: BrowserType = BrowserType.FIREFOX,
                 headless: bool = False,
                 route_interceptor: RouteInterceptor or None = None,
                 proxy: dict or None = None,
                 await_for_networkidle: bool = False,
                 await_for_load_state: bool = False,
                 timeout_ms: int = 15000,
                 error_page_detectors: list[ErrorPageDetector] or None = None):
        self.browser_type: BrowserType = browser
        self.headless: bool = headless
        self.route_interceptor: RouteInterceptor = route_interceptor
        self.proxy: dict = proxy
        self.await_for_networkidle: bool = await_for_networkidle
        self.await_for_load_state: bool = await_for_load_state
        self.timeout_ms: int = timeout_ms
        self.error_page_detectors: list[ErrorPageDetector] = error_page_detectors

        self.urls: list[str] = []
        self.responses: list[PlaywrightResponse] = []
        self.htmls: list[str] = []
        self.status_codes: list[int] = []
        self.elapsed_time: float = 0.0

    async def extra_function(self, page: Page or None) -> Any:
        """define a function to operate the page before close
        useful when inherit this class and do operation over the page
        like click on elements etc...
        """
        return None

    def __str__(self):
        """message class"""
        lines = [
            f"#URLS: {len(self.urls)}",
            f"STATUSES: {self.status_codes}",
            f"ELAPSED: {self.elapsed_time} sec",
        ]
        return "\n".join(lines)

    def request(self, urls: list[str]) -> list[PlaywrightResponse]:
        """request operations over the urls"""
        self.urls = urls
        t1 = time.perf_counter()
        responses = asyncio.run(self._request_many(urls=urls))

        self.responses = responses
        self.htmls = [x.html for x in responses]
        self.status_codes = [x.status_code for x in responses]

        t2 = time.perf_counter()
        self.elapsed_time = t2 - t1
        return self.responses

    async def _request_many(self, urls: list[str]) -> list[PlaywrightResponse]:
        """request many urls asynchronously"""
        async with async_playwright() as p:
            if self.browser_type == BrowserType.FIREFOX:
                browser = await p.firefox.launch(headless=self.headless, proxy=self.proxy)
            elif self.browser_type == BrowserType.CHROMIUM:
                browser = await p.chromium.launch(headless=self.headless, proxy=self.proxy)
            elif self.browser_type == BrowserType.WEBKIT:
                browser = await p.webkit.launch(headless=self.headless, proxy=self.proxy)
            else:
                browser = await p.firefox.launch(headless=self.headless, proxy=self.proxy)

            context = await browser.new_context()
            tasks = [
                asyncio.ensure_future(
                    self._request_one(
                        context=context,
                        url=url
                    ))
                for url in urls
            ]
            raw_responses = await asyncio.gather(*tasks, return_exceptions=True)
            responses = [x if isinstance(x, PlaywrightResponse) else PlaywrightResponse.exception()
                         for x in raw_responses]

            return responses

    async def _request_one(self, context, url) -> PlaywrightResponse:
        """request one html from url by using the context object
        and returns a tuple with:
            original html
            parsed html
            status_code
            a list of detected errors
        """

        # 1. open a new page
        try:
            page: Page = await context.new_page()
        except Exception as e:
            log_message(f"Error `new_page()` at '{url}': {e}", "error")
            return PlaywrightResponse(content="", html="", status_code=500, exception_list=[str(e)],
                                      extra_result=None)

        # 2.1 configure a route interceptor
        if self.route_interceptor and (self.route_interceptor.block_resources is True):
            await page.route("**/*", self.route_interceptor.route_intercept)

        status_code = -1
        exception_list = []

        # 2.2 going to url
        try:
            response = await page.goto(url=url, timeout=self.timeout_ms)
            status_code = response.status
            ok_str = f"{status_code}-OK✅" if response.ok else f"{status_code}-🔴"
            log_message(f"Response: {status_code}, {ok_str}", "info")
        except Exception as e:
            exception_list.append(str(e))
            log_message(f"Error `goto()` at '{url}': {e}", "error")

        # 3. wait until the page is loaded if necessary
        if self.await_for_networkidle:
            try:
                await page.wait_for_load_state(state='networkidle', timeout=self.timeout_ms)
            except Exception as e:
                exception_list.append(str(e))
                log_message(f"Error `wait_for_load_state(state='networkidle')` at '{url}': {e}", "error")
        if self.await_for_load_state:
            try:
                await page.wait_for_load_state(timeout=self.timeout_ms)
            except Exception as e:
                exception_list.append(str(e))
                log_message(f"Error `wait_for_load_state()` at '{url}': {e}", "error")

        # 4. get the html content
        original_html = await page.content()
        html = original_html
        error_list = []

        # 5. detect errors if provided
        if self.error_page_detectors:
            error_flag = False
            for error_detector in self.error_page_detectors:
                error_list = error_detector.detect_errors(html)
                if error_list:
                    error_flag = True
                    log_message(f"'{error_detector.__name__}' detects the following errors:", "error")
                    log_message(", ".join(error_list), "error")
            html = "" if error_flag else html

        # if implemented, operate over the page
        extra_result = await self.extra_function(page=page)

        await page.close()

        return PlaywrightResponse(
            content=original_html,
            html=html,
            status_code=status_code,
            exception_list=exception_list,
            error_list=error_list,
            extra_result=extra_result
        )
