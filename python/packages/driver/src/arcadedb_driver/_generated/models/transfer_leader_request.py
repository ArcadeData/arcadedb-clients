from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TransferLeaderRequest")


@_attrs_define
class TransferLeaderRequest:
    """Transfer target. Send an empty object to let Raft choose. Unknown fields are rejected.

    Attributes:
        peer_id (str | Unset): Peer to make leader. Raft chooses when omitted.
        timeout_ms (int | Unset): How long to wait for the transfer to complete, in milliseconds. Defaults to 30000.
    """

    peer_id: str | Unset = UNSET
    timeout_ms: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        peer_id = self.peer_id

        timeout_ms = self.timeout_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if peer_id is not UNSET:
            field_dict["peerId"] = peer_id
        if timeout_ms is not UNSET:
            field_dict["timeoutMs"] = timeout_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        peer_id = d.pop("peerId", UNSET)

        timeout_ms = d.pop("timeoutMs", UNSET)

        transfer_leader_request = cls(
            peer_id=peer_id,
            timeout_ms=timeout_ms,
        )

        transfer_leader_request.additional_properties = d
        return transfer_leader_request

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
