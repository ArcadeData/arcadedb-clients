import base64

from arcadedb_driver.auth import basic_auth, bearer_auth


def test_basic_auth_encodes_user_and_password_as_rfc_7617() -> None:
    headers = basic_auth("root", "playwithdata")
    assert headers == {"Authorization": "Basic cm9vdDpwbGF5d2l0aGRhdGE="}


def test_basic_auth_encodes_non_ascii_credentials_as_utf8() -> None:
    # The TypeScript client needs 60 lines of TextEncoder plumbing for this case
    # because btoa throws above U+00FF. Python's b64encode takes bytes, so the
    # hazard does not exist here - this test pins that it stays correct anyway.
    headers = basic_auth("josé", "münchen")
    decoded = base64.b64decode(headers["Authorization"].removeprefix("Basic ")).decode("utf-8")
    assert decoded == "josé:münchen"


def test_basic_auth_handles_a_very_long_credential() -> None:
    # The TypeScript version blew the call stack here via String.fromCharCode(...bytes).
    headers = basic_auth("u", "x" * 200_000)
    assert headers["Authorization"].startswith("Basic ")


def test_bearer_auth_sets_the_authorization_header() -> None:
    assert bearer_auth("AU-abc123") == {"Authorization": "Bearer AU-abc123"}
