from urllib.parse import urlencode

from aiohttp import web
import aiohttp.test_utils
import pytest

from aiohttp_graphql import GraphQLView


# GraphQLView Fixtures
@pytest.fixture
def view_kwargs():
    return {}


# aiohttp Fixtures
@pytest.fixture
def app(view_kwargs):
    app = web.Application()
    GraphQLView.attach(app, **view_kwargs)
    return app


@pytest.fixture
async def client(app):
    srv = aiohttp.test_utils.TestServer(app)
    client = aiohttp.test_utils.TestClient(srv)
    await client.start_server()
    yield client
    await client.close()


# URL Fixtures
@pytest.fixture
def base_url():
    return "/graphql"


@pytest.fixture
def base_url_subscriptions():
    return "/subscriptions"


@pytest.fixture
def url_builder(base_url):
    def builder(**url_params):
        if url_params:
            return "{}?{}".format(base_url, urlencode(url_params))
        return base_url

    return builder
