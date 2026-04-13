from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt

from app.services.confidence_service import score_inventory_position


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.7613
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * radius_miles * atan2(sqrt(a), sqrt(1 - a))


def build_alternative_nodes(
    positions: list,
    nodes_by_id: dict[str, object],
    *,
    primary_node: str | None = None,
    nearby_nodes: list[str] | None = None,
) -> list[dict]:
    if not primary_node or not nearby_nodes:
        return []

    primary = nodes_by_id.get(primary_node)
    nearby_set = set(nearby_nodes)
    alternatives: dict[str, dict] = {}

    for position in positions:
        node_id = position.fulfillment_node
        if node_id == primary_node or node_id not in nearby_set:
            continue

        node = nodes_by_id.get(node_id)
        if node is None or not getattr(node, "enabled", True) or not position.node_enabled:
            continue

        available_qty = max(int(position.available_qty or 0) - int(position.reserved_qty or 0), 0)
        if available_qty <= 0:
            continue

        distance = 0.0
        if primary is not None:
            distance = haversine_miles(
                float(primary.latitude),
                float(primary.longitude),
                float(node.latitude),
                float(node.longitude),
            )

        confidence = score_inventory_position(position)
        alternatives[node_id] = {
            "node_id": node_id,
            "node_name": node.node_name,
            "distance_miles": round(distance, 1),
            "available_qty": available_qty,
            "confidence_score": confidence["confidence_score"],
        }

    return sorted(
        alternatives.values(),
        key=lambda entry: (entry["distance_miles"], -entry["available_qty"], entry["node_id"]),
    )
