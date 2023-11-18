"""file with the methods to test route interceptor class"""
from unittest.mock import MagicMock

from playwright_request.route_interceptor import RouteInterceptor


def test_constructor_and_default_methods():
    """test constructor and all default methods"""
    # 1. different ways to set defaults
    blocker1 = RouteInterceptor().set_default_resource_exclusions(
    ).set_default_keyword_re_exclusions()
    blocker2 = RouteInterceptor().set_default_exclusions()
    blocker3 = RouteInterceptor()
    blocker3.set_default_exclusions()

    assert blocker1.block_resources == blocker2.block_resources == blocker3.block_resources
    assert blocker1.resource_exclusions == blocker2.resource_exclusions == blocker3.resource_exclusions
    assert blocker1.keyword_re_exclusions == blocker2.keyword_re_exclusions == blocker3.keyword_re_exclusions

    # 2. test if block methods works as expected
    blocker1.block_on()
    assert blocker1.block_resources is True

    blocker1.block_off()
    assert blocker1.block_resources is False


def test_route_without_exclusion():
    """test route method without exclusion flag"""
    blocker = RouteInterceptor(block_resources=False)
    route = MagicMock()

    blocker.route_intercept(route=route)
    assert blocker.last_log_message == ""


def test_route_with_blocking_by_resource_type():
    """test route method with blocking by resource type"""
    # 1. define the interceptor with default resource exclusions
    blocker = RouteInterceptor(
        block_resources=True).set_default_resource_exclusions()

    # 2. simulate image request
    route = MagicMock()
    route.request.resource_type = "image"

    # 3. intercept the route
    blocker.route_intercept(route=route)
    assert "Blocking by resource type" in blocker.last_log_message


def test_route_with_blocking_by_url_keyword():
    """test route method with blocking by url exclusion"""
    # 1. define the interceptor with default resource exclusions
    blocker = RouteInterceptor(
        block_resources=True).set_default_keyword_re_exclusions()
    assert "a0.muscache.com" in blocker.keyword_re_exclusions

    # 2. simulate image request with one of the default keywords
    route = MagicMock()
    route.request.url = "https://a0.muscache.com/some/data"

    # 3. intercept the route
    blocker.route_intercept(route=route)
    assert "Blocking by keyword" in blocker.last_log_message


def test_route_with_no_blocking():
    """test route method with blocking by url exclusion"""
    # 1. define the interceptor with default resource exclusions
    blocker = RouteInterceptor(block_resources=True).set_default_exclusions()
    assert "image" in blocker.resource_exclusions
    assert "a0.muscache.com" in blocker.keyword_re_exclusions

    # 2. simulate a valid request from a valid url
    route = MagicMock()
    route.request.resource_type = "valid-resource-type"
    route.request.url = "https://valid/and/non/blocking/url"

    # 3. intercept the route
    blocker.route_intercept(route=route)
    assert blocker.last_log_message == ""
