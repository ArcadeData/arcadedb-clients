from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_chat_messages_item_commands_item import AiChatMessagesItemCommandsItem


T = TypeVar("T", bound="AiChatMessagesItem")


@_attrs_define
class AiChatMessagesItem:
    """One chat message

    Attributes:
        commands (list[AiChatMessagesItemCommandsItem] | Unset): SQL commands the assistant proposed with this reply.
            Present only on an assistant message that proposed at least one.
        content (str | Unset): Message text
        role (str | Unset): 'user' or the assistant role
        timestamp (str | Unset): ISO-8601 instant
    """

    commands: list[AiChatMessagesItemCommandsItem] | Unset = UNSET
    content: str | Unset = UNSET
    role: str | Unset = UNSET
    timestamp: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        commands: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.commands, Unset):
            commands = []
            for commands_item_data in self.commands:
                commands_item = commands_item_data.to_dict()
                commands.append(commands_item)

        content = self.content

        role = self.role

        timestamp = self.timestamp

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if commands is not UNSET:
            field_dict["commands"] = commands
        if content is not UNSET:
            field_dict["content"] = content
        if role is not UNSET:
            field_dict["role"] = role
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_chat_messages_item_commands_item import AiChatMessagesItemCommandsItem

        d = dict(src_dict)
        _commands = d.pop("commands", UNSET)
        commands: list[AiChatMessagesItemCommandsItem] | Unset = UNSET
        if _commands is not UNSET:
            commands = []
            for commands_item_data in _commands:
                commands_item = AiChatMessagesItemCommandsItem.from_dict(commands_item_data)

                commands.append(commands_item)

        content = d.pop("content", UNSET)

        role = d.pop("role", UNSET)

        timestamp = d.pop("timestamp", UNSET)

        ai_chat_messages_item = cls(
            commands=commands,
            content=content,
            role=role,
            timestamp=timestamp,
        )

        ai_chat_messages_item.additional_properties = d
        return ai_chat_messages_item

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
