from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.verify_database_response import VerifyDatabaseResponse
from ...types import Response


def _get_kwargs(
    database: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cluster/verify/{database}".format(
            database=quote(str(database), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | VerifyDatabaseResponse | None:
    if response.status_code == 200:
        response_200 = VerifyDatabaseResponse.from_dict(response.json())

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

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | VerifyDatabaseResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    database: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | VerifyDatabaseResponse]:
    """Checksum a database's files for comparison across peers

     Computes a per-file checksum of one database on this server. A follower returns only its own
    checksums; the leader additionally fans the same call out to every peer and reports a cluster-wide
    comparison in 'result'.Requires RaftHAPlugin: the route is registered on every server, but answers
    only where high availability is configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | VerifyDatabaseResponse]
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
    client: AuthenticatedClient | Client,
) -> ErrorResponse | VerifyDatabaseResponse | None:
    """Checksum a database's files for comparison across peers

     Computes a per-file checksum of one database on this server. A follower returns only its own
    checksums; the leader additionally fans the same call out to every peer and reports a cluster-wide
    comparison in 'result'.Requires RaftHAPlugin: the route is registered on every server, but answers
    only where high availability is configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | VerifyDatabaseResponse
    """

    return sync_detailed(
        database=database,
        client=client,
    ).parsed


async def asyncio_detailed(
    database: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | VerifyDatabaseResponse]:
    """Checksum a database's files for comparison across peers

     Computes a per-file checksum of one database on this server. A follower returns only its own
    checksums; the leader additionally fans the same call out to every peer and reports a cluster-wide
    comparison in 'result'.Requires RaftHAPlugin: the route is registered on every server, but answers
    only where high availability is configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | VerifyDatabaseResponse]
    """

    kwargs = _get_kwargs(
        database=database,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    database: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | VerifyDatabaseResponse | None:
    """Checksum a database's files for comparison across peers

     Computes a per-file checksum of one database on this server. A follower returns only its own
    checksums; the leader additionally fans the same call out to every peer and reports a cluster-wide
    comparison in 'result'.Requires RaftHAPlugin: the route is registered on every server, but answers
    only where high availability is configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | VerifyDatabaseResponse
    """

    return (
        await asyncio_detailed(
            database=database,
            client=client,
        )
    ).parsed
