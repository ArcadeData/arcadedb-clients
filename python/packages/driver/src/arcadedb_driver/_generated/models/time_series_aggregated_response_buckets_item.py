from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.time_series_aggregated_response_buckets_item_values_item import (
        TimeSeriesAggregatedResponseBucketsItemValuesItem,
    )


T = TypeVar("T", bound="TimeSeriesAggregatedResponseBucketsItem")


@_attrs_define
class TimeSeriesAggregatedResponseBucketsItem:
    """One aggregation bucket

    Attributes:
        timestamp (int | Unset): Bucket start timestamp
        values (list[TimeSeriesAggregatedResponseBucketsItemValuesItem] | Unset): Aggregated values, positionally
            aligned with 'aggregations'
    """

    timestamp: int | Unset = UNSET
    values: list[TimeSeriesAggregatedResponseBucketsItemValuesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp

        values: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.values, Unset):
            values = []
            for values_item_data in self.values:
                values_item = values_item_data.to_dict()
                values.append(values_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.time_series_aggregated_response_buckets_item_values_item import (
            TimeSeriesAggregatedResponseBucketsItemValuesItem,
        )

        d = dict(src_dict)
        timestamp = d.pop("timestamp", UNSET)

        _values = d.pop("values", UNSET)
        values: list[TimeSeriesAggregatedResponseBucketsItemValuesItem] | Unset = UNSET
        if _values is not UNSET:
            values = []
            for values_item_data in _values:
                values_item = TimeSeriesAggregatedResponseBucketsItemValuesItem.from_dict(values_item_data)

                values.append(values_item)

        time_series_aggregated_response_buckets_item = cls(
            timestamp=timestamp,
            values=values,
        )

        time_series_aggregated_response_buckets_item.additional_properties = d
        return time_series_aggregated_response_buckets_item

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
