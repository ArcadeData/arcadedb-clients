from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ServerInfo")


@_attrs_define
class ServerInfo:
    """Server information object

    Attributes:
        mode (str | Unset): Server mode
        status (str | Unset): Server status
        uptime (int | Unset): Server uptime in milliseconds
        version (str | Unset): Server version
    """

    mode: str | Unset = UNSET
    status: str | Unset = UNSET
    uptime: int | Unset = UNSET
    version: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode = self.mode

        status = self.status

        uptime = self.uptime

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if status is not UNSET:
            field_dict["status"] = status
        if uptime is not UNSET:
            field_dict["uptime"] = uptime
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mode = d.pop("mode", UNSET)

        status = d.pop("status", UNSET)

        uptime = d.pop("uptime", UNSET)

        version = d.pop("version", UNSET)

        server_info = cls(
            mode=mode,
            status=status,
            uptime=uptime,
            version=version,
        )

        server_info.additional_properties = d
        return server_info

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
