from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProgressResponseResultItem")


@_attrs_define
class ProgressResponseResultItem:
    """One in-progress operation

    Attributes:
        database (str | Unset): Database the operation runs on
        done (int | Unset): Units completed in the current step
        elapsed_ms (int | Unset): Elapsed time in milliseconds
        id (int | Unset): Operation identifier
        operation (str | Unset): Operation name, for example CHECK DATABASE
        percentage (int | Unset): Completion percentage of the current step, -1 when the total is unknown
        started_on (int | Unset): Start time as epoch milliseconds
        step_index (int | Unset): Current step, 0-based
        step_name (str | Unset): Current step name
        total (int | Unset): Units in the current step, -1 when unknown
        total_steps (int | Unset): Total number of steps
    """

    database: str | Unset = UNSET
    done: int | Unset = UNSET
    elapsed_ms: int | Unset = UNSET
    id: int | Unset = UNSET
    operation: str | Unset = UNSET
    percentage: int | Unset = UNSET
    started_on: int | Unset = UNSET
    step_index: int | Unset = UNSET
    step_name: str | Unset = UNSET
    total: int | Unset = UNSET
    total_steps: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        database = self.database

        done = self.done

        elapsed_ms = self.elapsed_ms

        id = self.id

        operation = self.operation

        percentage = self.percentage

        started_on = self.started_on

        step_index = self.step_index

        step_name = self.step_name

        total = self.total

        total_steps = self.total_steps

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if database is not UNSET:
            field_dict["database"] = database
        if done is not UNSET:
            field_dict["done"] = done
        if elapsed_ms is not UNSET:
            field_dict["elapsedMs"] = elapsed_ms
        if id is not UNSET:
            field_dict["id"] = id
        if operation is not UNSET:
            field_dict["operation"] = operation
        if percentage is not UNSET:
            field_dict["percentage"] = percentage
        if started_on is not UNSET:
            field_dict["startedOn"] = started_on
        if step_index is not UNSET:
            field_dict["stepIndex"] = step_index
        if step_name is not UNSET:
            field_dict["stepName"] = step_name
        if total is not UNSET:
            field_dict["total"] = total
        if total_steps is not UNSET:
            field_dict["totalSteps"] = total_steps

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        database = d.pop("database", UNSET)

        done = d.pop("done", UNSET)

        elapsed_ms = d.pop("elapsedMs", UNSET)

        id = d.pop("id", UNSET)

        operation = d.pop("operation", UNSET)

        percentage = d.pop("percentage", UNSET)

        started_on = d.pop("startedOn", UNSET)

        step_index = d.pop("stepIndex", UNSET)

        step_name = d.pop("stepName", UNSET)

        total = d.pop("total", UNSET)

        total_steps = d.pop("totalSteps", UNSET)

        progress_response_result_item = cls(
            database=database,
            done=done,
            elapsed_ms=elapsed_ms,
            id=id,
            operation=operation,
            percentage=percentage,
            started_on=started_on,
            step_index=step_index,
            step_name=step_name,
            total=total,
            total_steps=total_steps,
        )

        progress_response_result_item.additional_properties = d
        return progress_response_result_item

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
