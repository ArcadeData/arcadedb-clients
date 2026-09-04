from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.grafana_metadata_types_item_fields_item import GrafanaMetadataTypesItemFieldsItem
    from ..models.grafana_metadata_types_item_tags_item import GrafanaMetadataTypesItemTagsItem


T = TypeVar("T", bound="GrafanaMetadataTypesItem")


@_attrs_define
class GrafanaMetadataTypesItem:
    """One queryable time-series type

    Attributes:
        fields (list[GrafanaMetadataTypesItemFieldsItem] | Unset): Value columns
        name (str | Unset): Type name
        tags (list[GrafanaMetadataTypesItemTagsItem] | Unset): Tag columns available as filters
    """

    fields: list[GrafanaMetadataTypesItemFieldsItem] | Unset = UNSET
    name: str | Unset = UNSET
    tags: list[GrafanaMetadataTypesItemTagsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fields: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.fields, Unset):
            fields = []
            for fields_item_data in self.fields:
                fields_item = fields_item_data.to_dict()
                fields.append(fields_item)

        name = self.name

        tags: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = []
            for tags_item_data in self.tags:
                tags_item = tags_item_data.to_dict()
                tags.append(tags_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if fields is not UNSET:
            field_dict["fields"] = fields
        if name is not UNSET:
            field_dict["name"] = name
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.grafana_metadata_types_item_fields_item import GrafanaMetadataTypesItemFieldsItem
        from ..models.grafana_metadata_types_item_tags_item import GrafanaMetadataTypesItemTagsItem

        d = dict(src_dict)
        _fields = d.pop("fields", UNSET)
        fields: list[GrafanaMetadataTypesItemFieldsItem] | Unset = UNSET
        if _fields is not UNSET:
            fields = []
            for fields_item_data in _fields:
                fields_item = GrafanaMetadataTypesItemFieldsItem.from_dict(fields_item_data)

                fields.append(fields_item)

        name = d.pop("name", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: list[GrafanaMetadataTypesItemTagsItem] | Unset = UNSET
        if _tags is not UNSET:
            tags = []
            for tags_item_data in _tags:
                tags_item = GrafanaMetadataTypesItemTagsItem.from_dict(tags_item_data)

                tags.append(tags_item)

        grafana_metadata_types_item = cls(
            fields=fields,
            name=name,
            tags=tags,
        )

        grafana_metadata_types_item.additional_properties = d
        return grafana_metadata_types_item

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
