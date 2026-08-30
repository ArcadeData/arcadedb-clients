from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="McpDatabaseOverride")


@_attrs_define
class McpDatabaseOverride:
    """Per-database permission override. Every field is optional; an omitted field inherits the server-wide value. A
    permission set to true here still requires the corresponding global permission to be true, so an override can only
    narrow access, never widen it. 'allowedUsers' is intersected with the global 'allowedUsers', not a replacement for
    it.

        Attributes:
            allow_admin (bool | Unset): Restrict administrative access for this database
            allow_delete (bool | Unset): Restrict delete access for this database
            allow_insert (bool | Unset): Restrict insert access for this database
            allow_reads (bool | Unset): Restrict read access for this database
            allow_schema_change (bool | Unset): Restrict schema-change access for this database
            allow_update (bool | Unset): Restrict update access for this database
            allowed_users (list[str] | Unset): Users permitted on this database, intersected with the global 'allowedUsers'
    """

    allow_admin: bool | Unset = UNSET
    allow_delete: bool | Unset = UNSET
    allow_insert: bool | Unset = UNSET
    allow_reads: bool | Unset = UNSET
    allow_schema_change: bool | Unset = UNSET
    allow_update: bool | Unset = UNSET
    allowed_users: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allow_admin = self.allow_admin

        allow_delete = self.allow_delete

        allow_insert = self.allow_insert

        allow_reads = self.allow_reads

        allow_schema_change = self.allow_schema_change

        allow_update = self.allow_update

        allowed_users: list[str] | Unset = UNSET
        if not isinstance(self.allowed_users, Unset):
            allowed_users = self.allowed_users

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
        if allowed_users is not UNSET:
            field_dict["allowedUsers"] = allowed_users

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        allow_admin = d.pop("allowAdmin", UNSET)

        allow_delete = d.pop("allowDelete", UNSET)

        allow_insert = d.pop("allowInsert", UNSET)

        allow_reads = d.pop("allowReads", UNSET)

        allow_schema_change = d.pop("allowSchemaChange", UNSET)

        allow_update = d.pop("allowUpdate", UNSET)

        allowed_users = cast(list[str], d.pop("allowedUsers", UNSET))

        mcp_database_override = cls(
            allow_admin=allow_admin,
            allow_delete=allow_delete,
            allow_insert=allow_insert,
            allow_reads=allow_reads,
            allow_schema_change=allow_schema_change,
            allow_update=allow_update,
            allowed_users=allowed_users,
        )

        mcp_database_override.additional_properties = d
        return mcp_database_override

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
