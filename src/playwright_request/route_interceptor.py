"""route interceptor file to control what we block from playwright requests"""
import logging
import re


class RouteInterceptor:
    """class able to intercept routes and block some of them
    Usage:
        ```
            ...
            page = browser.new_page()
            interceptor = RouteInterceptor().set_default_exclusions()
            ...
            page.route("**/*", interceptor.route_intercept)
            page.goto(URL)
        ```
    """
    DEBUG: bool = False
    BLOCK_RESOURCES: bool = True
    DEFAULT_RESOURCE_EXCLUSIONS = [
        'image', 'stylesheet', 'media', 'font', 'other'
    ]
    DEFAULT_KEYWORD_RE_EXCLUSIONS = [
        "airdog", "tracking", ".svg", ".gif", ".jpg", "a0.muscache.com"
    ]

    def __init__(self,
                 block_resources: bool = True,
                 resource_exclusions: list[str] or None = None,
                 keyword_re_exclusions: list[str] or None = None,
                 debug_mode: bool = False):
        """constructor for RouteInterceptor

        :param block_resources: flag to block or not
        :param resource_exclusions: a list of resources to be blocked if None use the default: RESOURCE_EXCLUSIONS
        :param keyword_re_exclusions: a list of regular expressions used to block outgoing urls, if None use the default: KEYWORD_EXCLUSIONS
        :param debug_mode: flag for debug mode
        """
        self.block_resources = block_resources
        self.resource_exclusions = resource_exclusions if resource_exclusions is not None else []
        self.keyword_re_exclusions = keyword_re_exclusions if keyword_re_exclusions is not None else []
        self.debug_mode = debug_mode

        self.keyword_regex_exclusions = [
            re.compile(x) for x in self.keyword_re_exclusions
        ]
        self.last_log_message: str = ""

    def set_default_resource_exclusions(self):
        """set default resource exclusions"""
        self.resource_exclusions = self.DEFAULT_RESOURCE_EXCLUSIONS
        return self

    def set_default_keyword_re_exclusions(self):
        """set default keyword regex exclusions"""
        self.keyword_re_exclusions = self.DEFAULT_KEYWORD_RE_EXCLUSIONS
        self.keyword_regex_exclusions = [
            re.compile(x) for x in self.keyword_re_exclusions
        ]
        return self

    def set_default_exclusions(self):
        """set both, resource and keyword exclusions"""
        self.set_default_resource_exclusions()
        self.set_default_keyword_re_exclusions()
        return self

    def block_on(self):
        """set block resources flag to True"""
        self.block_resources = True
        return self

    def block_off(self):
        """set block resources flag to False"""
        self.block_resources = False
        return self

    def route_intercept(self, route):
        """intercept route in order to detect and invalidate load images or other resources"""
        # 1. if not block, continue
        if not self.block_resources:
            self.last_log_message = ""
            return route.continue_()

        # 2. set initial message and exclusion flag as False
        message = ""
        exclusion_flag = False

        # A. detect if the resource type from route should be blocked
        if route.request.resource_type in self.resource_exclusions:
            exclusion_flag = True
            message = f"Blocking by resource type '{route.request.resource_type}' request to: {route.request.url}"
        else:
            # B. if not, try to detect a regex exlusion rule in the route url
            for key, regex in zip(self.keyword_re_exclusions,
                                  self.keyword_regex_exclusions):
                if regex.findall(route.request.url):
                    exclusion_flag = True
                    message = f"Blocking by keyword {route.request.url} as it contains key='{key}'"
                    # if found, break the loop
                    break

        self.last_log_message = message
        # C. if there is a detected exclusion
        if exclusion_flag:
            # print a log message and abort
            _ = logging.warning(message) if self.debug_mode else None
            return route.abort()

        # if nothing was detected continue the execution
        return route.continue_()
