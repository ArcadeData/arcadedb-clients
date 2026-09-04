from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.verify_database_response_files_item import VerifyDatabaseResponseFilesItem
    from ..models.verify_database_response_local_checksums import VerifyDatabaseResponseLocalChecksums
    from ..models.verify_database_response_result import VerifyDatabaseResponseResult


T = TypeVar("T", bound="VerifyDatabaseResponse")


@_attrs_define
class VerifyDatabaseResponse:
    """Per-file checksums of one database. A follower response carries only its own 'localChecksums', 'files' and
    'localServer'; the leader instead returns only 'result', nesting a cluster-wide comparison against every other peer.

        Attributes:
            files (list[VerifyDatabaseResponseFilesItem] | Unset): Files with size and category. Present on a follower
                response.
            local_checksums (VerifyDatabaseResponseLocalChecksums | Unset): File name to checksum map, for a quick cross-
                peer comparison. Present on a follower response.
            local_server (str | Unset): Server the checksums were taken on. Present on a follower response.
            result (VerifyDatabaseResponseResult | Unset): Leader-only cluster-wide comparison, fanned out to every peer
    """

    files: list[VerifyDatabaseResponseFilesItem] | Unset = UNSET
    local_checksums: VerifyDatabaseResponseLocalChecksums | Unset = UNSET
    local_server: str | Unset = UNSET
    result: VerifyDatabaseResponseResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        local_checksums: dict[str, Any] | Unset = UNSET
        if not isinstance(self.local_checksums, Unset):
            local_checksums = self.local_checksums.to_dict()

        local_server = self.local_server

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if files is not UNSET:
            field_dict["files"] = files
        if local_checksums is not UNSET:
            field_dict["localChecksums"] = local_checksums
        if local_server is not UNSET:
            field_dict["localServer"] = local_server
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.verify_database_response_files_item import VerifyDatabaseResponseFilesItem
        from ..models.verify_database_response_local_checksums import VerifyDatabaseResponseLocalChecksums
        from ..models.verify_database_response_result import VerifyDatabaseResponseResult

        d = dict(src_dict)
        _files = d.pop("files", UNSET)
        files: list[VerifyDatabaseResponseFilesItem] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = VerifyDatabaseResponseFilesItem.from_dict(files_item_data)

                files.append(files_item)

        _local_checksums = d.pop("localChecksums", UNSET)
        local_checksums: VerifyDatabaseResponseLocalChecksums | Unset
        if isinstance(_local_checksums, Unset):
            local_checksums = UNSET
        else:
            local_checksums = VerifyDatabaseResponseLocalChecksums.from_dict(_local_checksums)

        local_server = d.pop("localServer", UNSET)

        _result = d.pop("result", UNSET)
        result: VerifyDatabaseResponseResult | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = VerifyDatabaseResponseResult.from_dict(_result)

        verify_database_response = cls(
            files=files,
            local_checksums=local_checksums,
            local_server=local_server,
            result=result,
        )

        verify_database_response.additional_properties = d
        return verify_database_response

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
