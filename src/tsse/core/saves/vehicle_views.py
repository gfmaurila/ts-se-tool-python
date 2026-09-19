"""Read-only, lossless projections of legacy vehicle and trailer blocks."""

from __future__ import annotations

from dataclasses import dataclass

from tsse.core.saves.vehicle_graph import inspect_accessories
from tsse.core.sii import SiiBlock, SiiDocument


class VehicleViewError(ValueError):
    """Raised when a requested vehicle or trailer block is absent."""


@dataclass(frozen=True, slots=True)
class LicensePlateView:
    """Legacy `plate|country` display data, without changing its raw SII text."""

    raw: str
    plate: str | None
    country: str | None
    valid: bool


@dataclass(frozen=True, slots=True)
class OdometerView:
    """The separate odometer fields stored by legacy `Vehicle`/`Trailer`."""

    integer_raw: str | None
    integer_value: int | None
    float_part_raw: str | None


@dataclass(frozen=True, slots=True)
class WheelWearView:
    """One indexed wear value; it deliberately has no wheel-accessory link."""

    index: int
    raw_value: str


@dataclass(frozen=True, slots=True)
class VehicleAccessoryView:
    reference: str
    data_path: str | None
    refund: int | None
    component_type: str


@dataclass(frozen=True, slots=True)
class WheelAccessoryView:
    reference: str
    data_path: str | None
    refund: int | None
    component_type: str
    offset: int | None
    paint_color_raw: str | None


@dataclass(frozen=True, slots=True)
class AddonAccessoryView:
    reference: str


@dataclass(frozen=True, slots=True)
class PaintAccessoryView:
    reference: str
    mask_r_color: str | None
    mask_g_color: str | None
    mask_b_color: str | None
    flake_color: str | None
    flip_color: str | None
    base_color: str | None
    data_path: str | None
    refund: int | None


@dataclass(frozen=True, slots=True)
class UnknownAccessoryView:
    reference: str
    block_type: str


@dataclass(frozen=True, slots=True)
class MissingAccessoryView:
    reference: str


AccessoryView = (
    VehicleAccessoryView
    | WheelAccessoryView
    | AddonAccessoryView
    | PaintAccessoryView
    | UnknownAccessoryView
    | MissingAccessoryView
)


@dataclass(frozen=True, slots=True)
class VehicleComponentsView:
    engine_wear: str | None
    transmission_wear: str | None
    chassis_wear: str | None
    cabin_wear: str | None
    wheels: tuple[WheelWearView, ...]


@dataclass(frozen=True, slots=True)
class TrailerComponentsView:
    cargo_damage: str | None
    body_wear: str | None
    chassis_wear: str | None
    wheels: tuple[WheelWearView, ...]


@dataclass(frozen=True, slots=True)
class VehicleView:
    identifier: str
    components: VehicleComponentsView
    fuel_relative: str | None
    accessories: tuple[AccessoryView, ...]
    license_plate: LicensePlateView | None
    odometer: OdometerView


@dataclass(frozen=True, slots=True)
class TrailerView:
    identifier: str
    components: TrailerComponentsView
    accessories: tuple[AccessoryView, ...]
    license_plate: LicensePlateView | None
    odometer: OdometerView
    slave_trailer_reference: str | None


def parse_license_plate(raw: str | None) -> LicensePlateView | None:
    """Mirror `SCSLicensePlate.CheckSourceText` without image/font loading."""
    if raw is None:
        return None
    value = _unquote(raw)
    parts = value.split("|")
    if len(parts) < 2:
        return LicensePlateView(raw, None, None, False)
    return LicensePlateView(raw, parts[0], parts[1].strip("_ "), True)


def build_vehicle_view(document: SiiDocument, identifier: str) -> VehicleView:
    """Project a `vehicle` block without altering the lossless document."""
    block = _require_block(document, identifier, "vehicle")
    wheels = _wheel_wear(block)
    return VehicleView(
        identifier=identifier,
        components=VehicleComponentsView(
            engine_wear=_field(block, "engine_wear"),
            transmission_wear=_field(block, "transmission_wear"),
            chassis_wear=_field(block, "chassis_wear"),
            cabin_wear=_field(block, "cabin_wear"),
            wheels=wheels,
        ),
        fuel_relative=_field(block, "fuel_relative"),
        accessories=_accessories(document, block),
        license_plate=parse_license_plate(_field(block, "license_plate")),
        odometer=_odometer(block),
    )


def build_trailer_view(document: SiiDocument, identifier: str) -> TrailerView:
    """Project one `trailer` block; slave chains are not traversed here."""
    block = _require_block(document, identifier, "trailer")
    wheels = _wheel_wear(block)
    return TrailerView(
        identifier=identifier,
        components=TrailerComponentsView(
            cargo_damage=_field(block, "cargo_damage"),
            body_wear=_field(block, "trailer_body_wear"),
            chassis_wear=_field(block, "chassis_wear"),
            wheels=wheels,
        ),
        accessories=_accessories(document, block),
        license_plate=parse_license_plate(_field(block, "license_plate")),
        odometer=_odometer(block),
        slave_trailer_reference=_field(block, "slave_trailer"),
    )


def _require_block(document: SiiDocument, identifier: str, expected_type: str) -> SiiBlock:
    block = next((item for item in document.blocks if item.identifier == identifier), None)
    if block is None:
        raise VehicleViewError(f"missing {expected_type}: {identifier}")
    if block.type_name != expected_type:
        raise VehicleViewError(f"expected {expected_type}, found {block.type_name}: {identifier}")
    return block


def _field(block: SiiBlock, key: str) -> str | None:
    return next((field.value for field in block.fields if field.key == key), None)


def _wheel_wear(block: SiiBlock) -> tuple[WheelWearView, ...]:
    return tuple(
        WheelWearView(field.array_index, field.value)
        for field in block.fields
        if field.name == "wheels_wear" and field.array_index is not None
    )


def _odometer(block: SiiBlock) -> OdometerView:
    integer_raw = _field(block, "odometer")
    try:
        integer_value = int(integer_raw) if integer_raw is not None else None
    except ValueError:
        integer_value = None
    return OdometerView(integer_raw, integer_value, _field(block, "odometer_float_part"))


def _accessories(document: SiiDocument, owner: SiiBlock) -> tuple[AccessoryView, ...]:
    result: list[AccessoryView] = []
    for _, typed_reference, target in inspect_accessories(document, owner):
        reference = typed_reference.raw
        if target is None:
            result.append(MissingAccessoryView(reference))
        elif target.type_name == "vehicle_accessory":
            result.append(_vehicle_accessory(target, reference))
        elif target.type_name == "vehicle_wheel_accessory":
            result.append(_wheel_accessory(target, reference))
        elif target.type_name == "vehicle_addon_accessory":
            result.append(AddonAccessoryView(reference))
        elif target.type_name == "vehicle_paint_job_accessory":
            result.append(_paint_accessory(target, reference))
        else:
            result.append(UnknownAccessoryView(reference, target.type_name))
    return tuple(result)


def _vehicle_accessory(block: SiiBlock, reference: str) -> VehicleAccessoryView:
    path = _field(block, "data_path")
    return VehicleAccessoryView(
        reference, path, _uint_or_none(_field(block, "refund")), _component_type(path)
    )


def _wheel_accessory(block: SiiBlock, reference: str) -> WheelAccessoryView:
    path = _field(block, "data_path")
    return WheelAccessoryView(
        reference,
        path,
        _uint_or_none(_field(block, "refund")),
        _wheel_component_type(path),
        _int_or_none(_field(block, "offset")),
        _field(block, "paint_color"),
    )


def _paint_accessory(block: SiiBlock, reference: str) -> PaintAccessoryView:
    return PaintAccessoryView(
        reference,
        _field(block, "mask_r_color"),
        _field(block, "mask_g_color"),
        _field(block, "mask_b_color"),
        _field(block, "flake_color"),
        _field(block, "flip_color"),
        _field(block, "base_color"),
        _field(block, "data_path"),
        _uint_or_none(_field(block, "refund")),
    )


def _component_type(path: str | None) -> str:
    value = _unquote(path) if path is not None else ""
    if "/data.sii" in value:
        return "basepart"
    for component in ("chassis", "body", "cabin", "engine", "transmission"):
        if component in value:
            return component
    return "generalpart"


def _wheel_component_type(path: str | None) -> str:
    value = _unquote(path) if path is not None else ""
    parts = ("/f_tire/", "/r_tire/", "/f_wheel/", "/r_wheel/", "/t_wheel/")
    if any(part in value for part in parts):
        return "tire"
    return "generalpart"


def _unquote(value: str) -> str:
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _uint_or_none(value: str | None) -> int | None:
    result = _int_or_none(value)
    return result if result is not None and result >= 0 else None
