import httpx
import pytest
import respx
from arcadedb_client import ArcadeDBError, ArcadeDBServer, AsyncArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_write_posts_line_protocol_as_text_plain() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("mydb").ts.write(line_protocol="cpu,host=a value=0.9 1700000000000000000")

    request = route.calls.last.request
    assert request.headers["Content-Type"].startswith("text/plain")
    assert request.read() == b"cpu,host=a value=0.9 1700000000000000000"
    assert "precision" not in str(request.url)


@respx.mock
def test_write_sends_precision_when_supplied() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("mydb").ts.write(line_protocol="cpu value=1 1700000000000", precision="ms")

    assert "precision=ms" in str(route.calls.last.request.url)


@respx.mock
def test_write_raises_on_a_non_2xx() -> None:
    respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(
        return_value=httpx.Response(400, json={"error": "bad line protocol"})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").ts.write(line_protocol="garbage")

    assert caught.value.error == "bad line protocol"


@respx.mock
def test_query_returns_the_parsed_json_body_unaltered() -> None:
    # The contract types this response's scalar column values (a timestamp, a
    # numeric measurement) as `"type": "object"`, which makes the generated
    # response model misparse (silently, for the raw shape - see
    # facade/timeseries.py's module docstring) every realistic response. `query`
    # bypasses that generated parsing and hands back the parsed JSON body as-is.
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/query").mock(
        return_value=httpx.Response(200, json={"rows": [[1700000000000, 0.9]]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").ts.query(body={"type": "cpu"})

    assert result == {"rows": [[1700000000000, 0.9]]}
    assert route.calls.last.request.headers["Content-Type"].startswith("application/json")


@respx.mock
def test_query_raises_on_a_non_2xx() -> None:
    respx.post(f"{BASE_URL}/api/v1/ts/mydb/query").mock(
        return_value=httpx.Response(400, json={"error": "unknown time-series type"})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").ts.query(body={"type": "does-not-exist"})

    assert caught.value.error == "unknown time-series type"


@respx.mock
def test_latest_returns_the_parsed_json_body_and_translates_type_to_the_query_parameter() -> None:
    # Same bypass as `query`, for the same reason: `TimeSeriesLatestResponse.latest`
    # types its scalar values as `"type": "object"` too, and the generated model has
    # no fallback branch, so it raises `TypeError` outright on an ordinary response.
    route = respx.get(f"{BASE_URL}/api/v1/ts/mydb/latest").mock(
        return_value=httpx.Response(200, json={"latest": [1700000000000, 0.9]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").ts.latest(type_="cpu", tag="host=a")

    assert result == {"latest": [1700000000000, 0.9]}
    request = route.calls.last.request
    assert "type=cpu" in str(request.url)
    assert "tag=host" in str(request.url)


@respx.mock
def test_latest_raises_on_a_non_2xx() -> None:
    respx.get(f"{BASE_URL}/api/v1/ts/mydb/latest").mock(
        return_value=httpx.Response(404, json={"error": "unknown time-series type"})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").ts.latest(type_="does-not-exist")

    assert caught.value.error == "unknown time-series type"


@respx.mock
def test_write_escapes_a_database_name_needing_it() -> None:
    # `ArcadeDBServer.db(name)` accepts an arbitrary caller-supplied string with no
    # sanitisation. A name containing `/` must be percent-encoded on the wire - not
    # left to act as a path separator - the same property `quote(..., safe="")`
    # gives every generated operation (see e.g. query_time_series.py).
    route = respx.post(f"{BASE_URL}/api/v1/ts/a%2Fb/write").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("a/b").ts.write(line_protocol="cpu value=1 1700000000000")

    assert route.called
    assert route.calls.last.request.url.raw_path == b"/api/v1/ts/a%2Fb/write"


@pytest.mark.asyncio
@respx.mock
async def test_async_write_posts_line_protocol() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        await srv.db("mydb").ts.write(line_protocol="cpu value=1 1700000000000")

    assert route.calls.last.request.headers["Content-Type"].startswith("text/plain")
