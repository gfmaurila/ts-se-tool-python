"""Lossless Freight Market job preparation based on the legacy writer."""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass

from tsse.core.sii import SiiBlock, SiiDocument, parse_sii


class FreightMarketError(ValueError):
    """Raised for invalid company/job references or job parameters."""


RandomSource = Callable[[int, int], int]


@dataclass(frozen=True)
class JobOfferPayload:
    """The fields written by DataManipulation.PrepareCompaniesJobWrite."""

    target: str
    expiration_time: int
    urgency: int
    shortest_distance_km: int
    ferry_time: int
    ferry_price: int
    cargo: str
    company_truck: str
    trailer_variant: str
    trailer_definition: str
    units_count: int


def resolve_job_offer(document: SiiDocument, company_id: str, index: int) -> SiiBlock:
    company = _resolve_company(document, company_id)
    references = _collection(company, "job_offer")
    if index < 0 or index >= len(references):
        raise FreightMarketError(f"job_offer index does not exist: {index}")
    reference = references[index]
    block = _blocks(document).get(reference)
    if block is None:
        raise FreightMarketError(f"job_offer_data reference is missing: {reference}")
    if block.type_name != "job_offer_data":
        raise FreightMarketError(f"job offer has unexpected type: {block.type_name}")
    return block


def write_job_offer(
    document: SiiDocument,
    company_id: str,
    index: int,
    payload: JobOfferPayload,
) -> SiiDocument:
    """Apply the legacy writer to an existing indexed job offer block.

    The legacy has no block/ID allocator here: it writes into the existing
    reference at ``company.job_offer[index]``.
    """
    block = resolve_job_offer(document, company_id, index)
    _validate_payload(payload)
    fields = {
        "target": _quoted_target(payload.target),
        "expiration_time": str(payload.expiration_time),
        "urgency": str(payload.urgency),
        "shortest_distance_km": str(payload.shortest_distance_km),
        "ferry_time": str(payload.ferry_time),
        "ferry_price": str(payload.ferry_price),
        "cargo": _prefixed(payload.cargo, "cargo."),
        "company_truck": payload.company_truck,
        "trailer_variant": payload.trailer_variant,
        "trailer_definition": payload.trailer_definition,
        "units_count": str(payload.units_count),
    }
    edited = _replace_scalars(document, block.identifier, fields)
    return _update_matching_events(edited, company_id, index, payload.expiration_time)


def expiration_time(
    game_time: int,
    random_source: RandomSource = random.randrange,
    jobs_amount_added: int = 0,
    job_pickup_time_minutes: int = 0,
) -> int:
    """Reproduce AddCargo's expiration calculation."""
    if game_time < 0 or jobs_amount_added < 0 or job_pickup_time_minutes < 0:
        raise FreightMarketError("expiration inputs must be non-negative")
    offset = random_source(180, 1800)
    if not isinstance(offset, int) or not 180 <= offset < 1800:
        raise FreightMarketError("random source returned an invalid expiration offset")
    return game_time + offset + jobs_amount_added * job_pickup_time_minutes * 60


def clear_pending_jobs(_pending_jobs: object) -> tuple[object, ...]:
    """ClearJobData: discard the UI queue; it does not mutate the save AST."""
    return ()


def _validate_payload(payload: JobOfferPayload) -> None:
    if payload.expiration_time < 0 or payload.urgency < 0:
        raise FreightMarketError("expiration_time and urgency must be non-negative")
    if payload.shortest_distance_km < 0 or payload.ferry_time < 0 or payload.ferry_price < 0:
        raise FreightMarketError("route values must be non-negative")
    if payload.units_count < 0:
        raise FreightMarketError("units_count must be non-negative")
    for name in ("target", "cargo", "company_truck", "trailer_variant", "trailer_definition"):
        if not getattr(payload, name):
            raise FreightMarketError(f"{name} is required")


def _resolve_company(document: SiiDocument, identifier: str) -> SiiBlock:
    block = _blocks(document).get(identifier)
    if block is None:
        raise FreightMarketError(f"company reference is missing: {identifier}")
    if block.type_name != "company":
        raise FreightMarketError(f"company has unexpected type: {block.type_name}")
    return block


def _collection(block: SiiBlock, name: str) -> list[str]:
    count_field = next((field for field in block.fields if field.key == name), None)
    if count_field is None:
        raise FreightMarketError(f"missing {block.type_name}.{name}")
    try:
        count = int(count_field.value)
    except ValueError as error:
        raise FreightMarketError(f"invalid {block.type_name}.{name} count") from error
    values = {
        field.array_index: field.value
        for field in block.fields
        if field.name == name and field.array_index is not None
    }
    if count < 0 or sorted(values) != list(range(count)):
        raise FreightMarketError(f"inconsistent {block.type_name}.{name} collection")
    return [values[index] for index in range(count)]


def _blocks(document: SiiDocument) -> dict[str, SiiBlock]:
    return {block.identifier: block for block in document.blocks}


def _quoted_target(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return value
    return f'"{value}"'


def _prefixed(value: str, prefix: str) -> str:
    return value if value.startswith(prefix) else prefix + value


def _replace_scalars(
    document: SiiDocument, identifier: str, values: dict[str, str]
) -> SiiDocument:
    block = _blocks(document).get(identifier)
    if block is None or block.type_name != "job_offer_data":
        raise FreightMarketError(f"missing job_offer_data block: {identifier}")
    missing = [name for name in values if not any(field.key == name for field in block.fields)]
    if missing:
        raise FreightMarketError(f"missing job_offer_data fields: {', '.join(missing)}")
    source = document.source
    header = re.escape(f"job_offer_data : {identifier} {{")
    match = re.search(rf"(?s)({header})(?P<body>.*?)(^}})", source, re.MULTILINE)
    if match is None:
        raise FreightMarketError(f"could not locate job_offer_data source: {identifier}")
    body = match.group("body")
    for name, value in values.items():
        body, count = re.subn(
            rf"(?m)^([ \t]*){re.escape(name)}:.*$",
            rf"\g<1>{name}: {value}",
            body,
            count=1,
        )
        if count != 1:
            raise FreightMarketError(f"could not update job_offer_data.{name}")
    source = source[: match.start("body")] + body + source[match.end("body") :]
    return parse_sii(source)


def _update_matching_events(
    document: SiiDocument, company_id: str, index: int, expiration: int
) -> SiiDocument:
    """Mirror PrepareEvents for queued jobs; unrelated events stay untouched."""
    current = document
    for event in current.blocks:
        if event.type_name != "economy_event":
            continue
        unit_link = next((field.value for field in event.fields if field.key == "unit_link"), None)
        param = next((field.value for field in event.fields if field.key == "param"), None)
        if unit_link != company_id or param != str(index):
            continue
        if not any(field.key == "time" for field in event.fields):
            raise FreightMarketError(f"economy_event.time is missing: {event.identifier}")
        current = _replace_one_scalar(current, event.identifier, "time", str(expiration))
    return current


def _replace_one_scalar(
    document: SiiDocument, identifier: str, name: str, value: str
) -> SiiDocument:
    block = _blocks(document).get(identifier)
    if block is None:
        raise FreightMarketError(f"missing block during event mutation: {identifier}")
    header = re.escape(f"{block.type_name} : {identifier} {{")
    match = re.search(rf"(?s)({header})(?P<body>.*?)(^}})", document.source, re.MULTILINE)
    if match is None:
        raise FreightMarketError(f"could not locate event source: {identifier}")
    body, count = re.subn(
        rf"(?m)^([ \t]*){re.escape(name)}:.*$",
        rf"\g<1>{name}: {value}",
        match.group("body"),
        count=1,
    )
    if count != 1:
        raise FreightMarketError(f"could not update {block.type_name}.{name}")
    source = document.source[: match.start("body")] + body + document.source[match.end("body") :]
    return parse_sii(source)
