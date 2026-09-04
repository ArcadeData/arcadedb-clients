from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.invoke_mcp_body import InvokeMcpBody
from ...models.invoke_mcp_response_200 import InvokeMcpResponse200
from ...models.invoke_mcp_response_403 import InvokeMcpResponse403
from ...models.invoke_mcp_response_405 import InvokeMcpResponse405
from ...models.invoke_mcp_response_503 import InvokeMcpResponse503
from ...types import Response


def _get_kwargs(
    *,
    body: InvokeMcpBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/mcp",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | ErrorResponse
    | InvokeMcpResponse200
    | InvokeMcpResponse403
    | InvokeMcpResponse405
    | InvokeMcpResponse503
    | None
):
    if response.status_code == 200:
        response_200 = InvokeMcpResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = cast(Any, None)
        return response_202

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = InvokeMcpResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 405:
        response_405 = InvokeMcpResponse405.from_dict(response.json())

        return response_405

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = InvokeMcpResponse503.from_dict(response.json())

        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InvokeMcpBody,
) -> Response[
    Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503
]:
    """Exchange a JSON-RPC message with the MCP server

     Accepts one JSON-RPC 2.0 request, notification, or response, or a batch of them as a top-level
    array, and answers with the corresponding response. The method set and the parameter and result
    shapes for each method are defined by the Model Context Protocol specification, not by this API, so
    request and response bodies are not enumerated here.

    The route is always registered; when the MCP server is disabled the request is refused at request
    time with 503, which is what makes runtime toggling possible without a restart. A request carrying
    only notifications and/or responses receives 202 with no body, because JSON-RPC forbids replying to
    those. Every other outcome, including a JSON-RPC-level error such as an unknown method or a
    malformed request body, is reported inside a 200 response: JSON-RPC layers its own error reporting
    over the HTTP transport, so a non-200 status is reserved for transport-level failures such as
    missing credentials, a disallowed browser Origin, an unauthorized user, an unsupported HTTP method,
    or the server being disabled. Requires MCPPlugin: present in every standard distribution, absent
    from a custom build that excludes the MCP module.

    Args:
        body (InvokeMcpBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: InvokeMcpBody,
) -> (
    Any
    | ErrorResponse
    | InvokeMcpResponse200
    | InvokeMcpResponse403
    | InvokeMcpResponse405
    | InvokeMcpResponse503
    | None
):
    """Exchange a JSON-RPC message with the MCP server

     Accepts one JSON-RPC 2.0 request, notification, or response, or a batch of them as a top-level
    array, and answers with the corresponding response. The method set and the parameter and result
    shapes for each method are defined by the Model Context Protocol specification, not by this API, so
    request and response bodies are not enumerated here.

    The route is always registered; when the MCP server is disabled the request is refused at request
    time with 503, which is what makes runtime toggling possible without a restart. A request carrying
    only notifications and/or responses receives 202 with no body, because JSON-RPC forbids replying to
    those. Every other outcome, including a JSON-RPC-level error such as an unknown method or a
    malformed request body, is reported inside a 200 response: JSON-RPC layers its own error reporting
    over the HTTP transport, so a non-200 status is reserved for transport-level failures such as
    missing credentials, a disallowed browser Origin, an unauthorized user, an unsupported HTTP method,
    or the server being disabled. Requires MCPPlugin: present in every standard distribution, absent
    from a custom build that excludes the MCP module.

    Args:
        body (InvokeMcpBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InvokeMcpBody,
) -> Response[
    Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503
]:
    """Exchange a JSON-RPC message with the MCP server

     Accepts one JSON-RPC 2.0 request, notification, or response, or a batch of them as a top-level
    array, and answers with the corresponding response. The method set and the parameter and result
    shapes for each method are defined by the Model Context Protocol specification, not by this API, so
    request and response bodies are not enumerated here.

    The route is always registered; when the MCP server is disabled the request is refused at request
    time with 503, which is what makes runtime toggling possible without a restart. A request carrying
    only notifications and/or responses receives 202 with no body, because JSON-RPC forbids replying to
    those. Every other outcome, including a JSON-RPC-level error such as an unknown method or a
    malformed request body, is reported inside a 200 response: JSON-RPC layers its own error reporting
    over the HTTP transport, so a non-200 status is reserved for transport-level failures such as
    missing credentials, a disallowed browser Origin, an unauthorized user, an unsupported HTTP method,
    or the server being disabled. Requires MCPPlugin: present in every standard distribution, absent
    from a custom build that excludes the MCP module.

    Args:
        body (InvokeMcpBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: InvokeMcpBody,
) -> (
    Any
    | ErrorResponse
    | InvokeMcpResponse200
    | InvokeMcpResponse403
    | InvokeMcpResponse405
    | InvokeMcpResponse503
    | None
):
    """Exchange a JSON-RPC message with the MCP server

     Accepts one JSON-RPC 2.0 request, notification, or response, or a batch of them as a top-level
    array, and answers with the corresponding response. The method set and the parameter and result
    shapes for each method are defined by the Model Context Protocol specification, not by this API, so
    request and response bodies are not enumerated here.

    The route is always registered; when the MCP server is disabled the request is refused at request
    time with 503, which is what makes runtime toggling possible without a restart. A request carrying
    only notifications and/or responses receives 202 with no body, because JSON-RPC forbids replying to
    those. Every other outcome, including a JSON-RPC-level error such as an unknown method or a
    malformed request body, is reported inside a 200 response: JSON-RPC layers its own error reporting
    over the HTTP transport, so a non-200 status is reserved for transport-level failures such as
    missing credentials, a disallowed browser Origin, an unauthorized user, an unsupported HTTP method,
    or the server being disabled. Requires MCPPlugin: present in every standard distribution, absent
    from a custom build that excludes the MCP module.

    Args:
        body (InvokeMcpBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | InvokeMcpResponse200 | InvokeMcpResponse403 | InvokeMcpResponse405 | InvokeMcpResponse503
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
