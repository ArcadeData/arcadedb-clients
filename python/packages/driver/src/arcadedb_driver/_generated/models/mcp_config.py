from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mcp_config_databases import McpConfigDatabases
    from ..models.mcp_config_principal_profiles import McpConfigPrincipalProfiles


T = TypeVar("T", bound="McpConfig")


@_attrs_define
class McpConfig:
    """MCP server configuration

    Attributes:
        allow_admin (bool | Unset): Permit administrative operations
        allow_delete (bool | Unset): Permit deletes
        allow_insert (bool | Unset): Permit inserts
        allow_reads (bool | Unset): Permit read operations
        allow_schema_change (bool | Unset): Permit schema changes
        allow_update (bool | Unset): Permit updates
        allowed_origins (list[str] | Unset): Extra browser origins permitted for the HTTP transport, beyond loopback
            addresses which are always allowed. The value '*' permits any origin, disabling the anti-DNS-rebinding check.
        allowed_users (list[str] | Unset): Users permitted to reach the MCP server. The value '*' permits any
            authenticated user.
        databases (McpConfigDatabases | Unset): Per-database permission overrides, keyed by database name. Present only
            when at least one override is configured.
        enabled (bool | Unset): Whether the MCP server answers requests
        principal_profiles (McpConfigPrincipalProfiles | Unset): Tool profile assigned per principal (user or API token)
            name. Present only when at least one is configured.
        profile (str | Unset): Default tool profile: 'all', 'rag', or 'admin'
    """

    allow_admin: bool | Unset = UNSET
    allow_delete: bool | Unset = UNSET
    allow_insert: bool | Unset = UNSET
    allow_reads: bool | Unset = UNSET
    allow_schema_change: bool | Unset = UNSET
    allow_update: bool | Unset = UNSET
    allowed_origins: list[str] | Unset = UNSET
    allowed_users: list[str] | Unset = UNSET
    databases: McpConfigDatabases | Unset = UNSET
    enabled: bool | Unset = UNSET
    principal_profiles: McpConfigPrincipalProfiles | Unset = UNSET
    profile: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allow_admin = self.allow_admin

        allow_delete = self.allow_delete

        allow_insert = self.allow_insert

        allow_reads = self.allow_reads

        allow_schema_change = self.allow_schema_change

        allow_update = self.allow_update

        allowed_origins: list[str] | Unset = UNSET
        if not isinstance(self.allowed_origins, Unset):
            allowed_origins = self.allowed_origins

        allowed_users: list[str] | Unset = UNSET
        if not isinstance(self.allowed_users, Unset):
            allowed_users = self.allowed_users

        databases: dict[str, Any] | Unset = UNSET
        if not isinstance(self.databases, Unset):
            databases = self.databases.to_dict()

        enabled = self.enabled

        principal_profiles: dict[str, Any] | Unset = UNSET
        if not isinstance(self.principal_profiles, Unset):
            principal_profiles = self.principal_profiles.to_dict()

        profile = self.profile

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if allow_admin is not UNSET:
            field_dict["allowAdmin"] = allow_admin
        if allow_delete is not UNSET:
            field_dict["allowDelete"] = allow_delete
        if allow_insert is not UNSET:
            field_dict["allowInsert"] = allow_insert
        if allow_reads is not UNSET:
            field_dict["allowReads"] = allow_reads
        if allow_schema_change is not UNSET:
            field_dict["allowSchemaChange"] = allow_schema_change
        if allow_update is not UNSET:
            field_dict["allowUpdate"] = allow_update
        if allowed_origins is not UNSET:
            field_dict["allowedOrigins"] = allowed_origins
        if allowed_users is not UNSET:
            field_dict["allowedUsers"] = allowed_users
        if databases is not UNSET:
            field_dict["databases"] = databases
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if principal_profiles is not UNSET:
            field_dict["principalProfiles"] = principal_profiles
        if profile is not UNSET:
            field_dict["profile"] = profile

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mcp_config_databases import McpConfigDatabases
        from ..models.mcp_config_principal_profiles import McpConfigPrincipalProfiles

        d = dict(src_dict)
        allow_admin = d.pop("allowAdmin", UNSET)

        allow_delete = d.pop("allowDelete", UNSET)

        allow_insert = d.pop("allowInsert", UNSET)

        allow_reads = d.pop("allowReads", UNSET)

        allow_schema_change = d.pop("allowSchemaChange", UNSET)

        allow_update = d.pop("allowUpdate", UNSET)

        allowed_origins = cast(list[str], d.pop("allowedOrigins", UNSET))

        allowed_users = cast(list[str], d.pop("allowedUsers", UNSET))

        _databases = d.pop("databases", UNSET)
        databases: McpConfigDatabases | Unset
        if isinstance(_databases, Unset):
            databases = UNSET
        else:
            databases = McpConfigDatabases.from_dict(_databases)

        enabled = d.pop("enabled", UNSET)

        _principal_profiles = d.pop("principalProfiles", UNSET)
        principal_profiles: McpConfigPrincipalProfiles | Unset
        if isinstance(_principal_profiles, Unset):
            principal_profiles = UNSET
        else:
            principal_profiles = McpConfigPrincipalProfiles.from_dict(_principal_profiles)

        profile = d.pop("profile", UNSET)

        mcp_config = cls(
            allow_admin=allow_admin,
            allow_delete=allow_delete,
            allow_insert=allow_insert,
            allow_reads=allow_reads,
            allow_schema_change=allow_schema_change,
            allow_update=allow_update,
            allowed_origins=allowed_origins,
            allowed_users=allowed_users,
            databases=databases,
            enabled=enabled,
            principal_profiles=principal_profiles,
            profile=profile,
        )

        mcp_config.additional_properties = d
        return mcp_config

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
