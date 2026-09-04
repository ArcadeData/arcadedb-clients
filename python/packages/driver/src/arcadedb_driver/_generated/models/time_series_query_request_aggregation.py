from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.time_series_query_request_aggregation_requests_item import (
        TimeSeriesQueryRequestAggregationRequestsItem,
    )


T = TypeVar("T", bound="TimeSeriesQueryRequestAggregation")


@_attrs_define
class TimeSeriesQueryRequestAggregation:
    """Bucketed aggregation. Present only when the caller wants buckets rather than raw rows.

    Attributes:
        bucket_interval (int | Unset): Bucket width in the same unit as the timestamps
        requests (list[TimeSeriesQueryRequestAggregationRequestsItem] | Unset): Aggregations to compute
    """

    bucket_interval: int | Unset = UNSET
    requests: list[TimeSeriesQueryRequestAggregationRequestsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bucket_interval = self.bucket_interval

        requests: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.requests, Unset):
            requests = []
            for requests_item_data in self.requests:
                requests_item = requests_item_data.to_dict()
                requests.append(requests_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bucket_interval is not UNSET:
            field_dict["bucketInterval"] = bucket_interval
        if requests is not UNSET:
            field_dict["requests"] = requests

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.time_series_query_request_aggregation_requests_item import (
            TimeSeriesQueryRequestAggregationRequestsItem,
        )

        d = dict(src_dict)
        bucket_interval = d.pop("bucketInterval", UNSET)

        _requests = d.pop("requests", UNSET)
        requests: list[TimeSeriesQueryRequestAggregationRequestsItem] | Unset = UNSET
        if _requests is not UNSET:
            requests = []
            for requests_item_data in _requests:
                requests_item = TimeSeriesQueryRequestAggregationRequestsItem.from_dict(requests_item_data)

                requests.append(requests_item)

        time_series_query_request_aggregation = cls(
            bucket_interval=bucket_interval,
            requests=requests,
        )

        time_series_query_request_aggregation.additional_properties = d
        return time_series_query_request_aggregation

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
