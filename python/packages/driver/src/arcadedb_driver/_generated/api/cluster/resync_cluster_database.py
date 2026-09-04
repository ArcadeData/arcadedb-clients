from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_action_response import ClusterActionResponse
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs(
    database: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cluster/resync/{database}".format(
            database=quote(str(database), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ClusterActionResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = ClusterActionResponse.from_dict(response.json())

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
) -> Response[ClusterActionResponse | ErrorResponse]:
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
) -> Response[ClusterActionResponse | ErrorResponse]:
    """Re-fetch a database from the leader

     Discards this server's copy of one database and installs a fresh snapshot from the leader. Refuses
    to run on the leader itself. Answers 503 when no leader is currently reachable.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterActionResponse | ErrorResponse]
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
) -> ClusterActionResponse | ErrorResponse | None:
    """Re-fetch a database from the leader

     Discards this server's copy of one database and installs a fresh snapshot from the leader. Refuses
    to run on the leader itself. Answers 503 when no leader is currently reachable.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterActionResponse | ErrorResponse
    """

    return sync_detailed(
        database=database,
        client=client,
    ).parsed


async def asyncio_detailed(
    database: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ClusterActionResponse | ErrorResponse]:
    """Re-fetch a database from the leader

     Discards this server's copy of one database and installs a fresh snapshot from the leader. Refuses
    to run on the leader itself. Answers 503 when no leader is currently reachable.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterActionResponse | ErrorResponse]
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
) -> ClusterActionResponse | ErrorResponse | None:
    """Re-fetch a database from the leader

     Discards this server's copy of one database and installs a fresh snapshot from the leader. Refuses
    to run on the leader itself. Answers 503 when no leader is currently reachable.Requires
    RaftHAPlugin: the route is registered on every server, but answers only where high availability is
    configured.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterActionResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            database=database,
            client=client,
        )
    ).parsed
