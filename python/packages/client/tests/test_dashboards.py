import httpx
import pytest
import respx
from arcadedb_client import ArcadeDBError, ArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_promql_labels_returns_the_generated_model() -> None:
    respx.get(f"{BASE_URL}/api/v1/ts/mydb/prom/api/v1/labels").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": ["__name__", "host"]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").promql.labels()

    assert result.data == ["__name__", "host"]


@respx.mock
def test_grafana_query_reaches_the_right_route() -> None:
    # `grafana.query` is hand-written for the same reason as `db.ts.query`/`db.ts.latest`
    # (see facade/timeseries.py's module docstring): the contract types
    # `GrafanaQueryResponse`'s per-element DataFrame values as `"type": "object"`, so
    # it returns the parsed JSON body directly instead of the generated model.
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/grafana/query").mock(
        return_value=httpx.Response(200, json={"results": {}})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").grafana.query(body={"targets": []})

    assert route.called
    assert result == {"results": {}}


@respx.mock
def test_grafana_query_raises_on_a_non_2xx() -> None:
    respx.post(f"{BASE_URL}/api/v1/ts/mydb/grafana/query").mock(
        return_value=httpx.Response(400, json={"error": "unknown time-series type"})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").grafana.query(body={"targets": [{"type": "does-not-exist"}]})

    assert caught.value.error == "unknown time-series type"


@respx.mock
def test_the_namespaces_are_cached_per_database_handle() -> None:
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        db = srv.db("mydb")
        assert db.ts is db.ts
        assert db.grafana is db.grafana
        assert db.promql is db.promql
