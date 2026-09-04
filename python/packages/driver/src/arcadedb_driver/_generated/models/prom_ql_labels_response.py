from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PromQLLabelsResponse")


@_attrs_define
class PromQLLabelsResponse:
    """Prometheus label response

    Attributes:
        data (list[str] | Unset): Sorted names or values
        status (str | Unset): Always 'success' on a 200
    """

    data: list[str] | Unset = UNSET
    status: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: list[str] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        data = cast(list[str], d.pop("data", UNSET))

        status = d.pop("status", UNSET)

        prom_ql_labels_response = cls(
            data=data,
            status=status,
        )

        prom_ql_labels_response.additional_properties = d
        return prom_ql_labels_response

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
