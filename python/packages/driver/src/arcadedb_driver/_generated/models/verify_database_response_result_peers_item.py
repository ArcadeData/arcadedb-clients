from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.verify_database_response_result_peers_item_mismatches_item import (
        VerifyDatabaseResponseResultPeersItemMismatchesItem,
    )


T = TypeVar("T", bound="VerifyDatabaseResponseResultPeersItem")


@_attrs_define
class VerifyDatabaseResponseResultPeersItem:
    """One peer's comparison against the leader's checksums

    Attributes:
        error (str | Unset): Why the peer could not be queried or compared. Absent on a completed comparison.
        http_address (str | Unset): Peer HTTP address
        matching_files (int | Unset): Files whose checksum matches. Absent when the peer could not be queried.
        mismatched_files (int | Unset): Files whose checksum differs. Absent when the peer could not be queried.
        mismatches (list[VerifyDatabaseResponseResultPeersItemMismatchesItem] | Unset): Present only when
            mismatchedFiles is greater than zero
        peer_id (str | Unset): Peer identifier
        status (str | Unset): CONSISTENT, INCONSISTENT, or ERROR
    """

    error: str | Unset = UNSET
    http_address: str | Unset = UNSET
    matching_files: int | Unset = UNSET
    mismatched_files: int | Unset = UNSET
    mismatches: list[VerifyDatabaseResponseResultPeersItemMismatchesItem] | Unset = UNSET
    peer_id: str | Unset = UNSET
    status: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        http_address = self.http_address

        matching_files = self.matching_files

        mismatched_files = self.mismatched_files

        mismatches: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.mismatches, Unset):
            mismatches = []
            for mismatches_item_data in self.mismatches:
                mismatches_item = mismatches_item_data.to_dict()
                mismatches.append(mismatches_item)

        peer_id = self.peer_id

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error
        if http_address is not UNSET:
            field_dict["httpAddress"] = http_address
        if matching_files is not UNSET:
            field_dict["matchingFiles"] = matching_files
        if mismatched_files is not UNSET:
            field_dict["mismatchedFiles"] = mismatched_files
        if mismatches is not UNSET:
            field_dict["mismatches"] = mismatches
        if peer_id is not UNSET:
            field_dict["peerId"] = peer_id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.verify_database_response_result_peers_item_mismatches_item import (
            VerifyDatabaseResponseResultPeersItemMismatchesItem,
        )

        d = dict(src_dict)
        error = d.pop("error", UNSET)

        http_address = d.pop("httpAddress", UNSET)

        matching_files = d.pop("matchingFiles", UNSET)

        mismatched_files = d.pop("mismatchedFiles", UNSET)

        _mismatches = d.pop("mismatches", UNSET)
        mismatches: list[VerifyDatabaseResponseResultPeersItemMismatchesItem] | Unset = UNSET
        if _mismatches is not UNSET:
            mismatches = []
            for mismatches_item_data in _mismatches:
                mismatches_item = VerifyDatabaseResponseResultPeersItemMismatchesItem.from_dict(mismatches_item_data)

                mismatches.append(mismatches_item)

        peer_id = d.pop("peerId", UNSET)

        status = d.pop("status", UNSET)

        verify_database_response_result_peers_item = cls(
            error=error,
            http_address=http_address,
            matching_files=matching_files,
            mismatched_files=mismatched_files,
            mismatches=mismatches,
            peer_id=peer_id,
            status=status,
        )

        verify_database_response_result_peers_item.additional_properties = d
        return verify_database_response_result_peers_item

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
