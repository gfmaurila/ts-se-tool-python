"""Conservative in-memory edits for proven player fields."""

from __future__ import annotations

import re

from tsse.core.sii import SiiDocument, parse_sii


class PlayerEditError(ValueError):
    """Raised when a requested player field is missing or invalid."""


_SKILLS = frozenset({"adr", "long_distance", "heavy", "fragile", "urgent", "mechanical"})


def set_experience(document: SiiDocument, experience: int) -> SiiDocument:
    """Set proven `economy.experience_points` without changing other fields."""
    if experience < 0:
        raise PlayerEditError("experience must be non-negative")
    return _replace_field(document, "economy", "experience_points", str(experience))


def set_money(document: SiiDocument, money: int) -> SiiDocument:
    """Set proven `bank.money_account` without changing other fields."""
    return _replace_field(document, "bank", "money_account", str(money))


def set_skill(document: SiiDocument, skill: str, value: int) -> SiiDocument:
    """Set a proven economy skill with legacy's zero-to-six range."""
    if skill not in _SKILLS:
        raise PlayerEditError(f"unsupported player skill: {skill}")
    if not 0 <= value <= 6:
        raise PlayerEditError("skill value must be between 0 and 6")
    return _replace_field(document, "economy", skill, str(value))


def _replace_field(document: SiiDocument, block_type: str, key: str, value: str) -> SiiDocument:
    block = next((item for item in document.blocks if item.type_name == block_type), None)
    if block is None:
        raise PlayerEditError(f"missing {block_type} block")
    if not any(field.key == key for field in block.fields):
        raise PlayerEditError(f"missing {block_type}.{key}")
    pattern = re.compile(
        rf"(?m)^(?P<prefix>\s*{re.escape(key)}\s*:\s*)[^\r\n]*(?P<ending>\r?\n|$)"
    )
    source, count = pattern.subn(rf"\g<prefix>{value}\g<ending>", document.source, count=1)
    if count != 1:
        raise PlayerEditError(f"could not update {block_type}.{key}")
    return parse_sii(source)
