"""Domain view for proven garage fields."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Garage:
    """A garage identity and its legacy status value."""

    identifier: str
    status: int
