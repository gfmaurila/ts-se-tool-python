"""Domain view of the proven editable vehicle fields."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Truck:
    """A vehicle identity and its supported condition fields."""

    identifier: str
    engine_wear: int
    transmission_wear: int
    cabin_wear: int
    fuel_relative: float
