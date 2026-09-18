"""Domain view of proven editable trailer condition fields."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Trailer:
    """A trailer identity and legacy repairable condition values."""

    identifier: str
    cargo_damage: float
    body_wear: float
    chassis_wear: float
