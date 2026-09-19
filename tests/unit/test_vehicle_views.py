from tsse.core.saves.vehicle_views import (
    AddonAccessoryView,
    MissingAccessoryView,
    PaintAccessoryView,
    VehicleAccessoryView,
    WheelAccessoryView,
    build_trailer_view,
    build_vehicle_view,
    parse_license_plate,
)
from tsse.core.sii import parse_sii

SOURCE = """SiiNunit
{
vehicle : vehicle.one {
 engine_wear: &3f000000
 transmission_wear: 0.2
 chassis_wear: 0.3
 cabin_wear: 0.4
 fuel_relative: &3f800000
 wheels_wear: 2
 wheels_wear[0]: &3e000000
 wheels_wear[2]: 0.5
 accessories: 5
 accessories[0]: accessory.engine
 accessories[1]: accessory.wheel
 accessories[2]: accessory.addon
 accessories[3]: accessory.paint
 accessories[4]: accessory.missing
 license_plate: "AB-12|_portugal_ "
 odometer: 123
 odometer_float_part: &3e800000
 unknown_future: preserve
}
trailer : trailer.one {
 cargo_damage: 0.1
 trailer_body_wear: 0.2
 chassis_wear: 0.3
 wheels_wear: 1
 wheels_wear[3]: 0.6
 accessories: 1
 accessories[0]: accessory.paint
 license_plate: "T-1|texas"
 odometer: 9
 odometer_float_part: 0.2
 slave_trailer: trailer.two
}
vehicle_accessory : accessory.engine {
 data_path: "/def/vehicle/truck/foo/engine.sii"
 refund: 20
}
vehicle_wheel_accessory : accessory.wheel {
 offset: -1
 paint_color: (1, 2, 3)
 data_path: "/def/vehicle/truck/f_tire/foo.sii"
 refund: 30
}
vehicle_addon_accessory : accessory.addon {
 future: preserve
}
vehicle_paint_job_accessory : accessory.paint {
 mask_r_color: (1, 0, 0)
 mask_g_color: (0, 1, 0)
 mask_b_color: (0, 0, 1)
 flake_color: (0.1, 0.2, 0.3)
 flip_color: (0.4, 0.5, 0.6)
 base_color: (0.7, 0.8, 0.9)
 data_path: "/def/paint.sii"
 refund: 40
}
}
"""


def test_legacy_license_plate_parsing_is_read_only_and_handles_edge_cases() -> None:
    valid = parse_license_plate('"AB|_us__|ignored"')
    invalid = parse_license_plate('"no-separator"')

    assert valid is not None
    assert (valid.plate, valid.country, valid.valid) == ("AB", "us", True)
    assert invalid is not None
    assert (invalid.plate, invalid.country, invalid.valid) == (None, None, False)
    assert parse_license_plate(None) is None


def test_vehicle_view_projects_legacy_fields_without_changing_document() -> None:
    document = parse_sii(SOURCE)
    original = document.serialize()
    view = build_vehicle_view(document, "vehicle.one")

    assert view.components.engine_wear == "&3f000000"
    assert view.components.chassis_wear == "0.3"
    assert [(wheel.index, wheel.raw_value) for wheel in view.components.wheels] == [
        (0, "&3e000000"),
        (2, "0.5"),
    ]
    assert view.fuel_relative == "&3f800000"
    assert view.license_plate is not None
    assert (view.license_plate.plate, view.license_plate.country) == ("AB-12", "portugal")
    assert (view.odometer.integer_value, view.odometer.float_part_raw) == (123, "&3e800000")
    assert document.serialize() == original


def test_accessories_are_polymorphic_and_missing_reference_is_explicit() -> None:
    view = build_vehicle_view(parse_sii(SOURCE), "vehicle.one")
    engine, wheel, addon, paint, missing = view.accessories

    assert isinstance(engine, VehicleAccessoryView)
    assert (engine.component_type, engine.refund) == ("engine", 20)
    assert isinstance(wheel, WheelAccessoryView)
    assert (wheel.component_type, wheel.offset, wheel.paint_color_raw) == ("tire", -1, "(1, 2, 3)")
    assert isinstance(addon, AddonAccessoryView)
    assert isinstance(paint, PaintAccessoryView)
    assert paint.base_color == "(0.7, 0.8, 0.9)"
    assert (paint.data_path, paint.refund) == ('"/def/paint.sii"', 40)
    assert isinstance(missing, MissingAccessoryView)
    assert missing.reference == "accessory.missing"


def test_trailer_view_preserves_slave_reference_and_optional_fields() -> None:
    document = parse_sii(SOURCE)
    original = document.serialize()
    view = build_trailer_view(document, "trailer.one")

    values = (
        view.components.cargo_damage,
        view.components.body_wear,
        view.components.chassis_wear,
    )
    assert values == (
        "0.1",
        "0.2",
        "0.3",
    )
    assert [(wheel.index, wheel.raw_value) for wheel in view.components.wheels] == [(3, "0.6")]
    assert view.slave_trailer_reference == "trailer.two"
    assert isinstance(view.accessories[0], PaintAccessoryView)
    assert document.serialize() == original


def test_missing_optional_fields_remain_none_without_defaults() -> None:
    source = "SiiNunit\n{\nvehicle : bare {\n accessories: 0\n}\n}\n"
    view = build_vehicle_view(parse_sii(source), "bare")

    assert view.license_plate is None
    assert view.odometer.integer_raw is None
    assert view.odometer.float_part_raw is None
    assert view.components.wheels == ()
