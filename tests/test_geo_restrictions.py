"""Unit tests for geo restriction helpers."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "services",
        "eligibility-service",
    ),
)

from app.services.geo_service import point_in_polygon, zone_matches


def test_point_in_polygon_accepts_object_points():
    polygon = [
        {"lat": 32.7800, "lng": -96.8050},
        {"lat": 32.7850, "lng": -96.8050},
        {"lat": 32.7850, "lng": -96.7970},
        {"lat": 32.7800, "lng": -96.7970},
    ]
    assert point_in_polygon(32.7825, -96.8010, polygon) is True
    assert point_in_polygon(32.7900, -96.7900, polygon) is False


def test_zone_matches_polygon_zone():
    zone = SimpleNamespace(
        hex_cells=[],
        geometry_type="polygon",
        center_latitude=None,
        center_longitude=None,
        radius_meters=None,
        polygon_coordinates=[
            {"lat": 32.7800, "lng": -96.8050},
            {"lat": 32.7850, "lng": -96.8050},
            {"lat": 32.7850, "lng": -96.7970},
            {"lat": 32.7800, "lng": -96.7970},
        ],
    )
    assert zone_matches(zone, {"latitude": 32.7825, "longitude": -96.8010}) is True

