from http import HTTPStatus
from typing import Any

import pytest
from arcadedb_driver._generated.types import Response
from arcadedb_driver._internal.unwrap import unwrap
from arcadedb_driver.errors import ArcadeDBError


def make_response(status: int, content: bytes = b"", headers: dict[str, str] | None = None) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(status),
        content=content,
        headers=headers or {},
        parsed=None,
    )


def test_carries_every_field_the_body_supplied() -> None:
    err = ArcadeDBError(
        400,
        {
            "error": "Encountered an error",
            "exception": "com.arcadedb.SomeException",
            "detail": "line 1",
            "requestId": "abc-123",
            "help": "check the syntax",
            "exceptionArgs": "arg",
        },
    )
    assert err.status == 400
    assert err.error == "Encountered an error"
    assert err.exception == "com.arcadedb.SomeException"
    assert err.detail == "line 1"
    assert err.request_id == "abc-123"
    assert err.help_ == "check the syntax"
    assert err.exception_args == "arg"
    assert str(err) == "Encountered an error"


def test_falls_back_through_detail_then_status_for_the_message() -> None:
    assert str(ArcadeDBError(500, {"detail": "boom"})) == "boom"
    assert str(ArcadeDBError(503)) == "ArcadeDB request failed with status 503"


@pytest.mark.parametrize("body", [None, "not an object", 42, [1, 2, 3], b"\xff\xfe"])
def test_parsing_never_raises_on_a_body_that_is_not_an_object(body: object) -> None:
    # This runs on the failure path. An error class that can itself fail turns a
    # server error into a confusing client-side crash.
    err = ArcadeDBError(500, body)
    assert err.status == 500
    assert err.error is None


def test_reads_the_request_id_from_the_header_when_the_body_has_none() -> None:
    response = make_response(404, b'{"error":"not found"}', {"X-Request-Id": "hdr-9"})
    err = ArcadeDBError.from_response(response)
    assert err.error == "not found"
    assert err.request_id == "hdr-9"


def test_survives_an_unparsable_error_body() -> None:
    response = make_response(500, b"<html>gateway timeout</html>")
    err = ArcadeDBError.from_response(response)
    assert err.status == 500
    assert err.error is None


def test_unwrap_returns_parsed_on_success() -> None:
    response = Response(status_code=HTTPStatus(200), content=b"{}", headers={}, parsed={"ok": True})
    assert unwrap(response) == {"ok": True}


def test_unwrap_raises_on_a_non_2xx() -> None:
    response = make_response(409, b'{"error":"conflict"}')
    with pytest.raises(ArcadeDBError) as caught:
        unwrap(response)
    assert caught.value.status == 409
    assert caught.value.error == "conflict"


def test_unwrap_accepts_a_204_with_no_body() -> None:
    assert unwrap(make_response(204)) is None
