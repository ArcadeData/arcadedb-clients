from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VerifyDatabaseResponseResultPeersItemMismatchesItem")


@_attrs_define
class VerifyDatabaseResponseResultPeersItemMismatchesItem:
    """One file whose checksum differs between the leader and a peer

    Attributes:
        file (str | Unset): File name
        local_checksum (int | Unset): Leader's CRC for the file
        remote_checksum (str | Unset): Peer's CRC for the file, or 'MISSING' when the peer does not have it
        type_ (str | Unset): File category
    """

    file: str | Unset = UNSET
    local_checksum: int | Unset = UNSET
    remote_checksum: str | Unset = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        local_checksum = self.local_checksum

        remote_checksum = self.remote_checksum

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file is not UNSET:
            field_dict["file"] = file
        if local_checksum is not UNSET:
            field_dict["localChecksum"] = local_checksum
        if remote_checksum is not UNSET:
            field_dict["remoteChecksum"] = remote_checksum
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file", UNSET)

        local_checksum = d.pop("localChecksum", UNSET)

        remote_checksum = d.pop("remoteChecksum", UNSET)

        type_ = d.pop("type", UNSET)

        verify_database_response_result_peers_item_mismatches_item = cls(
            file=file,
            local_checksum=local_checksum,
            remote_checksum=remote_checksum,
            type_=type_,
        )

        verify_database_response_result_peers_item_mismatches_item.additional_properties = d
        return verify_database_response_result_peers_item_mismatches_item

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
