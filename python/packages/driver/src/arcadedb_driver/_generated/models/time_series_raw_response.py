from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.time_series_raw_response_rows_item_item import TimeSeriesRawResponseRowsItemItem


T = TypeVar("T", bound="TimeSeriesRawResponse")


@_attrs_define
class TimeSeriesRawResponse:
    """Raw samples

    Attributes:
        columns (list[str] | Unset): Column names, in the order the row values appear
        count (int | Unset): Number of rows returned
        rows (list[list[TimeSeriesRawResponseRowsItemItem]] | Unset): Rows, each positionally aligned with 'columns'
        type_ (str | Unset): Time-series type name
    """

    columns: list[str] | Unset = UNSET
    count: int | Unset = UNSET
    rows: list[list[TimeSeriesRawResponseRowsItemItem]] | Unset = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        columns: list[str] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = self.columns

        count = self.count

        rows: list[list[dict[str, Any]]] | Unset = UNSET
        if not isinstance(self.rows, Unset):
            rows = []
            for rows_item_data in self.rows:
                rows_item = []
                for rows_item_item_data in rows_item_data:
                    rows_item_item = rows_item_item_data.to_dict()
                    rows_item.append(rows_item_item)

                rows.append(rows_item)

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if columns is not UNSET:
            field_dict["columns"] = columns
        if count is not UNSET:
            field_dict["count"] = count
        if rows is not UNSET:
            field_dict["rows"] = rows
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.time_series_raw_response_rows_item_item import TimeSeriesRawResponseRowsItemItem

        d = dict(src_dict)
        columns = cast(list[str], d.pop("columns", UNSET))

        count = d.pop("count", UNSET)

        _rows = d.pop("rows", UNSET)
        rows: list[list[TimeSeriesRawResponseRowsItemItem]] | Unset = UNSET
        if _rows is not UNSET:
            rows = []
            for rows_item_data in _rows:
                rows_item = []
                _rows_item = rows_item_data
                for rows_item_item_data in _rows_item:
                    rows_item_item = TimeSeriesRawResponseRowsItemItem.from_dict(rows_item_item_data)

                    rows_item.append(rows_item_item)

                rows.append(rows_item)

        type_ = d.pop("type", UNSET)

        time_series_raw_response = cls(
            columns=columns,
            count=count,
            rows=rows,
            type_=type_,
        )

        time_series_raw_response.additional_properties = d
        return time_series_raw_response

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
