from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VerifyDatabaseResponseFilesItem")


@_attrs_define
class VerifyDatabaseResponseFilesItem:
    """One database file

    Attributes:
        checksum (int | Unset): CRC of the file's contents
        name (str | Unset): File name
        size (int | Unset): File size in bytes
        type_ (str | Unset): File category
    """

    checksum: int | Unset = UNSET
    name: str | Unset = UNSET
    size: int | Unset = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        checksum = self.checksum

        name = self.name

        size = self.size

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if checksum is not UNSET:
            field_dict["checksum"] = checksum
        if name is not UNSET:
            field_dict["name"] = name
        if size is not UNSET:
            field_dict["size"] = size
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        checksum = d.pop("checksum", UNSET)

        name = d.pop("name", UNSET)

        size = d.pop("size", UNSET)

        type_ = d.pop("type", UNSET)

        verify_database_response_files_item = cls(
            checksum=checksum,
            name=name,
            size=size,
            type_=type_,
        )

        verify_database_response_files_item.additional_properties = d
        return verify_database_response_files_item

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
