from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.get_database_snapshot_checksums_response_200 import GetDatabaseSnapshotChecksumsResponse200
from ...types import Response


def _get_kwargs(
    database: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ha/snapshot/{database}/checksums".format(
            database=quote(str(database), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | GetDatabaseSnapshotChecksumsResponse200 | None:
    if response.status_code == 200:
        response_200 = GetDatabaseSnapshotChecksumsResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ErrorResponse.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | GetDatabaseSnapshotChecksumsResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    database: str,
    *,
    client: AuthenticatedClient,
) -> Response[ErrorResponse | GetDatabaseSnapshotChecksumsResponse200]:
    r"""Read the checksums of a snapshot's files

     Returns the per-file checksums of the database as a snapshot download would produce it, read through
    the same point-in-time window. Only the root user may read them.

    This is an operator diagnostic: it answers \"do these two nodes hold the same bytes?\" without
    transferring a database. Resync itself does not consult it - a follower that falls behind the
    compacted Raft log always downloads the full snapshot ZIP - because a whole-file comparison is the
    wrong granularity for an ArcadeDB database, which is usually dominated by one bucket file that any
    single changed byte re-ships in full. Incremental resync is tracked as a page-level diff in #6115.

    This route accepts HTTP Basic only, for the same reason as the snapshot download.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | GetDatabaseSnapshotChecksumsResponse200]
    """

    kwargs = _get_kwargs(
        database=database,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    database: str,
    *,
    client: AuthenticatedClient,
) -> ErrorResponse | GetDatabaseSnapshotChecksumsResponse200 | None:
    r"""Read the checksums of a snapshot's files

     Returns the per-file checksums of the database as a snapshot download would produce it, read through
    the same point-in-time window. Only the root user may read them.

    This is an operator diagnostic: it answers \"do these two nodes hold the same bytes?\" without
    transferring a database. Resync itself does not consult it - a follower that falls behind the
    compacted Raft log always downloads the full snapshot ZIP - because a whole-file comparison is the
    wrong granularity for an ArcadeDB database, which is usually dominated by one bucket file that any
    single changed byte re-ships in full. Incremental resync is tracked as a page-level diff in #6115.

    This route accepts HTTP Basic only, for the same reason as the snapshot download.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | GetDatabaseSnapshotChecksumsResponse200
    """

    return sync_detailed(
        database=database,
        client=client,
    ).parsed


async def asyncio_detailed(
    database: str,
    *,
    client: AuthenticatedClient,
) -> Response[ErrorResponse | GetDatabaseSnapshotChecksumsResponse200]:
    r"""Read the checksums of a snapshot's files

     Returns the per-file checksums of the database as a snapshot download would produce it, read through
    the same point-in-time window. Only the root user may read them.

    This is an operator diagnostic: it answers \"do these two nodes hold the same bytes?\" without
    transferring a database. Resync itself does not consult it - a follower that falls behind the
    compacted Raft log always downloads the full snapshot ZIP - because a whole-file comparison is the
    wrong granularity for an ArcadeDB database, which is usually dominated by one bucket file that any
    single changed byte re-ships in full. Incremental resync is tracked as a page-level diff in #6115.

    This route accepts HTTP Basic only, for the same reason as the snapshot download.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | GetDatabaseSnapshotChecksumsResponse200]
    """

    kwargs = _get_kwargs(
        database=database,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    database: str,
    *,
    client: AuthenticatedClient,
) -> ErrorResponse | GetDatabaseSnapshotChecksumsResponse200 | None:
    r"""Read the checksums of a snapshot's files

     Returns the per-file checksums of the database as a snapshot download would produce it, read through
    the same point-in-time window. Only the root user may read them.

    This is an operator diagnostic: it answers \"do these two nodes hold the same bytes?\" without
    transferring a database. Resync itself does not consult it - a follower that falls behind the
    compacted Raft log always downloads the full snapshot ZIP - because a whole-file comparison is the
    wrong granularity for an ArcadeDB database, which is usually dominated by one bucket file that any
    single changed byte re-ships in full. Incremental resync is tracked as a page-level diff in #6115.

    This route accepts HTTP Basic only, for the same reason as the snapshot download.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | GetDatabaseSnapshotChecksumsResponse200
    """

    return (
        await asyncio_detailed(
            database=database,
            client=client,
        )
    ).parsed
