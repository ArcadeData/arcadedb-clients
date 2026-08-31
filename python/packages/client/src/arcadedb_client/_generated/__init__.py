"""A client library for accessing ArcadeDB HTTP API"""

from .client import AuthenticatedClient, Client

__all__ = (
    "AuthenticatedClient",
    "Client",
)
