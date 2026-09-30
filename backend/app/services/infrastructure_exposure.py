import json
import math
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)


# ============================================================
# DISTANCE
# ============================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate distance between two coordinates
    using the Haversine formula.
    """

    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(
        lat2 - lat1
    )

    dlon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1_rad)
        *
        math.cos(lat2_rad)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# CACHE PATH
# ============================================================

def get_infrastructure_cache_path(
    latitude: float,
    longitude: float,
    radius_km: float
):
    """
    Get the processed infrastructure JSON path.

    Uses the same filename convention as the
    infrastructure downloader/cache creator.
    """

    lat_string = str(latitude)

    lon_string = str(longitude)

    # IMPORTANT:
    # 10.0 -> "10"
    # 10.5 -> "10.5"
    #
    # This must match infrastructure.py
    # which creates:
    #
    # infrastructure_19.8135_85.8312_10km.json

    radius_string = f"{radius_km:g}"

    filename = (
        f"infrastructure_"
        f"{lat_string}_"
        f"{lon_string}_"
        f"{radius_string}km.json"
    )

    return PROCESSED_DIR / filename

# ============================================================
# LOAD INFRASTRUCTURE DATA
# ============================================================

def load_infrastructure_data(
    latitude: float,
    longitude: float,
    radius_km: float = 10
):
    """
    Load the processed infrastructure GeoJSON.

    IMPORTANT:
    This function does NOT call Overpass.

    infrastructure.py is responsible for
    downloading and caching infrastructure.
    """

    cache_file = (
        get_infrastructure_cache_path(
            latitude,
            longitude,
            radius_km
        )
    )

    if not cache_file.exists():

        raise FileNotFoundError(
            f"Infrastructure cache not found: "
            f"{cache_file}"
        )

    try:

        with open(
            cache_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception as error:

        raise RuntimeError(
            f"Failed to load infrastructure "
            f"cache: {error}"
        )


# ============================================================
# FEATURE POINT
# ============================================================

def get_feature_reference_point(
    feature
):
    """
    Extract a usable latitude/longitude from
    a GeoJSON feature.

    Supports Point and LineString geometries.
    """

    geometry = feature.get(
        "geometry"
    )

    if not geometry:
        return None

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates"
    )

    if not coordinates:
        return None

    # --------------------------------------------------------
    # POINT
    # --------------------------------------------------------

    if geometry_type == "Point":

        lon, lat = coordinates[:2]

        return {
            "latitude": float(lat),
            "longitude": float(lon)
        }

    # --------------------------------------------------------
    # LINESTRING
    # --------------------------------------------------------

    if geometry_type == "LineString":

        if len(coordinates) == 0:
            return None

        # Use first coordinate as reference
        lon, lat = coordinates[0][:2]

        return {
            "latitude": float(lat),
            "longitude": float(lon)
        }

    # --------------------------------------------------------
    # POLYGON
    # --------------------------------------------------------

    if geometry_type == "Polygon":

        try:

            lon, lat = coordinates[0][0][:2]

            return {
                "latitude": float(lat),
                "longitude": float(lon)
            }

        except Exception:
            return None

    return None


# ============================================================
# CLASSIFY FEATURE
# ============================================================

def classify_feature(feature):
    """
    Read the classification already produced by
    infrastructure.py.
    """

    properties = feature.get("properties") or {}

    return {
        "infrastructure_type": (
            properties.get("asset_type")
            or properties.get("infrastructure_type")
            or properties.get("type")
            or properties.get("category")
            or "unknown"
        ),

        "infrastructure_class": (
            properties.get("infrastructure_class")
            or properties.get("road_class")
            or properties.get("class")
            or "unknown"
        ),

        "name": (
            properties.get("name")
            or properties.get("ref")
            or "Unnamed"
        )
    }


# ============================================================
# INFRASTRUCTURE EXPOSURE
# ============================================================

def calculate_infrastructure_exposure(
    latitude: float,
    longitude: float,
    radius_km: float = 10
):
    """
    Calculate infrastructure exposure around
    the selected location.

    Data source:
        processed infrastructure GeoJSON

    Categories:
        roads
        bridges
        schools
        healthcare
        critical_buildings

    Returns frontend/map-ready data.
    """

    data = load_infrastructure_data(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )

    # Infrastructure classifier stores GeoJSON
    # inside the "map" object.
    map_data = data.get("map", {})

    features = map_data.get("features", [])

    print(
        f"Loaded {len(features)} infrastructure features"
    )

    if not features:
        print(
            "WARNING: Infrastructure cache contains "
            "no GeoJSON features."
        )

        print(
            "Available cache keys:",
            list(data.keys())
        )

        print(
            "Map keys:",
            list(map_data.keys())
        )

    # ========================================================
    # CATEGORY STORAGE
    # ========================================================

    roads = []
    bridges = []
    schools = []
    healthcare = []
    critical_buildings = []

    all_assets = []

    # ========================================================
    # PROCESS FEATURES
    # ========================================================

    for feature in features:

        reference_point = (
            get_feature_reference_point(
                feature
            )
        )

        if not reference_point:
            continue

        feature_lat = (
            reference_point["latitude"]
        )

        feature_lon = (
            reference_point["longitude"]
        )

        distance = calculate_distance_km(
            latitude,
            longitude,
            feature_lat,
            feature_lon
        )
        if distance > radius_km:
            continue

        classification = (
            classify_feature(
                feature
            )
        )

        properties = (
            feature.get(
                "properties"
            )
            or {}
        )

        asset = {
            "id": feature.get(
                "id"
            ),

            "name": classification[
                "name"
            ],

            "type": classification[
                "infrastructure_type"
            ],

            "class": classification[
                "infrastructure_class"
            ],

            "latitude": round(
                feature_lat,
                6
            ),

            "longitude": round(
                feature_lon,
                6
            ),

            "distance_km": round(
                distance,
                3
            ),

            "geometry": feature.get(
                "geometry"
            ),

            "properties": properties
        }

        all_assets.append(
            asset
        )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        asset_type = (
            classification[
                "infrastructure_type"
            ]
            .lower()
        )

        asset_class = (
            classification[
                "infrastructure_class"
            ]
            .lower()
        )

        combined = (
            f"{asset_type} "
            f"{asset_class}"
        )

        if "road" in combined:

            roads.append(
                asset
            )

        elif "bridge" in combined:

            bridges.append(
                asset
            )

        elif "school" in combined:

            schools.append(
                asset
            )

        elif (
            "health" in combined
            or
            "hospital" in combined
            or
            "clinic" in combined
            or
            "doctor" in combined
        ):

            healthcare.append(
                asset
            )

        elif (
            "critical" in combined
            or
            "government" in combined
            or
            "police" in combined
            or
            "fire" in combined
            or
            "emergency" in combined
        ):

            critical_buildings.append(
                asset
            )

    # ========================================================
    # SORT BY DISTANCE
    # ========================================================

    roads.sort(
        key=lambda x: x["distance_km"]
    )

    bridges.sort(
        key=lambda x: x["distance_km"]
    )

    schools.sort(
        key=lambda x: x["distance_km"]
    )

    healthcare.sort(
        key=lambda x: x["distance_km"]
    )

    critical_buildings.sort(
        key=lambda x: x["distance_km"]
    )

    all_assets.sort(
        key=lambda x: x["distance_km"]
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {
        "roads": len(roads),
        "bridges": len(bridges),
        "schools": len(schools),
        "healthcare": len(
            healthcare
        ),
        "critical_buildings": len(
            critical_buildings
        ),
        "total_assets": len(
            all_assets
        )
    }

    # ========================================================
    # DENSITY / EXPOSURE SCORE
    # ========================================================

    area_km2 = (
        math.pi
        * radius_km
        * radius_km
    )

    asset_density = (
        len(all_assets)
        / area_km2
        if area_km2 > 0
        else 0
    )

    # Simple normalized exposure score
    # capped at 1.0
    exposure_score = min(
        1.0,
        asset_density / 100.0
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "success": True,

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "radius_km": radius_km,

        "summary": summary,

        "exposure": {
            "asset_count": len(
                all_assets
            ),

            "asset_density_per_km2": round(
                asset_density,
                3
            ),

            "infrastructure_exposure_score": round(
                exposure_score,
                4
            )
        },

        "categories": {
            "roads": roads,
            "bridges": bridges,
            "schools": schools,
            "healthcare": healthcare,
            "critical_buildings": critical_buildings
        },

        # Flat list is useful for map rendering
        "assets": all_assets
    }


# ============================================================
# FRONTEND / MAP OUTPUT
# ============================================================

def get_map_ready_infrastructure(
    latitude: float,
    longitude: float,
    radius_km: float = 10
):
    """
    Return only the information needed by
    a frontend map.
    """

    result = calculate_infrastructure_exposure(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )

    map_features = []

    for asset in result["assets"]:

        map_features.append({
            "id": asset["id"],
            "type": asset["type"],
            "class": asset["class"],
            "name": asset["name"],

            "latitude": asset[
                "latitude"
            ],

            "longitude": asset[
                "longitude"
            ],

            "distance_km": asset[
                "distance_km"
            ],

            "geometry": asset[
                "geometry"
            ]
        })

    return {
        "success": True,

        "center": {
            "latitude": latitude,
            "longitude": longitude
        },

        "radius_km": radius_km,

        "summary": result[
            "summary"
        ],

        "exposure": result[
            "exposure"
        ],

        "features": map_features
    }


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    result = calculate_infrastructure_exposure(
        latitude=19.8135,
        longitude=85.8312,
        radius_km=10
    )

    print("\n" + "=" * 60)
    print("INFRASTRUCTURE EXPOSURE RESULT")
    print("=" * 60)

    print("\nSUMMARY:")
    print(json.dumps(result.get("summary", {}), indent=2))

    print("\nEXPOSURE:")
    print(json.dumps(result.get("exposure", {}), indent=2))

    print("\nCATEGORIES:")
    print(json.dumps(result.get("categories", {}), indent=2))

    print("\nTOTAL MAP FEATURES:")
    print(len(result.get("assets", [])))

    print("=" * 60)