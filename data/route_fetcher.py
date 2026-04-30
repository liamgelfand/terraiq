"""
Fetches a real-world route between two coordinates using OSMnx, then overlays
elevation data from the Open-Meteo elevation API to produce a grade profile.

Route data is cached to disk in data/route_cache/ so subsequent runs skip all
network requests. Delete the cache file for a route to force a fresh fetch.
"""

import hashlib
import math
import pickle
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import osmnx as ox
import requests

# Open-Meteo elevation: free, no API key, accepts up to 100 coords per request
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
ELEVATION_BATCH_SIZE = 100

CACHE_DIR = Path(__file__).parent / "route_cache"


@dataclass
class RoutePoint:
    distance_m: float       # cumulative distance from origin (meters)
    lat: float
    lon: float
    elevation_m: float
    grade: float            # rise/run (dimensionless); positive = uphill
    speed_limit_ms: float   # speed limit in m/s


def fetch_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    network_type: str = "drive",
    default_speed_limit_kmh: float = 90.0,
) -> list[RoutePoint]:
    """
    Pull the shortest road-network path between origin and destination.

    Results are cached to disk in data/route_cache/. On subsequent calls with
    the same arguments the cache is loaded instantly, skipping all API calls.

    Args:
        origin: (lat, lon) of start point
        destination: (lat, lon) of end point
        network_type: OSMnx network type ("drive", "bike", "walk")
        default_speed_limit_kmh: fallback speed limit when OSM data is missing

    Returns:
        List of RoutePoint objects with distance, elevation, grade, speed limit.
    """
    cache_key = hashlib.md5(
        f"{origin}{destination}{network_type}{default_speed_limit_kmh}".encode()
    ).hexdigest()[:12]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{cache_key}.pkl"

    if cache_path.exists():
        print(f"Loading route from cache ({cache_path.name})...", flush=True)
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    route_points = _fetch_route_from_network(origin, destination, network_type, default_speed_limit_kmh)

    with open(cache_path, "wb") as f:
        pickle.dump(route_points, f)
    print(f"Route cached to {cache_path.name}", flush=True)

    return route_points


def _fetch_route_from_network(
    origin: tuple[float, float],
    destination: tuple[float, float],
    network_type: str,
    default_speed_limit_kmh: float,
) -> list[RoutePoint]:
    """Fetch route from OSMnx + elevation API (no caching)."""
    print(f"Fetching road network around route...", flush=True)
    padding_deg = 0.05  # ~5 km buffer around the bounding box
    min_lat = min(origin[0], destination[0]) - padding_deg
    max_lat = max(origin[0], destination[0]) + padding_deg
    min_lon = min(origin[1], destination[1]) - padding_deg
    max_lon = max(origin[1], destination[1]) + padding_deg

    highway_filter = (
        '["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link'
        '|secondary|secondary_link"]'
    )

    graph = ox.graph_from_bbox(
        (min_lon, min_lat, max_lon, max_lat),
        custom_filter=highway_filter,
        simplify=True,
    )
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)

    origin_node = ox.nearest_nodes(graph, X=origin[1], Y=origin[0])
    dest_node = ox.nearest_nodes(graph, X=destination[1], Y=destination[0])

    print("Computing shortest path...", flush=True)
    path_nodes = ox.shortest_path(graph, origin_node, dest_node, weight="length")
    if path_nodes is None:
        raise ValueError("No path found between the given coordinates.")

    coords = _extract_coords(graph, path_nodes)
    distances = _cumulative_distances(coords)
    speed_limits = _extract_speed_limits(graph, path_nodes, default_speed_limit_kmh)

    print(f"Route has {len(coords)} points, total distance: {distances[-1]/1000:.1f} km", flush=True)
    print("Fetching elevation data...", flush=True)
    elevations = _fetch_elevations(coords)

    grades = _compute_grades(distances, elevations)

    route_points = []
    for coord, dist, elev, grade, speed_ms in zip(
        coords, distances, elevations, grades, speed_limits
    ):
        route_points.append(RoutePoint(
            distance_m=dist,
            lat=coord[0],
            lon=coord[1],
            elevation_m=elev,
            grade=grade,
            speed_limit_ms=speed_ms,
        ))

    return route_points


def _extract_coords(graph, path_nodes: list) -> list[tuple[float, float]]:
    """Return (lat, lon) for each node in the path."""
    node_data = graph.nodes(data=True)
    return [(node_data[n]["y"], node_data[n]["x"]) for n in path_nodes]


def _extract_speed_limits(
    graph, path_nodes: list, default_kmh: float
) -> list[float]:
    """
    Return speed limit in m/s for each node, derived from the edge leading
    into that node. First node inherits the second node's speed limit.
    """
    default_ms = default_kmh / 3.6
    speed_limits_ms = [default_ms]

    for i in range(1, len(path_nodes)):
        u, v = path_nodes[i - 1], path_nodes[i]
        edge_data = graph.get_edge_data(u, v)
        if edge_data is None:
            speed_limits_ms.append(default_ms)
            continue
        # OSMnx stores speed_kph as a float after add_edge_speeds()
        key = min(edge_data.keys())
        speed_kph = edge_data[key].get("speed_kph", default_kmh)
        if isinstance(speed_kph, list):
            speed_kph = min(speed_kph)
        speed_limits_ms.append(float(speed_kph) / 3.6)

    return speed_limits_ms


def _cumulative_distances(coords: list[tuple[float, float]]) -> list[float]:
    """Return cumulative distances in meters along the route."""
    distances = [0.0]
    for i in range(1, len(coords)):
        d = _haversine_m(coords[i - 1], coords[i])
        distances.append(distances[-1] + d)
    return distances


def _fetch_elevations(coords: list[tuple[float, float]]) -> list[float]:
    """
    Fetch elevations from Open-Meteo elevation API in batches.

    Open-Meteo is free, requires no API key, and accepts up to 100 lat/lon
    pairs per request as comma-separated query parameters.
    Falls back to 0.0 m on any request failure (with a warning).
    """
    elevations = []
    for batch_start in range(0, len(coords), ELEVATION_BATCH_SIZE):
        batch = coords[batch_start : batch_start + ELEVATION_BATCH_SIZE]
        lats = ",".join(f"{lat:.6f}" for lat, _ in batch)
        lons = ",".join(f"{lon:.6f}" for _, lon in batch)
        try:
            response = requests.get(
                ELEVATION_URL,
                params={"latitude": lats, "longitude": lons},
                timeout=30,
            )
            response.raise_for_status()
            elevations.extend(response.json()["elevation"])
        except Exception as e:
            print(f"  Elevation API error for batch {batch_start}: {e}. Using 0m.", flush=True)
            elevations.extend([0.0] * len(batch))
        time.sleep(0.05)

    return elevations


def _compute_grades(
    distances: list[float], elevations: list[float]
) -> list[float]:
    """
    Compute road grade (rise/run) at each point using central differences.
    First and last points use forward/backward difference respectively.
    Grade is clamped to [-0.20, 0.20] (20% max — beyond this OSM data is likely wrong).
    """
    n = len(distances)
    grades = []
    for i in range(n):
        if i == 0:
            dx = distances[1] - distances[0]
            dz = elevations[1] - elevations[0]
        elif i == n - 1:
            dx = distances[-1] - distances[-2]
            dz = elevations[-1] - elevations[-2]
        else:
            dx = distances[i + 1] - distances[i - 1]
            dz = elevations[i + 1] - elevations[i - 1]

        grade = (dz / dx) if dx > 0.1 else 0.0
        grade = max(-0.20, min(0.20, grade))
        grades.append(grade)

    return grades


def _haversine_m(
    point_a: tuple[float, float], point_b: tuple[float, float]
) -> float:
    """Haversine distance in meters between two (lat, lon) points."""
    R = 6_371_000
    lat1, lon1 = math.radians(point_a[0]), math.radians(point_a[1])
    lat2, lon2 = math.radians(point_b[0]), math.radians(point_b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))
