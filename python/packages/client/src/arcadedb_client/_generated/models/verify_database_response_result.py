from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.verify_database_response_result_files_item import VerifyDatabaseResponseResultFilesItem
    from ..models.verify_database_response_result_local_checksums import VerifyDatabaseResponseResultLocalChecksums
    from ..models.verify_database_response_result_peers_item import VerifyDatabaseResponseResultPeersItem


T = TypeVar("T", bound="VerifyDatabaseResponseResult")


@_attrs_define
class VerifyDatabaseResponseResult:
    """Leader-only cluster-wide comparison, fanned out to every peer

    Attributes:
        database (str | Unset): Database name
        files (list[VerifyDatabaseResponseResultFilesItem] | Unset): The leader's files with size and category
        local_checksums (VerifyDatabaseResponseResultLocalChecksums | Unset): Leader's file name to checksum map
        local_peer_id (str | Unset): Leader's peer identifier
        local_server (str | Unset): Leader server name
        overall_status (str | Unset): ALL_CONSISTENT when every peer was compared and agreed, INCONSISTENCY_DETECTED
            when a compared peer differs, VERIFICATION_INCOMPLETE when nothing diverged but at least one peer could not be
            verified
        peers (list[VerifyDatabaseResponseResultPeersItem] | Unset): Every other peer's comparison result
    """

    database: str | Unset = UNSET
    files: list[VerifyDatabaseResponseResultFilesItem] | Unset = UNSET
    local_checksums: VerifyDatabaseResponseResultLocalChecksums | Unset = UNSET
    local_peer_id: str | Unset = UNSET
    local_server: str | Unset = UNSET
    overall_status: str | Unset = UNSET
    peers: list[VerifyDatabaseResponseResultPeersItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        database = self.database

        files: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        local_checksums: dict[str, Any] | Unset = UNSET
        if not isinstance(self.local_checksums, Unset):
            local_checksums = self.local_checksums.to_dict()

        local_peer_id = self.local_peer_id

        local_server = self.local_server

        overall_status = self.overall_status

        peers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.peers, Unset):
            peers = []
            for peers_item_data in self.peers:
                peers_item = peers_item_data.to_dict()
                peers.append(peers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if database is not UNSET:
            field_dict["database"] = database
        if files is not UNSET:
            field_dict["files"] = files
        if local_checksums is not UNSET:
            field_dict["localChecksums"] = local_checksums
        if local_peer_id is not UNSET:
            field_dict["localPeerId"] = local_peer_id
        if local_server is not UNSET:
            field_dict["localServer"] = local_server
        if overall_status is not UNSET:
            field_dict["overallStatus"] = overall_status
        if peers is not UNSET:
            field_dict["peers"] = peers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.verify_database_response_result_files_item import VerifyDatabaseResponseResultFilesItem
        from ..models.verify_database_response_result_local_checksums import VerifyDatabaseResponseResultLocalChecksums
        from ..models.verify_database_response_result_peers_item import VerifyDatabaseResponseResultPeersItem

        d = dict(src_dict)
        database = d.pop("database", UNSET)

        _files = d.pop("files", UNSET)
        files: list[VerifyDatabaseResponseResultFilesItem] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = VerifyDatabaseResponseResultFilesItem.from_dict(files_item_data)

                files.append(files_item)

        _local_checksums = d.pop("localChecksums", UNSET)
        local_checksums: VerifyDatabaseResponseResultLocalChecksums | Unset
        if isinstance(_local_checksums, Unset):
            local_checksums = UNSET
        else:
            local_checksums = VerifyDatabaseResponseResultLocalChecksums.from_dict(_local_checksums)

        local_peer_id = d.pop("localPeerId", UNSET)

        local_server = d.pop("localServer", UNSET)

        overall_status = d.pop("overallStatus", UNSET)

        _peers = d.pop("peers", UNSET)
        peers: list[VerifyDatabaseResponseResultPeersItem] | Unset = UNSET
        if _peers is not UNSET:
            peers = []
            for peers_item_data in _peers:
                peers_item = VerifyDatabaseResponseResultPeersItem.from_dict(peers_item_data)

                peers.append(peers_item)

        verify_database_response_result = cls(
            database=database,
            files=files,
            local_checksums=local_checksums,
            local_peer_id=local_peer_id,
            local_server=local_server,
            overall_status=overall_status,
            peers=peers,
        )

        verify_database_response_result.additional_properties = d
        return verify_database_response_result

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
