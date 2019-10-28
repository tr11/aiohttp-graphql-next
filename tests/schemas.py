import asyncio

from graphql.type.definition import (
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
)
from graphql.type.scalars import GraphQLString
from graphql.type.schema import GraphQLSchema


def resolve_raises(*args):
    raise Exception("Throws!")


def resolve_test(obj, info, **args):
    return "Hello %s" % (args.get("who") or "World")


def resolve_request(obj, info, *args):
    print(info)
    print(info.context)
    return info.context["request"].query.get("q")


# Sync schema
QueryRootType = GraphQLObjectType(
    name="QueryRoot",
    fields={
        "thrower": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_raises),
        "request": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_request),
        "context": GraphQLField(
            GraphQLNonNull(GraphQLString),
            resolve=lambda obj, info, *args: str(info.context),
        ),
        "test": GraphQLField(
            type_=GraphQLString,
            args={"who": GraphQLArgument(GraphQLString)},
            resolve=resolve_test,
        ),
    },
)


MutationRootType = GraphQLObjectType(
    name="MutationRoot",
    fields={
        "writeTest": GraphQLField(
            type_=QueryRootType, resolve=lambda *args: QueryRootType
        )
    },
)


async def resolve_fn(event, _info):
    return event


async def subscribe_subs(*args):
    vals = "abcdefghijkl"
    for v in vals:
        await asyncio.sleep(0.001)
        yield v


SubscriptionsRootType = GraphQLObjectType(
    name="SubscriptionsRoot",
    fields={
        "subscriptionsTest": GraphQLField(
            type_=GraphQLString, resolve=resolve_fn, subscribe=subscribe_subs
        )
    },
)


Schema = GraphQLSchema(QueryRootType, MutationRootType, SubscriptionsRootType)


# Schema with async methods
async def resolver(context, *args):
    await asyncio.sleep(0.001)
    return "hey"


async def resolver_2(context, *args):
    await asyncio.sleep(0.003)
    return "hey2"


def resolver_3(context, *args):
    return "hey3"


AsyncQueryType = GraphQLObjectType(
    "AsyncQueryType",
    {
        "a": GraphQLField(GraphQLString, resolve=resolver),
        "b": GraphQLField(GraphQLString, resolve=resolver_2),
        "c": GraphQLField(GraphQLString, resolve=resolver_3),
    },
)


AsyncSchema = GraphQLSchema(AsyncQueryType)
