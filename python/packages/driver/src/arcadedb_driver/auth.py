"""Authentication headers for `ArcadeDBServer` and `AsyncArcadeDBServer`.

Both return a plain header mapping, passed to the server constructor's `auth`
argument. The generated `AuthenticatedClient` is deliberately not used: its
token-and-prefix model fits bearer but not basic, and one uniform mechanism for
both is simpler than two.

`@arcadedb/driver`'s `auth.ts` spends sixty lines on `TextEncoder`, chunking, and
commentary because `btoa` mangles credentials above U+00FF and a spread call blows
the stack on a large one. `base64.b64encode` takes bytes and has neither hazard.
Do not port that workaround; there is no problem here for it to solve.
"""

from __future__ import annotations

import base64


def basic_auth(user: str, password: str) -> dict[str, str]:
    """HTTP Basic auth, per RFC 7617: `user:password` as UTF-8, then base64."""
    credential = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {credential}"}


def bearer_auth(token: str) -> dict[str, str]:
    """Bearer token auth, for session tokens from `/api/v1/login` (prefixed `AU-`) or any other bearer credential."""
    return {"Authorization": f"Bearer {token}"}
