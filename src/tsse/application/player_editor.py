"""Conservative in-memory edits for proven player fields."""

from __future__ import annotations

import re

from tsse.core.sii import SiiBlock, SiiDocument, SiiField, parse_sii


class PlayerEditError(ValueError):
    """Raised when a requested player field is missing or invalid."""


_SKILLS = frozenset({"adr", "long_distance", "heavy", "fragile", "urgent", "mechanical"})
_LEVEL_STEPS = {
    "ets2": (200, 500, 700, 900, 1000, 1100, 1300, 1600, 1700, 2100, 2300, 2600, 2700,
             2900, 3000, 3100, 3400, 3700, 4000, 4300, 4600, 4700, 4900, 5200, 5700, 5900,
             6000, 6200, 6600, 6800),
    "ats": (200, 500, 700, 900, 1100, 1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700,
            2900, 3100, 3300, 3500, 3700, 4000, 4300, 4600, 4900, 5200, 5500, 5800, 6100,
            6400, 6700, 7000, 7300),
}


def level_to_experience(game: str, level: int) -> int:
    """Port legacy ``Economy.setPlayerExp`` including its 0..150 clamp."""
    steps = _level_steps(game)
    bounded = min(150, max(0, level))
    return sum(steps[min(index, len(steps) - 1)] for index in range(bounded + 1)) - 1


def experience_to_level(game: str, experience: int) -> tuple[int, int]:
    """Port legacy ``Economy.getPlayerLvl``: return level and next threshold."""
    if experience < 0:
        raise PlayerEditError("experience must be non-negative")
    steps = _level_steps(game)
    threshold = 0
    level = 0
    for step in steps:
        threshold += step
        if experience < threshold:
            return level, threshold
        level += 1
    while True:
        threshold += steps[-1]
        if experience < threshold:
            return level, threshold
        level += 1


def _level_steps(game: str) -> tuple[int, ...]:
    try:
        return _LEVEL_STEPS[game.lower()]
    except KeyError as error:
        raise PlayerEditError(f"unsupported game for level conversion: {game}") from error


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


def set_gender(document: SiiDocument, male: bool) -> SiiDocument:
    """Set legacy ``user_profile.male`` as lowercase SII boolean text."""
    if not isinstance(male, bool):
        raise PlayerEditError("male must be a boolean")
    return _replace_field(document, "user_profile", "male", str(male).lower())


def set_company_name(document: SiiDocument, name: str) -> SiiDocument:
    """Set legacy company name; its UI accepts 1..20 characters."""
    if not 1 <= len(name) <= 20:
        raise PlayerEditError("company name must contain 1 to 20 characters")
    return _replace_field(document, "user_profile", "company_name", f'"{name}"')


def set_hq_city(document: SiiDocument, city: str) -> SiiDocument:
    """Set HQ reference; legacy UI sources candidates from owned garages."""
    if not city:
        raise PlayerEditError("HQ city ID must not be empty")
    return _replace_field(document, "player", "hq_city", city)


def unlock_dealer(document: SiiDocument, dealer: str) -> SiiDocument:
    return _append_unique(document, "unlocked_dealers", dealer)


def unlock_recruitment(document: SiiDocument, agency: str) -> SiiDocument:
    return _append_unique(document, "unlocked_recruitments", agency)


def visit_city(document: SiiDocument, city: str) -> SiiDocument:
    """Add a legacy visited-city pair; new cities receive visit count one."""
    if not city:
        raise PlayerEditError("city ID must not be empty")
    cities = _fields(document, "economy", "visited_cities")
    counts = _fields(document, "economy", "visited_cities_count")
    city_items = [field for field in cities if field.array_index is not None]
    count_items = [field for field in counts if field.array_index is not None]
    if len(city_items) != len(count_items):
        raise PlayerEditError("visited city arrays are inconsistent")
    if city in [field.value for field in city_items]:
        return document
    return _replace_collection_pair(document, city_items + [city], count_items + ["1"])


def resolve_driver(document: SiiDocument, index: int) -> SiiBlock:
    """Resolve a player driver reference to its actual SII block type."""
    drivers = _fields(document, "player", "drivers")
    readiness = _fields(document, "player", "driver_readiness_timer")
    driver_items = [field for field in drivers if field.array_index is not None]
    readiness_items = [field for field in readiness if field.array_index is not None]
    if len(driver_items) != len(readiness_items):
        raise PlayerEditError("driver and readiness arrays are inconsistent")
    reference = next((field.value for field in driver_items if field.array_index == index), None)
    if reference is None:
        raise PlayerEditError(f"driver index does not exist: {index}")
    block = next((item for item in document.blocks if item.identifier == reference), None)
    if block is None:
        raise PlayerEditError(f"driver reference is missing: {reference}")
    if block.type_name not in {"driver_player", "driver_ai"}:
        raise PlayerEditError(f"driver reference has unexpected type: {block.type_name}")
    return block


def _replace_collection_pair(
    document: SiiDocument, cities: list[SiiField | str], counts: list[SiiField | str]
) -> SiiDocument:
    source = document.source
    for name, values in (("visited_cities", cities), ("visited_cities_count", counts)):
        pattern = re.compile(rf"(?m)^\s*{name}:.*\n(?:\s*{name}\[\d+]:.*\n)*")
        replacement = f" {name}: {len(values)}\n" + "".join(
            f" {name}[{index}]: {value.value if isinstance(value, SiiField) else value}\n"
            for index, value in enumerate(values)
        )
        source, changed = pattern.subn(replacement, source, count=1)
        if changed != 1:
            raise PlayerEditError(f"missing economy.{name} collection")
    return parse_sii(source)


def _fields(document: SiiDocument, block_type: str, name: str) -> list[SiiField]:
    block = next((item for item in document.blocks if item.type_name == block_type), None)
    if block is None:
        raise PlayerEditError(f"missing {block_type} block")
    return [field for field in block.fields if field.name == name]


def _append_unique(document: SiiDocument, name: str, value: str) -> SiiDocument:
    if not value:
        raise PlayerEditError(f"{name} ID must not be empty")
    fields = _fields(document, "economy", name)
    if not fields:
        raise PlayerEditError(f"missing economy.{name}")
    entries = [field.value for field in fields if field.array_index is not None]
    if value in entries:
        return document
    count = next((field for field in fields if field.array_index is None), None)
    if count is None:
        raise PlayerEditError(f"missing economy.{name} count")
    source = _replace_field(document, "economy", name, str(len(entries) + 1)).source
    line = f" {name}[{len(entries)}]: {value}\n"
    marker = re.compile(rf"(?m)^(?P<line>\s*{re.escape(name)}\[\d+]:.*\n)")
    matches = list(marker.finditer(source))
    if not matches:
        raise PlayerEditError(f"missing economy.{name} entries")
    result = source[:matches[-1].end()] + line + source[matches[-1].end():]
    return parse_sii(result)


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
