"""aiohttp GraphQL view package."""

from collections import Mapping
import json
from inspect import isawaitable
from typing import Any, Dict, List, Optional, Union, cast, Type, Awaitable

from aiohttp.web import Application, Request, Response

from graphql import (
    GraphQLSchema,
    # get_operation_ast,
    graphql,
    graphql_sync,
    ExecutionResult,
    GraphQLError,
    parse,
    get_operation_ast,
    validate_schema,
    execute,
    Source,
    GraphQLFieldResolver,
    GraphQLTypeResolver,
    ExecutionContext,
    validate,
    OperationType,
)
from graphql.execution import Middleware
from graphql.pyutils import AwaitableOrValue

from mypy_extensions import TypedDict


ResultDataSuccessType = TypedDict(
    "ResultDataSuccessType", {"data": Optional[Dict[str, Any]]}
)
ResultDataFailType = TypedDict("ResultDataFailType", {"errors": List[Dict[str, Any]]})
ResultDataType = Union[ResultDataSuccessType, ResultDataFailType]


class GraphQLView:
    """GraphQL aiohttp view."""

    def __init__(
        self,
        schema: Union[GraphQLSchema],
        asynchronous: bool = True,
        root_value: Any = None,
        context: Any = None,
        middleware: Middleware = None,
        max_age: int = 86400,
        pretty: bool = False,
        subscriptions: bool = False,
    ):  # noqa: D403
        """
        GraphQL init.

        :param schema:
        :param asynchronous:
        :param root_value:
        :param context:
        :param middleware:
        """
        self.schema = schema
        self.asynchronous = asynchronous
        self.root_value = root_value
        self.context = context
        self.middleware = middleware
        self.max_age = max_age
        self.pretty = pretty
        self.subscriptions = subscriptions

    def _graphql(
        self,
        schema: GraphQLSchema,
        document,
        root_value: Any = None,
        context_value: Any = None,
        variable_values: Dict[str, Any] = None,
        operation_name: str = None,
        field_resolver: GraphQLFieldResolver = None,
        type_resolver: GraphQLTypeResolver = None,
        middleware: Middleware = None,
        execution_context_class: Type[ExecutionContext] = ExecutionContext,
    ) -> AwaitableOrValue[ExecutionResult]:
        # Execute
        return execute(
            schema,
            document,
            root_value,
            context_value,
            variable_values,
            operation_name,
            field_resolver,
            type_resolver,
            middleware,
            execution_context_class,
        )

    async def __call__(self, request: Request) -> Response:
        """
        Run the GraphQL query provided.

        :param request: aiohttp Request
        :return: aiohttp Response
        """
        request_method = request.method.lower()
        try:
            variables = json.loads(request.query.get("variables", "{}"))
        except json.decoder.JSONDecodeError:
            return self.error_response("Variables are invalid JSON.")
        operation_name = request.query.get("operationName")

        if request_method == "options":
            return self.process_preflight(request)
        elif request_method == "post":
            try:
                data = await self.parse_body(request)
            except json.decoder.JSONDecodeError:
                return self.error_response("POST body sent invalid JSON.")
            operation_name = data.get("operationName", operation_name)
        elif request_method == "get":
            data = {"query": request.query.get("query")}
        else:
            return self.error_response(
                "GraphQL only supports GET and POST requests.",
                405,
                headers={"Allow": "GET, POST"},
            )

        vars_dyn = data.get("variables", {})
        variables.update(
            vars_dyn if isinstance(vars_dyn, dict) else json.loads(vars_dyn)
        )
        query = data.get("query")
        context = self.get_context(request)
        invalid = False

        print("DATA:", data)
        print("CONTEXT:", self.context)

        if not data.get("query"):
            return self.encode_response(
                request,
                ExecutionResult(
                    data=None,
                    errors=[GraphQLError(message="Must provide query string.")],
                ),
                invalid=True,
            )

        # Validate Schema
        schema_validation_errors = validate_schema(self.schema)
        if schema_validation_errors:
            return self.encode_response(
                request,
                ExecutionResult(data=None, errors=schema_validation_errors),
                invalid=True,
            )

        # Parse
        try:
            document = parse(query)
            op = get_operation_ast(document, operation_name)
            if op is None:
                invalid = True
            else:
                if request_method == "get" and op.operation != OperationType.QUERY:
                    return self.error_response(
                        "Can only perform a {} operation from a POST request.".format(
                            op.operation.value
                        ),
                        405,
                        headers={"Allow": "POST"},
                    )
        except GraphQLError as error:
            return self.encode_response(
                request, ExecutionResult(data=None, errors=[error]), invalid=True
            )
        except Exception as error:
            error = GraphQLError(str(error), original_error=error)
            return self.encode_response(
                request, ExecutionResult(data=None, errors=[error]), invalid=True
            )

        # Validate
        validation_errors = validate(self.schema, document)
        if validation_errors:
            return self.encode_response(
                request,
                ExecutionResult(data=None, errors=validation_errors),
                invalid=True,
            )

        print("PASSED VALIDATION")

        if self.asynchronous:
            result = self._graphql(
                self.schema,
                document=document,
                variable_values=variables,
                operation_name=operation_name,
                root_value=self.root_value,
                context_value=context,
                middleware=self.middleware,
            )
            if isawaitable(result):
                result = await cast(Awaitable[ExecutionResult], result)
        else:
            result = self._graphql(
                self.schema,
                document=document,
                variable_values=variables,
                operation_name=operation_name,
                root_value=self.root_value,
                context_value=context,
                middleware=self.middleware,
            )

        return self.encode_response(request, result, invalid=invalid)

    def encode_response(self, request, result, invalid: bool = False) -> Response:
        if result.errors:
            response: ResultDataType = cast(
                ResultDataFailType,
                {
                    "data": result.data,
                    "errors": [x.formatted for x in result.errors or []],
                },
            )
            if result.data is None and invalid:
                del response["data"]  # type: ignore
            for error in response["errors"]:  # type: ignore
                if error["locations"] is None:
                    del error["locations"]
                if error["path"] is None:
                    del error["path"]
        else:
            response = cast(ResultDataSuccessType, {"data": result.data})

        print(response, invalid)

        status_code = 200 if not invalid else 400

        return Response(
            text=self.json_encode(response, self.is_pretty(request)),
            status=status_code,
            content_type="application/json",
        )

    def error_response(self, message: str, status_code: int = 400, headers=None):
        return Response(
            text=json.dumps({"errors": [{"message": message}]}),
            status=status_code,
            content_type="application/json",
            headers=headers,
        )

    def get_context(self, request: Request) -> Mapping:
        if self.context and isinstance(self.context, Mapping):
            context = self.context.copy()
        else:
            context = {}

        if isinstance(context, Mapping) and "request" not in context:
            context.update({"request": request})
        return context

    def json_encode(self, response: Dict[str, Any], pretty: bool = False):
        if pretty:
            return json.dumps(response, indent=2)
        else:
            return json.dumps(response, separators=(",", ":"))

    def is_pretty(self, request):
        return any(
            [
                self.pretty,
                # self.is_tool(request),
                request.query.get("pretty"),
            ]
        )

    async def parse_body(self, request: Request) -> Dict[str, Any]:
        """Parse a POST request body."""
        if request.content_type == "application/graphql":
            r_text = await request.text()
            return {"query": r_text}

        elif request.content_type == "application/json":
            text = await request.text()
            return cast(Dict[str, Any], json.loads(text))

        elif request.content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            # TODO: seems like a multidict would be more appropriate
            # than casting it and de-duping variables. Alas, it's what
            # graphql-python wants.
            return dict(await request.post())

        return {}

    def process_preflight(self, request: Request) -> Response:
        """
        Preflight request support for apollo-client.

        https://www.w3.org/TR/cors/#resource-preflight-requests

        :param request: aiohttp Request
        :return: aiohttp Response
        """
        headers = request.headers
        origin = headers.get("Origin", "")
        method = headers.get("Access-Control-Request-Method", "").upper()
        accepted_methods = ["GET", "POST", "PUT", "DELETE"]
        if method and method in accepted_methods:
            return Response(
                status=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": ", ".join(accepted_methods),
                    "Access-Control-Max-Age": str(self.max_age),
                },
            )
        return Response(status=400)

    @classmethod
    def attach(  # type: ignore
        cls,
        app: Application,
        *,
        route_path: str = "/graphql",
        route_name: str = "graphql",
        **kwargs
    ) -> None:
        """Attach the GraphQL view to the aiohttp app."""
        instance = cls(**kwargs)

        async def view(*args, **kwargs):  # type: ignore
            return await instance(*args, **kwargs)

        app.router.add_route("*", route_path, view, name=route_name)
