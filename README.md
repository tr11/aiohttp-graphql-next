# aiohttp-graphql-next
> experimental library to add GraphQL support to aiohttp

Adds [GraphQL] support to your [aiohttp] application.

Based on the work on [aiohttp-graphql] by Devin Fee.

## Usage
Just use the `GraphQLView` view from `aiohttp_graphql`
```python
from aiohttp_graphql import GraphQLView
from aiohttp_graphql.tools import GraphiQL

GraphQLView.attach(app, route_path="/graphql", schema=Schema, tool=GraphiQL())
```
The command above adds a `/graphql` endpoint to the aiohttp app.
When ran in a browser, the endpoint will yield the GraphiQL tool.

You can disable the GraphiQL tool by passing `tool=None` or add more tools using the keyword `tools`:
```python
tools=[
    GraphiQL(),
    GraphQLPlayground(),
    GraphQLVoyager(),
],
```
Each selected tool will be added to a different endpoint (`/graphql/<tool>`), which may be changed using the `url` parameter. For example,
```python
tools=[
    GraphQLPlayground(url='/playground'),
],
```
will add the GraphQL Playground tool to the `/playground` endpoint.

## Notes
This library uses the `next` versions of `graphene` and `graphql-core`,
and adds functionality that used to exist only in the `graphql-server-core` library.


[GraphQL]: http://graphql.org/
[aiohttp]: https://github.com/aio-libs/aiohttp/
[aiohttp-graphql]: https://github.com/graphql-python/aiohttp-graphql
[websockets]: https://github.com/dfee/graphql-ws-next
[graphql-core]:  https://github.com/graphql-python/graphql-core-next




