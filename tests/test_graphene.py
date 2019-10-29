import pytest

try:
    import graphene
except ImportError:
    graphene = None

if graphene:

    class Query(graphene.ObjectType):
        test = graphene.Float()
        abc = graphene.String()

        def resolve_test(self, info):
            return 70.5

        def resolve_abc(self, info):
            return "string_abc"

    schema = graphene.Schema(query=Query)

    class TestGraphene:
        @pytest.fixture
        def view_kwargs(self, view_kwargs):
            view_kwargs.update(schema=schema)
            return view_kwargs

        @pytest.mark.asyncio
        async def test_schema(self, client, url_builder):
            response = await client.get(url_builder(query="{test, abc}"))

            assert response.status == 200
            assert await response.json() == {
                "data": {"abc": "string_abc", "test": 70.5}
            }
