from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ai_config import AiConfig
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ai/config",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AiConfig | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = AiConfig.from_dict(response.json())

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

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AiConfig | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[AiConfig | ErrorResponse]:
    """Read the AI assistant configuration

     Reports whether the AI assistant is configured and which protocol versions this server speaks. A
    client reads 'currentProtocolVersion' at start-up and either matches it or picks the highest version
    it shares with 'supportedProtocolVersions'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AiConfig | ErrorResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> AiConfig | ErrorResponse | None:
    """Read the AI assistant configuration

     Reports whether the AI assistant is configured and which protocol versions this server speaks. A
    client reads 'currentProtocolVersion' at start-up and either matches it or picks the highest version
    it shares with 'supportedProtocolVersions'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AiConfig | ErrorResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[AiConfig | ErrorResponse]:
    """Read the AI assistant configuration

     Reports whether the AI assistant is configured and which protocol versions this server speaks. A
    client reads 'currentProtocolVersion' at start-up and either matches it or picks the highest version
    it shares with 'supportedProtocolVersions'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AiConfig | ErrorResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> AiConfig | ErrorResponse | None:
    """Read the AI assistant configuration

     Reports whether the AI assistant is configured and which protocol versions this server speaks. A
    client reads 'currentProtocolVersion' at start-up and either matches it or picks the highest version
    it shares with 'supportedProtocolVersions'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AiConfig | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
