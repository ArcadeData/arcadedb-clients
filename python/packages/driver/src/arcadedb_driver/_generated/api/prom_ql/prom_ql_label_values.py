from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.prom_ql_error_response import PromQLErrorResponse
from ...models.prom_ql_labels_response import PromQLLabelsResponse
from ...types import Response


def _get_kwargs(
    database: str,
    name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ts/{database}/prom/api/v1/label/{name}/values".format(
            database=quote(str(database), safe=""),
            name=quote(str(name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse | None:
    if response.status_code == 200:
        response_200 = PromQLLabelsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PromQLErrorResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    database: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse]:
    """List the values of one label

     Lists every value of one label name, sorted. Compatible with the Prometheus
    /api/v1/label/{name}/values endpoint. Querying '__name__' returns every time-series type name
    instead of scanning a tag column. Takes no filtering parameters: unlike Prometheus itself, this
    endpoint does not accept 'start', 'end', or 'match[]'.

    Args:
        database (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse]
    """

    kwargs = _get_kwargs(
        database=database,
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    database: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse | None:
    """List the values of one label

     Lists every value of one label name, sorted. Compatible with the Prometheus
    /api/v1/label/{name}/values endpoint. Querying '__name__' returns every time-series type name
    instead of scanning a tag column. Takes no filtering parameters: unlike Prometheus itself, this
    endpoint does not accept 'start', 'end', or 'match[]'.

    Args:
        database (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse
    """

    return sync_detailed(
        database=database,
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    database: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse]:
    """List the values of one label

     Lists every value of one label name, sorted. Compatible with the Prometheus
    /api/v1/label/{name}/values endpoint. Querying '__name__' returns every time-series type name
    instead of scanning a tag column. Takes no filtering parameters: unlike Prometheus itself, this
    endpoint does not accept 'start', 'end', or 'match[]'.

    Args:
        database (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse]
    """

    kwargs = _get_kwargs(
        database=database,
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    database: str,
    name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse | None:
    """List the values of one label

     Lists every value of one label name, sorted. Compatible with the Prometheus
    /api/v1/label/{name}/values endpoint. Querying '__name__' returns every time-series type name
    instead of scanning a tag column. Takes no filtering parameters: unlike Prometheus itself, this
    endpoint does not accept 'start', 'end', or 'match[]'.

    Args:
        database (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PromQLErrorResponse | PromQLLabelsResponse
    """

    return (
        await asyncio_detailed(
            database=database,
            name=name,
            client=client,
        )
    ).parsed
