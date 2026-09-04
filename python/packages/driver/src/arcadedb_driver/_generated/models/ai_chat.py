from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_chat_messages_item import AiChatMessagesItem


T = TypeVar("T", bound="AiChat")


@_attrs_define
class AiChat:
    """One chat transcript. GET /api/v1/ai/chats returns this shape without 'messages'; GET /api/v1/ai/chats/{id} returns
    it in full.

        Attributes:
            created (str | Unset): ISO-8601 instant the chat was created
            database (str | Unset): Database this chat is about
            id (str | Unset): Chat identifier
            messages (list[AiChatMessagesItem] | Unset): Messages, oldest first. Omitted from the /chats list response.
            title (str | Unset): Chat title, generated from the first user message
            updated (str | Unset): ISO-8601 instant of the last change
    """

    created: str | Unset = UNSET
    database: str | Unset = UNSET
    id: str | Unset = UNSET
    messages: list[AiChatMessagesItem] | Unset = UNSET
    title: str | Unset = UNSET
    updated: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created = self.created

        database = self.database

        id = self.id

        messages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.messages, Unset):
            messages = []
            for messages_item_data in self.messages:
                messages_item = messages_item_data.to_dict()
                messages.append(messages_item)

        title = self.title

        updated = self.updated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if created is not UNSET:
            field_dict["created"] = created
        if database is not UNSET:
            field_dict["database"] = database
        if id is not UNSET:
            field_dict["id"] = id
        if messages is not UNSET:
            field_dict["messages"] = messages
        if title is not UNSET:
            field_dict["title"] = title
        if updated is not UNSET:
            field_dict["updated"] = updated

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_chat_messages_item import AiChatMessagesItem

        d = dict(src_dict)
        created = d.pop("created", UNSET)

        database = d.pop("database", UNSET)

        id = d.pop("id", UNSET)

        _messages = d.pop("messages", UNSET)
        messages: list[AiChatMessagesItem] | Unset = UNSET
        if _messages is not UNSET:
            messages = []
            for messages_item_data in _messages:
                messages_item = AiChatMessagesItem.from_dict(messages_item_data)

                messages.append(messages_item)

        title = d.pop("title", UNSET)

        updated = d.pop("updated", UNSET)

        ai_chat = cls(
            created=created,
            database=database,
            id=id,
            messages=messages,
            title=title,
            updated=updated,
        )

        ai_chat.additional_properties = d
        return ai_chat

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
