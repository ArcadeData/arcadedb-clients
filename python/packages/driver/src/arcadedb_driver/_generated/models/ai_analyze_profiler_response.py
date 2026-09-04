from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_analyze_profiler_response_commands_item import AiAnalyzeProfilerResponseCommandsItem


T = TypeVar("T", bound="AiAnalyzeProfilerResponse")


@_attrs_define
class AiAnalyzeProfilerResponse:
    """Profiler analysis

    Attributes:
        commands (list[AiAnalyzeProfilerResponseCommandsItem] | Unset): Commands the assistant proposes. Absent when it
            proposes none.
        response (str | Unset): Assistant analysis
    """

    commands: list[AiAnalyzeProfilerResponseCommandsItem] | Unset = UNSET
    response: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        commands: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.commands, Unset):
            commands = []
            for commands_item_data in self.commands:
                commands_item = commands_item_data.to_dict()
                commands.append(commands_item)

        response = self.response

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if commands is not UNSET:
            field_dict["commands"] = commands
        if response is not UNSET:
            field_dict["response"] = response

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_analyze_profiler_response_commands_item import AiAnalyzeProfilerResponseCommandsItem

        d = dict(src_dict)
        _commands = d.pop("commands", UNSET)
        commands: list[AiAnalyzeProfilerResponseCommandsItem] | Unset = UNSET
        if _commands is not UNSET:
            commands = []
            for commands_item_data in _commands:
                commands_item = AiAnalyzeProfilerResponseCommandsItem.from_dict(commands_item_data)

                commands.append(commands_item)

        response = d.pop("response", UNSET)

        ai_analyze_profiler_response = cls(
            commands=commands,
            response=response,
        )

        ai_analyze_profiler_response.additional_properties = d
        return ai_analyze_profiler_response

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
