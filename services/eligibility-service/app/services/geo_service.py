from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geo_restriction_zone import GeoRestrictionZone


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return radius_miles * c


def _normalize_polygon(polygon: list) -> list[tuple[float, float]]:
    normalized: list[tuple[float, float]] = []
    for point in polygon or []:
        if isinstance(point, dict):
            normalized.append((float(point["lat"]), float(point["lng"])))
        else:
            lat, lon = point
            normalized.append((float(lat), float(lon)))
    return normalized


def point_in_polygon(latitude: float, longitude: float, polygon: list) -> bool:
    if not polygon:
        return False
    normalized = _normalize_polygon(polygon)
    inside = False
    j = len(normalized) - 1
    for i, point in enumerate(normalized):
        lat_i, lon_i = point
        lat_j, lon_j = normalized[j]
        denominator = lon_j - lon_i
        if abs(denominator) < 1e-9:
            denominator = 1e-9
        intersects = ((lon_i > longitude) != (lon_j > longitude)) and (
            latitude < (lat_j - lat_i) * (longitude - lon_i) / denominator + lat_i
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def zone_matches(zone: GeoRestrictionZone, customer_location: dict) -> bool:
    address_id = customer_location.get("address_id")
    latitude = customer_location.get("latitude")
    longitude = customer_location.get("longitude")

    if address_id and zone.hex_cells and address_id in zone.hex_cells:
        return True

    if latitude is None or longitude is None:
        return False

    if zone.geometry_type == "radius" and zone.center_latitude is not None and zone.center_longitude is not None:
        miles = haversine_miles(latitude, longitude, zone.center_latitude, zone.center_longitude)
        return miles * 1609.34 <= float(zone.radius_meters or 0)

    if zone.geometry_type == "polygon":
        return point_in_polygon(latitude, longitude, zone.polygon_coordinates or [])

    return False


async def find_matching_zones(
    db: AsyncSession,
    market_code: str,
    customer_location: dict,
    fulfillment_path: str,
) -> list[GeoRestrictionZone]:
    result = await db.execute(
        select(GeoRestrictionZone).where(
            GeoRestrictionZone.market_code == market_code,
            GeoRestrictionZone.active.is_(True),
        )
    )
    zones = result.scalars().all()
    matches = []
    for zone in zones:
        if zone.blocked_paths and fulfillment_path not in zone.blocked_paths:
            continue
        if zone_matches(zone, customer_location):
            matches.append(zone)
    return matches
