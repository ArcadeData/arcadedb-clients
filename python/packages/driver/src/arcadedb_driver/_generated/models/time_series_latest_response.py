from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.time_series_latest_response_latest_type_0_item import TimeSeriesLatestResponseLatestType0Item


T = TypeVar("T", bound="TimeSeriesLatestResponse")


@_attrs_define
class TimeSeriesLatestResponse:
    """Most recent sample of a series

    Attributes:
        columns (list[str] | Unset): Column names, in sample value order
        latest (list[TimeSeriesLatestResponseLatestType0Item] | None | Unset): Most recent sample, positionally aligned
            with 'columns'. Null when the series is empty.
        type_ (str | Unset): Time-series type name
    """

    columns: list[str] | Unset = UNSET
    latest: list[TimeSeriesLatestResponseLatestType0Item] | Unset | None = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        columns: list[str] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = self.columns

        latest: list[dict[str, Any]] | Unset | None
        if isinstance(self.latest, Unset):
            latest = UNSET
        elif isinstance(self.latest, list):
            latest = []
            for latest_type_0_item_data in self.latest:
                latest_type_0_item = latest_type_0_item_data.to_dict()
                latest.append(latest_type_0_item)

        else:
            latest = self.latest

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if columns is not UNSET:
            field_dict["columns"] = columns
        if latest is not UNSET:
            field_dict["latest"] = latest
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.time_series_latest_response_latest_type_0_item import TimeSeriesLatestResponseLatestType0Item

        d = dict(src_dict)
        columns = cast(list[str], d.pop("columns", UNSET))

        def _parse_latest(data: object) -> list[TimeSeriesLatestResponseLatestType0Item] | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                latest_type_0 = []
                _latest_type_0 = data
                for latest_type_0_item_data in _latest_type_0:
                    latest_type_0_item = TimeSeriesLatestResponseLatestType0Item.from_dict(latest_type_0_item_data)

                    latest_type_0.append(latest_type_0_item)

                return latest_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[TimeSeriesLatestResponseLatestType0Item] | None | Unset, data)

        latest = _parse_latest(d.pop("latest", UNSET))

        type_ = d.pop("type", UNSET)

        time_series_latest_response = cls(
            columns=columns,
            latest=latest,
            type_=type_,
        )

        time_series_latest_response.additional_properties = d
        return time_series_latest_response

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
