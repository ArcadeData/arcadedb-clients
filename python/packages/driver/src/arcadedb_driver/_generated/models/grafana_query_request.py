from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.grafana_query_request_targets_item import GrafanaQueryRequestTargetsItem


T = TypeVar("T", bound="GrafanaQueryRequest")


@_attrs_define
class GrafanaQueryRequest:
    """Grafana panel query

    Attributes:
        targets (list[GrafanaQueryRequestTargetsItem]): Queries to execute
        from_ (int | Unset): Inclusive lower bound of the timestamp range. Unbounded when omitted.
        max_data_points (int | Unset): Used with the time range to derive a bucket interval when
            'aggregation.bucketInterval' is omitted.
        to (int | Unset): Inclusive upper bound of the timestamp range. Unbounded when omitted.
    """

    targets: list[GrafanaQueryRequestTargetsItem]
    from_: int | Unset = UNSET
    max_data_points: int | Unset = UNSET
    to: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        targets = []
        for targets_item_data in self.targets:
            targets_item = targets_item_data.to_dict()
            targets.append(targets_item)

        from_ = self.from_

        max_data_points = self.max_data_points

        to = self.to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "targets": targets,
            }
        )
        if from_ is not UNSET:
            field_dict["from"] = from_
        if max_data_points is not UNSET:
            field_dict["maxDataPoints"] = max_data_points
        if to is not UNSET:
            field_dict["to"] = to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.grafana_query_request_targets_item import GrafanaQueryRequestTargetsItem

        d = dict(src_dict)
        targets = []
        _targets = d.pop("targets")
        for targets_item_data in _targets:
            targets_item = GrafanaQueryRequestTargetsItem.from_dict(targets_item_data)

            targets.append(targets_item)

        from_ = d.pop("from", UNSET)

        max_data_points = d.pop("maxDataPoints", UNSET)

        to = d.pop("to", UNSET)

        grafana_query_request = cls(
            targets=targets,
            from_=from_,
            max_data_points=max_data_points,
            to=to,
        )

        grafana_query_request.additional_properties = d
        return grafana_query_request

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
