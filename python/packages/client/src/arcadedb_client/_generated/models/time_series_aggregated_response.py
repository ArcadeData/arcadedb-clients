from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.time_series_aggregated_response_buckets_item import TimeSeriesAggregatedResponseBucketsItem


T = TypeVar("T", bound="TimeSeriesAggregatedResponse")


@_attrs_define
class TimeSeriesAggregatedResponse:
    """Aggregated samples

    Attributes:
        aggregations (list[str] | Unset): Aliases of the computed aggregations, in bucket value order
        buckets (list[TimeSeriesAggregatedResponseBucketsItem] | Unset): Buckets, ordered by timestamp
        count (int | Unset): Number of buckets returned
        type_ (str | Unset): Time-series type name
    """

    aggregations: list[str] | Unset = UNSET
    buckets: list[TimeSeriesAggregatedResponseBucketsItem] | Unset = UNSET
    count: int | Unset = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        aggregations: list[str] | Unset = UNSET
        if not isinstance(self.aggregations, Unset):
            aggregations = self.aggregations

        buckets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.buckets, Unset):
            buckets = []
            for buckets_item_data in self.buckets:
                buckets_item = buckets_item_data.to_dict()
                buckets.append(buckets_item)

        count = self.count

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if aggregations is not UNSET:
            field_dict["aggregations"] = aggregations
        if buckets is not UNSET:
            field_dict["buckets"] = buckets
        if count is not UNSET:
            field_dict["count"] = count
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.time_series_aggregated_response_buckets_item import TimeSeriesAggregatedResponseBucketsItem

        d = dict(src_dict)
        aggregations = cast(list[str], d.pop("aggregations", UNSET))

        _buckets = d.pop("buckets", UNSET)
        buckets: list[TimeSeriesAggregatedResponseBucketsItem] | Unset = UNSET
        if _buckets is not UNSET:
            buckets = []
            for buckets_item_data in _buckets:
                buckets_item = TimeSeriesAggregatedResponseBucketsItem.from_dict(buckets_item_data)

                buckets.append(buckets_item)

        count = d.pop("count", UNSET)

        type_ = d.pop("type", UNSET)

        time_series_aggregated_response = cls(
            aggregations=aggregations,
            buckets=buckets,
            count=count,
            type_=type_,
        )

        time_series_aggregated_response.additional_properties = d
        return time_series_aggregated_response

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
