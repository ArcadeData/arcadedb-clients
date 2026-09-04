from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AiChatRequest")


@_attrs_define
class AiChatRequest:
    """Chat message

    Attributes:
        database (str): Database the question is about. The caller must be authorized on it.
        message (str): User message
        chat_id (str | Unset): Existing chat to continue. A new chat is created when omitted.
        protocol_version (int | Unset): Protocol version the client speaks. Rejected with 'protocol_unsupported' when
            unknown. Defaults to 1 when omitted.
    """

    database: str
    message: str
    chat_id: str | Unset = UNSET
    protocol_version: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        database = self.database

        message = self.message

        chat_id = self.chat_id

        protocol_version = self.protocol_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "database": database,
                "message": message,
            }
        )
        if chat_id is not UNSET:
            field_dict["chatId"] = chat_id
        if protocol_version is not UNSET:
            field_dict["protocolVersion"] = protocol_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        database = d.pop("database")

        message = d.pop("message")

        chat_id = d.pop("chatId", UNSET)

        protocol_version = d.pop("protocolVersion", UNSET)

        ai_chat_request = cls(
            database=database,
            message=message,
            chat_id=chat_id,
            protocol_version=protocol_version,
        )

        ai_chat_request.additional_properties = d
        return ai_chat_request

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
