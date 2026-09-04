from enum import Enum


class WriteTimeSeriesPrecision(str, Enum):
    MS = "ms"
    NS = "ns"
    S = "s"
    US = "us"

    def __str__(self) -> str:
        return str(self.value)
