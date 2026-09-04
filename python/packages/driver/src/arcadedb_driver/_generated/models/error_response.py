from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ErrorResponse")


@_attrs_define
class ErrorResponse:
    """Error response object

    Attributes:
        detail (str | Unset): Error details
        error (str | Unset): Error message
        exception (str | Unset): Exception class name
        exception_args (str | Unset): Exception arguments
        help_ (str | Unset): Help information
    """

    detail: str | Unset = UNSET
    error: str | Unset = UNSET
    exception: str | Unset = UNSET
    exception_args: str | Unset = UNSET
    help_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        detail = self.detail

        error = self.error

        exception = self.exception

        exception_args = self.exception_args

        help_ = self.help_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if detail is not UNSET:
            field_dict["detail"] = detail
        if error is not UNSET:
            field_dict["error"] = error
        if exception is not UNSET:
            field_dict["exception"] = exception
        if exception_args is not UNSET:
            field_dict["exceptionArgs"] = exception_args
        if help_ is not UNSET:
            field_dict["help"] = help_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        detail = d.pop("detail", UNSET)

        error = d.pop("error", UNSET)

        exception = d.pop("exception", UNSET)

        exception_args = d.pop("exceptionArgs", UNSET)

        help_ = d.pop("help", UNSET)

        error_response = cls(
            detail=detail,
            error=error,
            exception=exception,
            exception_args=exception_args,
            help_=help_,
        )

        error_response.additional_properties = d
        return error_response

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
