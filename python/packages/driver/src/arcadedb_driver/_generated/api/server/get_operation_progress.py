from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.progress_response import ProgressResponse
from ...types import Response


def _get_kwargs(
    database: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/progress/{database}".format(
            database=quote(str(database), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ProgressResponse | None:
    if response.status_code == 200:
        response_200 = ProgressResponse.from_dict(response.json())

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

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ProgressResponse]:
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
) -> Response[ErrorResponse | ProgressResponse]:
    """List in-progress maintenance operations

     Returns the long-running maintenance operations currently running on this server for one database,
    with their step-by-step progress. Reads a lock-free snapshot: no database access and no transaction,
    so polling at any frequency is safe and cannot interfere with the operation being watched.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ProgressResponse]
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
) -> ErrorResponse | ProgressResponse | None:
    """List in-progress maintenance operations

     Returns the long-running maintenance operations currently running on this server for one database,
    with their step-by-step progress. Reads a lock-free snapshot: no database access and no transaction,
    so polling at any frequency is safe and cannot interfere with the operation being watched.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ProgressResponse
    """

    return sync_detailed(
        database=database,
        client=client,
    ).parsed


async def asyncio_detailed(
    database: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | ProgressResponse]:
    """List in-progress maintenance operations

     Returns the long-running maintenance operations currently running on this server for one database,
    with their step-by-step progress. Reads a lock-free snapshot: no database access and no transaction,
    so polling at any frequency is safe and cannot interfere with the operation being watched.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ProgressResponse]
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
) -> ErrorResponse | ProgressResponse | None:
    """List in-progress maintenance operations

     Returns the long-running maintenance operations currently running on this server for one database,
    with their step-by-step progress. Reads a lock-free snapshot: no database access and no transaction,
    so polling at any frequency is safe and cannot interfere with the operation being watched.

    Args:
        database (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ProgressResponse
    """

    return (
        await asyncio_detailed(
            database=database,
            client=client,
        )
    ).parsed
