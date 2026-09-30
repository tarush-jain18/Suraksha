import json
import math
import requests
from pathlib import Path
from app.services.data_sources.healthcare import get_healthcare_data


OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = "Cyclone-Impact-Forecaster/1.0"

# ============================================================
# PROCESSED INFRASTRUCTURE CACHE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PROCESSED_DIR = (
    BASE_DIR / "data" / "processed"
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def get_infrastructure_cache_path(
    latitude: float,
    longitude: float,
    radius_km: float
):
    """
    Returns the JSON file path for a specific
    location and radius.
    """

    lat = f"{latitude:.4f}"
    lon = f"{longitude:.4f}"
    radius = f"{radius_km:g}"

    return (
        PROCESSED_DIR
        / f"infrastructure_{lat}_{lon}_{radius}km.json"
    )


def load_infrastructure_cache(
    latitude: float,
    longitude: float,
    radius_km: float
):
    """
    Load already processed infrastructure data.

    If the JSON exists, no Overpass or healthcare
    request will be made.
    """

    cache_file = get_infrastructure_cache_path(
        latitude,
        longitude,
        radius_km
    )

    if not cache_file.exists():

        return None

    try:

        with open(
            cache_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        print()
        print("========================================")
        print("INFRASTRUCTURE CACHE FOUND")
        print("========================================")
        print(
            f"Loaded from: {cache_file}"
        )

        return data

    except Exception as error:

        print(
            f"Failed to read infrastructure cache: {error}"
        )

        return None


def save_infrastructure_cache(
    data,
    latitude: float,
    longitude: float,
    radius_km: float
):
    """
    Save the complete processed infrastructure
    GeoJSON result into data/processed/.
    """

    cache_file = get_infrastructure_cache_path(
        latitude,
        longitude,
        radius_km
    )

    try:

        with open(
            cache_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

        print()
        print("========================================")
        print("INFRASTRUCTURE CACHE SAVED")
        print("========================================")
        print(
            f"Saved to: {cache_file}"
        )

        return cache_file

    except Exception as error:

        print(
            f"Failed to save infrastructure cache: {error}"
        )

        return None
    
# ============================================================
# DISTANCE
# ============================================================

def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# OVERPASS QUERY
# ============================================================

def build_query(latitude, longitude, radius_km, query_type):

    radius_m = int(radius_km * 1000)

    if query_type == "roads":

        return f"""
[out:json][timeout:15];

way(
    around:{radius_m},
    {latitude},
    {longitude}
)["highway"];

out geom;
"""

    if query_type == "bridges":

        return f"""
    [out:json][timeout:15];

    way(
        around:{radius_m},
        {latitude},
        {longitude}
    )["bridge"];

out center;
"""

    if query_type == "schools":

        return f"""
[out:json][timeout:15];

nwr(
    around:{radius_m},
    {latitude},
    {longitude}
)["amenity"="school"];

out geom;
"""

    if query_type == "critical":

        return f"""
    [out:json][timeout:15];

    (
        nwr(
            around:{radius_m},
            {latitude},
            {longitude}
        )["amenity"~"^(fire_station|police|emergency)$"];

        nwr(
            around:{radius_m},
            {latitude},
            {longitude}
        )["building"="government"];

        nwr(
            around:{radius_m},
            {latitude},
            {longitude}
        )["office"="government"];
    );

out center;
"""

    raise ValueError(f"Unknown query type: {query_type}")


# ============================================================
# QUERY OVERPASS
# ============================================================

def query_overpass(
    latitude,
    longitude,
    radius_km,
    query_type
):

    # ========================================================
    # ROADS
    # ========================================================
    #
    # A 10 km road query can be very large. Public Overpass
    # servers frequently return 504/timeouts for that request.
    #
    # So roads are fetched in 4 smaller tiles and then
    # combined + deduplicated. Bridges, schools and critical
    # buildings keep the original query logic.
    # ========================================================

    if query_type == "roads":

        lat_delta = radius_km / 111.0

        cos_lat = math.cos(
            math.radians(latitude)
        )

        if abs(cos_lat) < 0.01:
            cos_lat = 0.01

        lon_delta = radius_km / (111.0 * cos_lat)

        boxes = [
            # South-West
            (
                latitude - lat_delta,
                longitude - lon_delta,
                latitude,
                longitude
            ),

            # South-East
            (
                latitude - lat_delta,
                longitude,
                latitude,
                longitude + lon_delta
            ),

            # North-West
            (
                latitude,
                longitude - lon_delta,
                latitude + lat_delta,
                longitude
            ),

            # North-East
            (
                latitude,
                longitude,
                latitude + lat_delta,
                longitude + lon_delta
            ),
        ]

        all_elements = []
        seen_elements = set()
        errors = []

        for index, (south, west, north, east) in enumerate(
            boxes,
            start=1
        ):

            query = f"""
[out:json][timeout:30];

way(
    {south},
    {west},
    {north},
    {east}
)["highway"];

out geom qt;
"""

            print()
            print(
                f"Querying roads tile {index}/4"
            )

            tile_success = False
            tile_errors = []

            for server in OVERPASS_SERVERS:

                try:

                    print(
                        f"  -> {server}"
                    )

                    response = requests.post(
                        server,
                        data={"data": query},
                        headers={
                            "User-Agent": USER_AGENT,
                            "Content-Type":
                                "application/x-www-form-urlencoded",
                        },
                        timeout=45,
                    )

                    response.raise_for_status()

                    elements = response.json().get(
                        "elements",
                        []
                    )

                    print(
                        f"  -> {len(elements)} roads found"
                    )

                    for element in elements:

                        element_key = (
                            element.get("type"),
                            element.get("id")
                        )

                        if element_key in seen_elements:
                            continue

                        seen_elements.add(
                            element_key
                        )

                        all_elements.append(
                            element
                        )

                    tile_success = True
                    break

                except Exception as error:

                    print(
                        f"  -> Failed: {error}"
                    )

                    tile_errors.append(
                        f"{server}: {error}"
                    )

            if not tile_success:

                errors.extend(tile_errors)

                raise RuntimeError(
                    f"All Overpass servers failed for "
                    f"roads tile {index}: "
                    + " | ".join(tile_errors)
                )

        print()
        print(
            f"Total unique roads fetched: "
            f"{len(all_elements)}"
        )

        return all_elements

    # ========================================================
    # BRIDGES / SCHOOLS / CRITICAL
    # ========================================================

    query = build_query(
        latitude,
        longitude,
        radius_km,
        query_type
    )

    errors = []

    for server in OVERPASS_SERVERS:

        try:

            print(
                f"Querying {query_type} from "
                f"{server}"
            )

            response = requests.post(
                server,
                data={"data": query},
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type":
                        "application/x-www-form-urlencoded",
                },
                timeout=45,
            )

            response.raise_for_status()

            elements = response.json().get(
                "elements",
                []
            )

            print(
                f"  -> {len(elements)} elements found"
            )

            return elements

        except Exception as error:

            print(
                f"  -> Failed: {error}"
            )

            errors.append(
                f"{server}: {error}"
            )

    raise RuntimeError(
        f"All Overpass servers failed for "
        f"{query_type}: "
        + " | ".join(errors)
    )


# ============================================================
# GEOMETRY
# ============================================================

def get_element_geometry(element):

    element_type = element.get("type")

    # --------------------------------------------------------
    # WAY
    # --------------------------------------------------------

    if element_type == "way":

        geometry = element.get(
            "geometry",
            []
        )

        coordinates = []

        for point in geometry:

            lat = point.get("lat")
            lon = point.get("lon")

            if lat is not None and lon is not None:

                coordinates.append([
                    float(lon),
                    float(lat)
                ])

        if len(coordinates) >= 2:

            # Closed geometry = polygon
            if (
                len(coordinates) >= 4
                and coordinates[0]
                == coordinates[-1]
            ):

                return {
                    "type": "Polygon",
                    "coordinates": [
                        coordinates
                    ]
                }

            # Open geometry = line
            return {
                "type": "LineString",
                "coordinates": coordinates
            }

    # --------------------------------------------------------
    # NODE
    # --------------------------------------------------------

    lat = element.get("lat")
    lon = element.get("lon")

    if lat is not None and lon is not None:

        return {
            "type": "Point",
            "coordinates": [
                float(lon),
                float(lat)
            ]
        }

    # --------------------------------------------------------
    # CENTER
    # --------------------------------------------------------

    center = element.get(
        "center",
        {}
    )

    lat = center.get("lat")
    lon = center.get("lon")

    if lat is not None and lon is not None:

        return {
            "type": "Point",
            "coordinates": [
                float(lon),
                float(lat)
            ]
        }

    return None


# ============================================================
# REFERENCE POINT
# ============================================================

def get_element_reference_point(element):

    geometry = element.get(
        "geometry",
        []
    )

    if geometry:

        middle = geometry[
            len(geometry) // 2
        ]

        if (
            middle.get("lat") is not None
            and middle.get("lon") is not None
        ):

            return (
                float(middle["lat"]),
                float(middle["lon"])
            )

    lat = element.get("lat")
    lon = element.get("lon")

    if lat is not None and lon is not None:

        return (
            float(lat),
            float(lon)
        )

    center = element.get(
        "center",
        {}
    )

    if (
        center.get("lat") is not None
        and center.get("lon") is not None
    ):

        return (
            float(center["lat"]),
            float(center["lon"])
        )

    return None


# ============================================================
# ROAD CLASS
# ============================================================

def road_class(tags):

    highway = tags.get(
        "highway"
    )

    primary = {
        "motorway",
        "motorway_link",
        "trunk",
        "trunk_link",
        "primary",
        "primary_link",
    }

    secondary = {
        "secondary",
        "secondary_link",
    }

    tertiary = {
        "tertiary",
        "tertiary_link",
    }

    local = {
        "residential",
        "unclassified",
        "living_street",
        "service",
    }

    if highway in primary:
        return "primary"

    if highway in secondary:
        return "secondary"

    if highway in tertiary:
        return "tertiary"

    if highway in local:
        return "local"

    return "other"


# ============================================================
# BUILD FEATURE
# ============================================================

def build_feature(
    element,
    target_latitude,
    target_longitude,
    asset_type
):

    tags = element.get(
        "tags",
        {}
    )

    geometry = get_element_geometry(
        element
    )

    if geometry is None:
        return None

    reference_point = (
        get_element_reference_point(
            element
        )
    )

    if reference_point is None:
        return None

    latitude, longitude = reference_point

    distance = calculate_distance_km(
        target_latitude,
        target_longitude,
        latitude,
        longitude
    )

    element_id = (
        f"{element.get('type', 'element')}_"
        f"{element.get('id')}"
    )

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    default_name = (
        "Unnamed "
        + asset_type.replace(
            "_",
            " "
        )
    )

    name = (
        tags.get("name")
        or default_name
    )

    # --------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------

    properties = {

        "id": element_id,

        "asset_type": asset_type,

        "name": name,

        "latitude": latitude,

        "longitude": longitude,

        "distance_km": round(
            distance,
            2
        ),
    }

    # --------------------------------------------------------
    # ROAD
    # --------------------------------------------------------

    if asset_type == "road":

        properties[
            "road_class"
        ] = road_class(tags)

        properties[
            "highway_type"
        ] = tags.get(
            "highway"
        )

    # --------------------------------------------------------
    # BRIDGE
    # --------------------------------------------------------

    elif asset_type == "bridge":

        properties[
            "road_class"
        ] = road_class(tags)

        properties[
            "highway_type"
        ] = tags.get(
            "highway"
        )

        properties[
            "bridge_type"
        ] = tags.get(
            "bridge"
        )

    # --------------------------------------------------------
    # SCHOOL
    # --------------------------------------------------------

    elif asset_type == "school":

        properties[
            "school_type"
        ] = tags.get(
            "school:type"
        )

        properties[
            "operator"
        ] = tags.get(
            "operator"
        )

    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    elif asset_type == "critical_building":

        properties[
            "critical_type"
        ] = (
            tags.get("amenity")
            or tags.get("building")
            or tags.get("office")
            or "critical"
        )

    return {

        "type": "Feature",

        "geometry": geometry,

        "properties": properties
    }


# ============================================================
# HEALTHCARE → GEOJSON
# ============================================================

def healthcare_to_feature(
    facility
):

    latitude = float(
        facility["latitude"]
    )

    longitude = float(
        facility["longitude"]
    )

    return {

        "type": "Feature",

        "geometry": {

            "type": "Point",

            "coordinates": [
                longitude,
                latitude
            ]
        },

        "properties": {

            "id":
                "healthcare_"
                + str(latitude)
                + "_"
                + str(longitude),

            "asset_type":
                "healthcare",

            "name":
                facility["name"],

            "latitude":
                latitude,

            "longitude":
                longitude,

            "distance_km":
                facility["distance_km"],

            "healthcare_type":
                facility["type"]
        }
    }


# ============================================================
# MAIN CLASSIFICATION
# ============================================================

def classify_infrastructure(
    latitude: float,
    longitude: float,
    radius_km: float = 10,
    use_cache: bool = True,
    refresh: bool = False
):

    print()
    print("========================================")
    print("INFRASTRUCTURE CLASSIFICATION")
    print("========================================")
    print(
        f"Location: {latitude}, {longitude}"
    )
    print(
        f"Radius: {radius_km} km"
    )

    # ========================================================
    # CHECK PROCESSED JSON FIRST
    # ========================================================

    if use_cache and not refresh:

        cached_data = (
            load_infrastructure_cache(
                latitude,
                longitude,
                radius_km
            )
        )

        if cached_data is not None:

            print(
                "Using processed infrastructure JSON."
            )

            return cached_data

    # ========================================================
    # NO CACHE → FETCH FRESH DATA
    # ========================================================

    print()
    print(
        "No processed infrastructure JSON found."
    )

    print(
        "Fetching fresh infrastructure data..."
    )

    features = []

    seen = set()

    # ========================================================
    # ROADS
    # ========================================================

    roads = query_overpass(
        latitude,
        longitude,
        radius_km,
        "roads"
    )

    for element in roads:

        feature = build_feature(
            element,
            latitude,
            longitude,
            "road"
        )

        if feature is None:
            continue

        asset_id = feature[
            "properties"
        ]["id"]

        if asset_id in seen:
            continue

        seen.add(
            asset_id
        )

        features.append(
            feature
        )

    # ========================================================
    # BRIDGES
    # ========================================================

    bridges = query_overpass(
        latitude,
        longitude,
        radius_km,
        "bridges"
    )

    for element in bridges:

        feature = build_feature(
            element,
            latitude,
            longitude,
            "bridge"
        )

        if feature is None:
            continue

        asset_id = feature[
            "properties"
        ]["id"]

        if asset_id in seen:
            continue

        seen.add(
            asset_id
        )

        features.append(
            feature
        )

    # ========================================================
    # SCHOOLS
    # ========================================================

    schools = query_overpass(
        latitude,
        longitude,
        radius_km,
        "schools"
    )

    for element in schools:

        feature = build_feature(
            element,
            latitude,
            longitude,
            "school"
        )

        if feature is None:
            continue

        asset_id = feature[
            "properties"
        ]["id"]

        if asset_id in seen:
            continue

        seen.add(
            asset_id
        )

        features.append(
            feature
        )

    # ========================================================
    # CRITICAL BUILDINGS
    # ========================================================

    critical = query_overpass(
        latitude,
        longitude,
        radius_km,
        "critical"
    )

    for element in critical:

        feature = build_feature(
            element,
            latitude,
            longitude,
            "critical_building"
        )

        if feature is None:
            continue

        asset_id = feature[
            "properties"
        ]["id"]

        if asset_id in seen:
            continue

        seen.add(
            asset_id
        )

        features.append(
            feature
        )

    # ========================================================
    # HEALTHCARE
    # ========================================================

    print()
    print(
        "Loading healthcare facilities..."
    )

    healthcare = get_healthcare_data(
        latitude,
        longitude,
        radius_km
    )

    healthcare_list = healthcare.get(
        "healthcare_facilities_list",
        []
    )

    print(
        f"  -> {len(healthcare_list)} "
        f"healthcare facilities found"
    )

    for facility in healthcare_list:

        feature = healthcare_to_feature(
            facility
        )

        asset_id = feature[
            "properties"
        ]["id"]

        if asset_id in seen:
            continue

        seen.add(
            asset_id
        )

        features.append(
            feature
        )

    # ========================================================
    # SORT BY DISTANCE
    # ========================================================

    features.sort(
        key=lambda feature:
            feature[
                "properties"
            ]["distance_km"]
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {

        "roads": 0,

        "bridges": 0,

        "schools": 0,

        "healthcare": 0,

        "critical_buildings": 0,

        "total_assets":
            len(features)
    }

    for feature in features:

        asset_type = feature[
            "properties"
        ]["asset_type"]

        if asset_type == "road":

            summary[
                "roads"
            ] += 1

        elif asset_type == "bridge":

            summary[
                "bridges"
            ] += 1

        elif asset_type == "school":

            summary[
                "schools"
            ] += 1

        elif asset_type == "healthcare":

            summary[
                "healthcare"
            ] += 1

        elif asset_type == "critical_building":

            summary[
                "critical_buildings"
            ] += 1

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {

        "success": True,

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude
        },

        "radius_km":
            radius_km,

        "map": {

            "type":
                "FeatureCollection",

            "features":
                features
        },

        "summary":
            summary
    }

    # ========================================================
    # SAVE COMPLETE RESULT
    # ========================================================

    if use_cache:

        save_infrastructure_cache(
            result,
            latitude,
            longitude,
            radius_km
        )

    return result
# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = classify_infrastructure(

        latitude=19.8135,

        longitude=85.8312,

        radius_km=10,

        use_cache=True,

        refresh=False
    )

    print()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )