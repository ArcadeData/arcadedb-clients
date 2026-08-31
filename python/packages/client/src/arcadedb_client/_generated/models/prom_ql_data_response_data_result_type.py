from enum import Enum


class PromQLDataResponseDataResultType(str, Enum):
    MATRIX = "matrix"
    SCALAR = "scalar"
    VECTOR = "vector"

    def __str__(self) -> str:
        return str(self.value)
