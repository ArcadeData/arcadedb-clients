from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.prom_ql_data_response_data_result_type_0_item_metric import (
        PromQLDataResponseDataResultType0ItemMetric,
    )


T = TypeVar("T", bound="PromQLDataResponseDataResultType0Item")


@_attrs_define
class PromQLDataResponseDataResultType0Item:
    """One instant sample

    Attributes:
        metric (PromQLDataResponseDataResultType0ItemMetric): Label map, including the '__name__' label
        value (list[Any]): One [timestamp, value] pair: a Unix timestamp in seconds (number), then the sample value
            (string)
    """

    metric: PromQLDataResponseDataResultType0ItemMetric
    value: list[Any]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metric = self.metric.to_dict()

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metric": metric,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prom_ql_data_response_data_result_type_0_item_metric import (
            PromQLDataResponseDataResultType0ItemMetric,
        )

        d = dict(src_dict)
        metric = PromQLDataResponseDataResultType0ItemMetric.from_dict(d.pop("metric"))

        value = cast(list[Any], d.pop("value"))

        prom_ql_data_response_data_result_type_0_item = cls(
            metric=metric,
            value=value,
        )

        prom_ql_data_response_data_result_type_0_item.additional_properties = d
        return prom_ql_data_response_data_result_type_0_item

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
