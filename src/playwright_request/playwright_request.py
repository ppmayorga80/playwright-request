"""playwright request file"""
import asyncio
import logging
import time
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from playwright.async_api import async_playwright, Page

from playwright_request.browser_type import BrowserType
from playwright_request.error_page_detector import ErrorPageDetector
from playwright_request.route_interceptor import RouteInterceptor
from playwright_request.utils.log_message import log_message


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


class PlaywrightRequest:
    """class to implement request with playwright"""

    def __init__(self,
                 browser: BrowserType = BrowserType.FIREFOX,
                 headless: bool = False,
                 route_interceptor: RouteInterceptor or None = None,
                 proxy: dict or None = None,
                 await_for_networkidle: bool = False,
                 await_for_doom: bool = False,
                 await_for_load_state: bool = False,
                 timeout_ms: int = 15000,
                 random_delay_before_goto: tuple[float, float] or None = None,
                 error_page_detectors: list[ErrorPageDetector] or None = None,
                 extra_async_function_ptr: Callable[[Page], Any]
                 or None = None,
                 extra_kwargs: dict or None = None):
        """constructor

        :param browser: the browser type FIREFOX, CHROMIUM, WEBKIT
        :param headless: flag to show or hide browser GUI
        :param route_interceptor: the object that intercepts routes and filter images,css, etc.
        :param proxy: proxy dictionary {"server":"","username":"","password":""}
        :param await_for_networkidle: flag to wait for networkidle while loading state
        :param await_for_doom: await for doom-content while loading state
        :param await_for_load_state: flag to wait for load_state while loading state
        :param timeout_ms: the number of milliseconds to wait when waiting for the function `wait_for_load_state`
        :param random_delay_before_goto: random interval, in seconds,  to wait before execute goto function
        :param error_page_detectors: the list of objects able to detect error pages
        :param extra_async_function_ptr: additional async function used to compute extra response data
        :param extra_kwargs: extra parameters passed to `extra_async_function_ptr` besides `Page`
        """
        self.browser_type: BrowserType = browser
        self.headless: bool = headless
        self.route_interceptor: RouteInterceptor = route_interceptor
        self.proxy: dict = proxy
        self.await_for_networkidle: bool = await_for_networkidle
        self.await_for_doom: bool = await_for_doom
        self.await_for_load_state: bool = await_for_load_state
        self.timeout_ms: int = timeout_ms
        self.random_delay_before_goto: tuple[int,
                                             int] = random_delay_before_goto
        self.error_page_detectors: list[
            ErrorPageDetector] = error_page_detectors
        self.extra_async_function_ptr = extra_async_function_ptr
        self.extra_kwargs = extra_kwargs if extra_kwargs is not None else {}

        self.urls: list[str] = []
        self.responses: list[PlaywrightResponse] = []
        self.htmls: list[str] = []
        self.status_codes: list[int] = []
        self.elapsed_time: float = 0.0

    async def extra_function(self, page: Page or None, **kwargs) -> Any:
        """define a function to operate the page before close
        useful when inherit this class and do operation over the page
        like click on elements etc...
        """
        if self.extra_async_function_ptr:
            return await self.extra_async_function_ptr(page=page, **kwargs)
        log_message(
            f"default extra_function that does nothing with page={page}")
        return None

    def __str__(self):
        """message class"""
        lines = [
            f"#URLS: {len(self.urls)}",
            f"STATUSES: {self.status_codes}",
            f"ELAPSED: {self.elapsed_time} sec",
        ]
        return "\n".join(lines)

    def get(self, urls: list[str]) -> list[PlaywrightResponse]:
        """request operations over the urls"""
        self.urls = urls
        starting_time = time.perf_counter()
        responses = asyncio.run(self._get_many(urls=urls))

        self.responses = responses
        self.htmls = [x.html for x in responses]
        self.status_codes = [x.status_code for x in responses]

        ending_time = time.perf_counter()
        self.elapsed_time = ending_time - starting_time
        return self.responses

    async def _get_many(self, urls: list[str]) -> list[PlaywrightResponse]:
        """request many urls asynchronously"""
        async with async_playwright() as p:
            if self.browser_type == BrowserType.FIREFOX:
                browser = await p.firefox.launch(headless=self.headless,
                                                 proxy=self.proxy)
            elif self.browser_type == BrowserType.CHROMIUM:
                browser = await p.chromium.launch(headless=self.headless,
                                                  proxy=self.proxy)
            elif self.browser_type == BrowserType.WEBKIT:
                browser = await p.webkit.launch(headless=self.headless,
                                                proxy=self.proxy)

            context = await browser.new_context()
            tasks = [
                asyncio.ensure_future(self._get_one(context=context, url=url))
                for url in urls
            ]
            raw_responses = await asyncio.gather(*tasks,
                                                 return_exceptions=True)
            responses = [
                x if isinstance(x, PlaywrightResponse) else
                PlaywrightResponse.exception_response() for x in raw_responses
            ]

            return responses

    async def _get_one(self, context, url) -> PlaywrightResponse:
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
        except Exception as error:
            log_message(f"Exception at `new_page()` for '{url}': {error}",
                        "error")
            return PlaywrightResponse(content="",
                                      html="",
                                      status_code=-1,
                                      exception_list=[str(error)],
                                      extra_result=None)

        # 2.1 configure a route interceptor
        if self.route_interceptor and (self.route_interceptor.block_resources
                                       is True):
            await page.route("**/*", self.route_interceptor.route_intercept)

        status_code = 500
        exception_list = []

        # wait a random interval before goto
        if self.random_delay_before_goto:
            random_interval = self.random_delay_before_goto
            rnd = int(random.uniform(*random_interval) * 1000)
            msg = f"waiting {rnd} ms before goto '{url}'"
            logging.info(msg)
            await page.wait_for_timeout(timeout=rnd)

        # 2.2 going to url
        try:
            response = await page.goto(url=url, timeout=self.timeout_ms)
            status_code = response.status
            ok_str = f"First {status_code}-OK" if response.ok else f"{status_code}"
            log_message(f"Response: {status_code}, {ok_str}", "info")
        except Exception as error:
            exception_list.append(str(error))
            log_message(f"Error `goto()` at '{url}': {error}", "error")

        # 3. wait until the page is loaded if necessary
        if self.await_for_networkidle:
            try:
                await page.wait_for_load_state(state='networkidle',
                                               timeout=self.timeout_ms)
            except Exception as error:
                exception_list.append(str(error))
                log_message(
                    f"Error `wait_for_load_state(state='networkidle')` at '{url}': {error}",
                    "error")

        if self.await_for_doom:
            try:
                await page.wait_for_load_state('domcontentloaded',
                                               timeout=self.timeout_ms)
            except Exception as error:
                exception_list.append(str(error))
                log_message(
                    f"Error `wait_for_load_state('domcontentloaded')` at '{url}': {error}",
                    "error")

        if self.await_for_load_state:
            try:
                await page.wait_for_load_state(timeout=self.timeout_ms)
            except Exception as error:
                exception_list.append(str(error))
                log_message(
                    f"Error `wait_for_load_state()` at '{url}': {error}",
                    "error")

        # 4. get the html content
        original_html = await page.content()
        html = original_html
        total_error_list = []
        error_flag = False

        # 5. detect errors if provided
        if self.error_page_detectors:
            for error_detector in self.error_page_detectors:
                error_list = error_detector.detect_errors(html)
                if error_list:
                    total_error_list += error_list
                    error_flag = True
                    log_message(
                        f"'{error_detector.__class__.__name__}' detects the following errors:",
                        "error")
                    log_message(", ".join(error_list), "error")
            html = "" if error_flag else html

        # if implemented, operate over the page
        extra_result = await self.extra_function(page=page,
                                                 **self.extra_kwargs)

        await page.close()

        return PlaywrightResponse(content=original_html,
                                  html=html,
                                  status_code=status_code,
                                  exception_list=exception_list,
                                  error_list=total_error_list,
                                  extra_result=extra_result)
