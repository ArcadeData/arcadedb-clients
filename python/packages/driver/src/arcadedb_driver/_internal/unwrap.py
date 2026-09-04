"""The single bridge from the generated client's non-throwing `Response` to the throwing facade.

One function serves BOTH facades: `sync_detailed` and `asyncio_detailed` return the
same `Response[T]`, so nothing here is transport-specific.

It lives in `_internal/` rather than being re-exported from `__init__.py` to break
an import cycle: `__init__.py` builds the server and database classes out of the
`facade/` functions, and `facade/` needs `unwrap` too.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

from .._generated.types import Response
from ..errors import ArcadeDBError

T = TypeVar("T")


def is_success(response: Response[Any]) -> bool:
    """True when the status is 2xx."""
    return 200 <= int(response.status_code) < 300


def unwrap(response: Response[T]) -> T:
    """Returns `parsed` on success; raises `ArcadeDBError` on any non-2xx response.

    `parsed` is `None` for the 204 endpoints (begin/commit/rollback, ts.write), and
    that `None` is returned rather than treated as a failure.
    """
    if not is_success(response):
        raise ArcadeDBError.from_response(response)
    return cast("T", response.parsed)
