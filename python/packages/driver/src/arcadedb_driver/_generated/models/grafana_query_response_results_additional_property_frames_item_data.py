from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.grafana_query_response_results_additional_property_frames_item_data_values_item_item import (
        GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem,
    )


T = TypeVar("T", bound="GrafanaQueryResponseResultsAdditionalPropertyFramesItemData")


@_attrs_define
class GrafanaQueryResponseResultsAdditionalPropertyFramesItemData:
    """Frame data

    Attributes:
        values (list[list[GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem]] | Unset): Column-
            major values, one array per field
    """

    values: list[list[GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem]] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        values: list[list[dict[str, Any]]] | Unset = UNSET
        if not isinstance(self.values, Unset):
            values = []
            for values_item_data in self.values:
                values_item = []
                for values_item_item_data in values_item_data:
                    values_item_item = values_item_item_data.to_dict()
                    values_item.append(values_item_item)

                values.append(values_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.grafana_query_response_results_additional_property_frames_item_data_values_item_item import (
            GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem,
        )

        d = dict(src_dict)
        _values = d.pop("values", UNSET)
        values: list[list[GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem]] | Unset = UNSET
        if _values is not UNSET:
            values = []
            for values_item_data in _values:
                values_item = []
                _values_item = values_item_data
                for values_item_item_data in _values_item:
                    values_item_item = (
                        GrafanaQueryResponseResultsAdditionalPropertyFramesItemDataValuesItemItem.from_dict(
                            values_item_item_data
                        )
                    )

                    values_item.append(values_item_item)

                values.append(values_item)

        grafana_query_response_results_additional_property_frames_item_data = cls(
            values=values,
        )

        grafana_query_response_results_additional_property_frames_item_data.additional_properties = d
        return grafana_query_response_results_additional_property_frames_item_data

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
