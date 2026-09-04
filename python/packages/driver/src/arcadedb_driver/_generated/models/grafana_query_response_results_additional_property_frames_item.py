from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.grafana_query_response_results_additional_property_frames_item_data import (
        GrafanaQueryResponseResultsAdditionalPropertyFramesItemData,
    )
    from ..models.grafana_query_response_results_additional_property_frames_item_schema import (
        GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema,
    )


T = TypeVar("T", bound="GrafanaQueryResponseResultsAdditionalPropertyFramesItem")


@_attrs_define
class GrafanaQueryResponseResultsAdditionalPropertyFramesItem:
    """One DataFrame

    Attributes:
        data (GrafanaQueryResponseResultsAdditionalPropertyFramesItemData | Unset): Frame data
        schema (GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema | Unset): Frame schema
    """

    data: GrafanaQueryResponseResultsAdditionalPropertyFramesItemData | Unset = UNSET
    schema: GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        schema: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schema, Unset):
            schema = self.schema.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if schema is not UNSET:
            field_dict["schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.grafana_query_response_results_additional_property_frames_item_data import (
            GrafanaQueryResponseResultsAdditionalPropertyFramesItemData,
        )
        from ..models.grafana_query_response_results_additional_property_frames_item_schema import (
            GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema,
        )

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: GrafanaQueryResponseResultsAdditionalPropertyFramesItemData | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = GrafanaQueryResponseResultsAdditionalPropertyFramesItemData.from_dict(_data)

        _schema = d.pop("schema", UNSET)
        schema: GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema | Unset
        if isinstance(_schema, Unset):
            schema = UNSET
        else:
            schema = GrafanaQueryResponseResultsAdditionalPropertyFramesItemSchema.from_dict(_schema)

        grafana_query_response_results_additional_property_frames_item = cls(
            data=data,
            schema=schema,
        )

        grafana_query_response_results_additional_property_frames_item.additional_properties = d
        return grafana_query_response_results_additional_property_frames_item

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
