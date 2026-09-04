import json
from typing import Any

import httpx
import pytest
import respx
from arcadedb_driver import ArcadeDBError, ArcadeDBServer, basic_auth

BASE_URL = "http://db.test"


def server() -> ArcadeDBServer:
    return ArcadeDBServer(base_url=BASE_URL, auth=basic_auth("root", "playwithdata"))


@respx.mock
def test_query_returns_the_whole_envelope() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"name": "Ada"}], "limit": 100, "returned": 1, "truncated": False},
        )
    )
    with server() as srv:
        env = srv.db("mydb").query(language="sql", command="SELECT FROM Person")

    assert env.result == [{"name": "Ada"}]
    assert env.limit == 100
    assert env.returned == 1
    assert env.truncated is False
    assert route.calls.last.request.headers["Authorization"].startswith("Basic ")


@respx.mock
def test_query_defaults_every_omitted_envelope_field() -> None:
    # QueryResponse has no `required` list in the contract, so all four fields are
    # technically optional. The defaults assert a completeness the server never
    # claimed - which is the most reassuring reading of "the server did not say",
    # and identical to what @arcadedb/driver's toEnvelope does.
    respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(return_value=httpx.Response(200, json={}))
    with server() as srv:
        env = srv.db("mydb").query(language="sql", command="SELECT 1")

    assert env.result == []
    assert env.limit == -1
    assert env.returned == 0
    assert env.truncated is False


@respx.mock
def test_query_sends_params_and_limit_only_when_supplied() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(return_value=httpx.Response(200, json={"result": []}))
    with server() as srv:
        srv.db("mydb").query(language="sql", command="SELECT FROM P WHERE age > :min", params={"min": 18}, limit=5)
        srv.db("mydb").query(language="sql", command="SELECT 1")

    with_opts: dict[str, Any] = json.loads(route.calls[0].request.read())
    without: dict[str, Any] = json.loads(route.calls[1].request.read())
    assert with_opts["params"] == {"min": 18}
    assert with_opts["limit"] == 5
    assert "params" not in without
    assert "limit" not in without


@respx.mock
def test_command_sends_language_as_a_required_field() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(200, json={"result": [], "returned": 0})
    )
    with server() as srv:
        srv.db("mydb").command(language="sql", command="INSERT INTO Person SET name = 'Ada'")

    body = json.loads(route.calls.last.request.read())
    assert body["language"] == "sql"
    assert body["command"] == "INSERT INTO Person SET name = 'Ada'"


@respx.mock
def test_a_non_2xx_raises_arcadedb_error_with_the_servers_detail() -> None:
    respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(
            400,
            json={"error": "Invalid query", "detail": "line 1:8"},
            headers={"X-Request-Id": "req-77"},
        )
    )
    with server() as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").query(language="sql", command="SELCT 1")

    assert caught.value.status == 400
    assert caught.value.error == "Invalid query"
    assert caught.value.detail == "line 1:8"
    assert caught.value.request_id == "req-77"


@respx.mock
def test_raw_does_not_raise() -> None:
    # The deliberate asymmetry: the facade throws, `.raw` never does.
    from arcadedb_driver._generated.api.database import list_databases

    respx.get(f"{BASE_URL}/api/v1/databases").mock(return_value=httpx.Response(500, json={"error": "boom"}))
    with server() as srv:
        response = list_databases.sync_detailed(client=srv.raw)

    assert response.status_code == 500
