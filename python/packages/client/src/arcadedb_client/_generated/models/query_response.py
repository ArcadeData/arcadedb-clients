from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.query_response_result_item import QueryResponseResultItem


T = TypeVar("T", bound="QueryResponse")


@_attrs_define
class QueryResponse:
    """Query response object

    Attributes:
        limit (int | Unset): Effective row cap applied while serializing, -1 when uncapped. This is the serializer's
            cap, not the query's own LIMIT: a query stating a LIMIT below the server default reports the default here, and
            'returned' with 'truncated' describe what the response actually carries.
        result (list[QueryResponseResultItem] | Unset): Query results
        returned (int | Unset): Number of rows carried by this response. With the 'graph' serializer, whose cap counts
            graph elements rather than rows, it is the number of serialized vertices plus edges, and it can exceed 'limit':
            a single row can expand into several elements, and the expansion of the row that reaches the cap is not cut in
            half.
        truncated (bool | Unset): True when the cap stopped the serialization with rows still pending, so the response
            is incomplete
    """

    limit: int | Unset = UNSET
    result: list[QueryResponseResultItem] | Unset = UNSET
    returned: int | Unset = UNSET
    truncated: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limit = self.limit

        result: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = []
            for result_item_data in self.result:
                result_item = result_item_data.to_dict()
                result.append(result_item)

        returned = self.returned

        truncated = self.truncated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if limit is not UNSET:
            field_dict["limit"] = limit
        if result is not UNSET:
            field_dict["result"] = result
        if returned is not UNSET:
            field_dict["returned"] = returned
        if truncated is not UNSET:
            field_dict["truncated"] = truncated

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.query_response_result_item import QueryResponseResultItem

        d = dict(src_dict)
        limit = d.pop("limit", UNSET)

        _result = d.pop("result", UNSET)
        result: list[QueryResponseResultItem] | Unset = UNSET
        if _result is not UNSET:
            result = []
            for result_item_data in _result:
                result_item = QueryResponseResultItem.from_dict(result_item_data)

                result.append(result_item)

        returned = d.pop("returned", UNSET)

        truncated = d.pop("truncated", UNSET)

        query_response = cls(
            limit=limit,
            result=result,
            returned=returned,
            truncated=truncated,
        )

        query_response.additional_properties = d
        return query_response

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
