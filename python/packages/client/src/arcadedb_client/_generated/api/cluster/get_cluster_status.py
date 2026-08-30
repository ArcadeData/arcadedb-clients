from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_status import ClusterStatus
from ...models.error_response import ErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    presence: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["presence"] = presence

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/cluster",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ClusterStatus | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = ClusterStatus.from_dict(response.json())

        return response_200

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
) -> Response[ClusterStatus | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    presence: bool | Unset = UNSET,
) -> Response[ClusterStatus | ErrorResponse]:
    """Read cluster and replication status

     Reports this server's Raft role, the current leader, and per-peer replication health including match
    and next index, lag, and round-trip latency. Answers 503 until Raft has started, because the route
    is registered before the Raft server comes up.

    The cluster and peer fields are server-level and readable by any authenticated user. The 'databases'
    array and the database-scoped 'alerts' are restricted to the databases the caller is authorized for,
    so a user granted one database does not learn the others.Requires RaftHAPlugin: the route is
    registered on every server, but answers only where high availability is configured.

    Args:
        presence (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterStatus | ErrorResponse]
    """

    kwargs = _get_kwargs(
        presence=presence,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    presence: bool | Unset = UNSET,
) -> ClusterStatus | ErrorResponse | None:
    """Read cluster and replication status

     Reports this server's Raft role, the current leader, and per-peer replication health including match
    and next index, lag, and round-trip latency. Answers 503 until Raft has started, because the route
    is registered before the Raft server comes up.

    The cluster and peer fields are server-level and readable by any authenticated user. The 'databases'
    array and the database-scoped 'alerts' are restricted to the databases the caller is authorized for,
    so a user granted one database does not learn the others.Requires RaftHAPlugin: the route is
    registered on every server, but answers only where high availability is configured.

    Args:
        presence (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterStatus | ErrorResponse
    """

    return sync_detailed(
        client=client,
        presence=presence,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    presence: bool | Unset = UNSET,
) -> Response[ClusterStatus | ErrorResponse]:
    """Read cluster and replication status

     Reports this server's Raft role, the current leader, and per-peer replication health including match
    and next index, lag, and round-trip latency. Answers 503 until Raft has started, because the route
    is registered before the Raft server comes up.

    The cluster and peer fields are server-level and readable by any authenticated user. The 'databases'
    array and the database-scoped 'alerts' are restricted to the databases the caller is authorized for,
    so a user granted one database does not learn the others.Requires RaftHAPlugin: the route is
    registered on every server, but answers only where high availability is configured.

    Args:
        presence (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterStatus | ErrorResponse]
    """

    kwargs = _get_kwargs(
        presence=presence,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    presence: bool | Unset = UNSET,
) -> ClusterStatus | ErrorResponse | None:
    """Read cluster and replication status

     Reports this server's Raft role, the current leader, and per-peer replication health including match
    and next index, lag, and round-trip latency. Answers 503 until Raft has started, because the route
    is registered before the Raft server comes up.

    The cluster and peer fields are server-level and readable by any authenticated user. The 'databases'
    array and the database-scoped 'alerts' are restricted to the databases the caller is authorized for,
    so a user granted one database does not learn the others.Requires RaftHAPlugin: the route is
    registered on every server, but answers only where high availability is configured.

    Args:
        presence (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterStatus | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            presence=presence,
        )
    ).parsed
