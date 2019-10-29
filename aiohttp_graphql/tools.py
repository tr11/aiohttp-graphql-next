"""Tools for GraphQL."""

import os
from typing import Any, Dict, Optional

from aiohttp.web import Request, Response

from jinja2 import Template


class GraphQLTool:
    """Base class for GraphQL tools."""

    def __init__(self, url: str, endpoint: str = "/graphql"):
        """
        Init.

        :param url: tool URL
        :param endpoint: graphql endpoint to use
        """
        self.url = url
        self.endpoint = endpoint

    async def render(
        self,
        query: Optional[str],
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> Response:
        """Render the tool."""
        raise NotImplementedError()

    async def view(self, request: Request) -> Response:
        """Return an aiohttp view."""
        raise NotImplementedError()


class GraphiQL(GraphQLTool):
    """GraphiQL."""

    def __init__(
        self,
        url: str = "/graphql/graphiql",
        endpoint: str = "/graphql",
        *,
        template: Optional[str] = None
    ):
        """
        Init.

        :param url: tool URL
        :param endpoint: graphql endpoint to use
        :param template: custom HTML template
        """
        super().__init__(url, endpoint)
        if not template:
            template = open(
                os.path.join(os.path.dirname(__file__), "template_graphiql.html"), "r"
            ).read()

        self.template = Template(template)

    async def render(
        self,
        query: Optional[str],
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> Response:
        """Render the tool."""
        return Response(
            text=self.template.render(endpoint=self.endpoint), content_type="text/html"
        )

    async def view(self, request: Request) -> Response:
        """Return an aiohttp view."""
        return await self.render(None, None, None)


class GraphQLPlayground(GraphQLTool):
    """GraphQL Playground."""

    def __init__(
        self,
        url: str = "/graphql/playground",
        endpoint: str = "/graphql",
        *,
        template: Optional[str] = None
    ):
        """
        Init.

        :param url: tool URL
        :param endpoint: graphql endpoint to use
        :param template: custom HTML template
        """
        super().__init__(url, endpoint)
        if not template:
            template = open(
                os.path.join(os.path.dirname(__file__), "template_playground.html"), "r"
            ).read()

        self.template = Template(template)

    async def render(
        self,
        query: Optional[str],
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> Response:
        """Render the tool."""
        return Response(
            text=self.template.render(endpoint=self.endpoint), content_type="text/html"
        )

    async def view(self, request: Request) -> Response:
        """Return an aiohttp view."""
        return await self.render(None, None, None)


class GraphQLVoyager(GraphQLTool):
    """GraphQL Voyager."""

    def __init__(
        self,
        url: str = "/graphql/voyager",
        endpoint: str = "/graphql",
        *,
        template: Optional[str] = None
    ):
        """
        Init.

        :param url: tool URL
        :param endpoint: graphql endpoint to use
        :param template: custom HTML template
        """
        super().__init__(url, endpoint)
        if not template:
            template = open(
                os.path.join(os.path.dirname(__file__), "template_voyager.html"), "r"
            ).read()

        self.template = Template(template)

    async def render(
        self,
        query: Optional[str],
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> Response:
        """Render the tool."""
        return Response(
            text=self.template.render(endpoint=self.endpoint), content_type="text/html"
        )

    async def view(self, request: Request) -> Response:
        """Return an aiohttp view."""
        return await self.render(None, None, None)
