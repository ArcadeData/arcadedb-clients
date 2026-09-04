from enum import Enum


class ExecuteBatchRefMode(str, Enum):
    ID = "id"
    ORDINAL = "ordinal"

    def __str__(self) -> str:
        return str(self.value)
