from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.query_request_params import QueryRequestParams


T = TypeVar("T", bound="QueryRequest")


@_attrs_define
class QueryRequest:
    """Query request object

    Attributes:
        command (str): Query or command to execute
        language (str | Unset): Query language Example: sql.
        limit (int | Unset): Maximum number of rows to serialize into the response. When omitted, a LIMIT stated by the
            query is honored as written and only a query stating none is capped by the server default
            ('arcadedb.server.httpQueryDefaultLimit'). Use -1 for no cap. The response always reports the cap that was
            applied ('limit'), how many rows it carries ('returned') and whether rows were left behind ('truncated'). No
            value here can widen a single response past the server's hard ceiling
            ('arcadedb.server.httpQueryMaxResultRows'): a result that would exceed it is refused with 413 instead of being
            truncated. Example: 100.
        params (QueryRequestParams | Unset): Query parameters. Values may be JSON primitives, arrays, or typed-marker
            objects: {"$bytes": "<base64>"} for byte[] (standard or URL-safe base64), {"$int8": [v0, v1, ...]} for byte[]
            from integers in [-128, 127] (used to send INT8-encoded vectors to LSM_VECTOR indexes without a float32 round-
            trip).
        serializer (str | Unset): Response serializer Example: json.
    """

    command: str
    language: str | Unset = UNSET
    limit: int | Unset = UNSET
    params: QueryRequestParams | Unset = UNSET
    serializer: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        command = self.command

        language = self.language

        limit = self.limit

        params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.params, Unset):
            params = self.params.to_dict()

        serializer = self.serializer

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "command": command,
            }
        )
        if language is not UNSET:
            field_dict["language"] = language
        if limit is not UNSET:
            field_dict["limit"] = limit
        if params is not UNSET:
            field_dict["params"] = params
        if serializer is not UNSET:
            field_dict["serializer"] = serializer

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.query_request_params import QueryRequestParams

        d = dict(src_dict)
        command = d.pop("command")

        language = d.pop("language", UNSET)

        limit = d.pop("limit", UNSET)

        _params = d.pop("params", UNSET)
        params: QueryRequestParams | Unset
        if isinstance(_params, Unset):
            params = UNSET
        else:
            params = QueryRequestParams.from_dict(_params)

        serializer = d.pop("serializer", UNSET)

        query_request = cls(
            command=command,
            language=language,
            limit=limit,
            params=params,
            serializer=serializer,
        )

        query_request.additional_properties = d
        return query_request

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
