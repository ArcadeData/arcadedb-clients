from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchError")


@_attrs_define
class BatchError:
    """Failed bulk load. Carries how much of the payload was attempted, because a batch is not atomic and the caller has to
    reconcile before retrying.

        Attributes:
            bytes_read (int | Unset): Bytes of the upload the server consumed, so a client can verify its whole file arrived
                - and, on a truncated load, how far the server got. Never more than the client sent.
            edges_created (int | Unset): Edges attempted before the failure, with the same upper-bound caveat as
                'verticesCreated'.
            error (str | Unset): Why the load failed. Carries the offending location, such as a line number or a temporary
                id, because a batch failure echoes client input rather than engine internals.
            exception (str | Unset): Exception class name, for distinguishing failure classes programmatically
            lines_read (int | Unset): Lines the parser read, so 'linesRead' minus 'linesSkipped' can be checked against the
                records created
            lines_skipped (int | Unset): Lines that carried no record: blank lines, plus CSV headers and '---' separators
            partial_commit (bool | Unset): True when earlier chunks are durably committed. Retrying the whole payload then
                duplicates the already-committed vertices, because temporary ids are not keys.
            request_id (str | Unset): Correlation id echoing X-Request-Id, for cross-referencing the failure against the
                server log. Absent when the request carried no correlation id.
            vertices_created (int | Unset): Vertices attempted before the failure. An upper bound on what is durable:
                records handled since the last commit boundary were rolled back.
            vertices_without_id (int | Unset): Vertices created without an '@id' under refMode=id. They are loaded and
                durable, but no edge can reference them. Absent when zero.
    """

    bytes_read: int | Unset = UNSET
    edges_created: int | Unset = UNSET
    error: str | Unset = UNSET
    exception: str | Unset = UNSET
    lines_read: int | Unset = UNSET
    lines_skipped: int | Unset = UNSET
    partial_commit: bool | Unset = UNSET
    request_id: str | Unset = UNSET
    vertices_created: int | Unset = UNSET
    vertices_without_id: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bytes_read = self.bytes_read

        edges_created = self.edges_created

        error = self.error

        exception = self.exception

        lines_read = self.lines_read

        lines_skipped = self.lines_skipped

        partial_commit = self.partial_commit

        request_id = self.request_id

        vertices_created = self.vertices_created

        vertices_without_id = self.vertices_without_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bytes_read is not UNSET:
            field_dict["bytesRead"] = bytes_read
        if edges_created is not UNSET:
            field_dict["edgesCreated"] = edges_created
        if error is not UNSET:
            field_dict["error"] = error
        if exception is not UNSET:
            field_dict["exception"] = exception
        if lines_read is not UNSET:
            field_dict["linesRead"] = lines_read
        if lines_skipped is not UNSET:
            field_dict["linesSkipped"] = lines_skipped
        if partial_commit is not UNSET:
            field_dict["partialCommit"] = partial_commit
        if request_id is not UNSET:
            field_dict["requestId"] = request_id
        if vertices_created is not UNSET:
            field_dict["verticesCreated"] = vertices_created
        if vertices_without_id is not UNSET:
            field_dict["verticesWithoutId"] = vertices_without_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bytes_read = d.pop("bytesRead", UNSET)

        edges_created = d.pop("edgesCreated", UNSET)

        error = d.pop("error", UNSET)

        exception = d.pop("exception", UNSET)

        lines_read = d.pop("linesRead", UNSET)

        lines_skipped = d.pop("linesSkipped", UNSET)

        partial_commit = d.pop("partialCommit", UNSET)

        request_id = d.pop("requestId", UNSET)

        vertices_created = d.pop("verticesCreated", UNSET)

        vertices_without_id = d.pop("verticesWithoutId", UNSET)

        batch_error = cls(
            bytes_read=bytes_read,
            edges_created=edges_created,
            error=error,
            exception=exception,
            lines_read=lines_read,
            lines_skipped=lines_skipped,
            partial_commit=partial_commit,
            request_id=request_id,
            vertices_created=vertices_created,
            vertices_without_id=vertices_without_id,
        )

        batch_error.additional_properties = d
        return batch_error

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
