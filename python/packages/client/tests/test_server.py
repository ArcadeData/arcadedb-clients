import httpx
import pytest
import respx
from arcadedb_client import ArcadeDBError, ArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_list_databases_returns_names() -> None:
    respx.get(f"{BASE_URL}/api/v1/databases").mock(return_value=httpx.Response(200, json={"result": ["one", "two"]}))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.list_databases() == ["one", "two"]


@respx.mock
def test_list_databases_defaults_an_omitted_result_to_empty() -> None:
    respx.get(f"{BASE_URL}/api/v1/databases").mock(return_value=httpx.Response(200, json={}))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.list_databases() == []


@respx.mock
def test_exists_returns_the_servers_answer() -> None:
    respx.get(f"{BASE_URL}/api/v1/exists/mydb").mock(return_value=httpx.Response(200, json={"result": True}))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.exists("mydb") is True


@respx.mock
def test_ready_returns_false_on_503_and_raises_on_anything_else() -> None:
    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(503))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.ready() is False

    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.ready() is True

    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(500, json={"error": "x"}))
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError):
        srv.ready()


@respx.mock
def test_health_raises_when_the_server_does_not_answer_204() -> None:
    respx.get(f"{BASE_URL}/api/v1/health").mock(return_value=httpx.Response(500, json={"error": "down"}))
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError):
        srv.health()
