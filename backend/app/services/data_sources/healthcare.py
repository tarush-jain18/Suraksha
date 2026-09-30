import json
import math
import requests
from pathlib import Path


OVERPASS_SERVERS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = (
    "Mozilla/5.0 "
    "(Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/154.0.0.0 "
    "Safari/537.36"
)

REFERER = "https://overpass-turbo.eu/"

CACHE_FILE = Path(
    "data/processed/healthcare_puri.json"
)


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


def build_overpass_query(
    latitude,
    longitude,
    radius_km=10
):
    radius_m = int(
        radius_km * 1000
    )

    return f"""
[out:json][timeout:20];

(
  nwr(
    around:{radius_m},
    {latitude},
    {longitude}
  )["amenity"="hospital"];

  nwr(
    around:{radius_m},
    {latitude},
    {longitude}
  )["amenity"="clinic"];

  nwr(
    around:{radius_m},
    {latitude},
    {longitude}
  )["amenity"="doctors"];
);

out center;
"""


def get_element_coordinates(element):

    latitude = element.get("lat")
    longitude = element.get("lon")

    if (
        latitude is not None
        and longitude is not None
    ):
        return (
            float(latitude),
            float(longitude)
        )

    center = element.get(
        "center",
        {}
    )

    latitude = center.get("lat")
    longitude = center.get("lon")

    if (
        latitude is None
        or longitude is None
    ):
        return None

    return (
        float(latitude),
        float(longitude)
    )


def parse_facilities(
    elements,
    target_latitude,
    target_longitude
):

    facilities = []
    seen = set()

    for element in elements:

        tags = element.get(
            "tags",
            {}
        )

        coordinates = (
            get_element_coordinates(
                element
            )
        )

        if coordinates is None:
            continue

        latitude, longitude = coordinates

        name = tags.get(
            "name"
        )

        amenity = tags.get(
            "amenity",
            "healthcare"
        )

        key = (
            name,
            round(latitude, 6),
            round(longitude, 6)
        )

        if key in seen:
            continue

        seen.add(key)

        distance = calculate_distance(
            target_latitude,
            target_longitude,
            latitude,
            longitude
        )

        facilities.append({
            "name": (
                name
                or
                "Unnamed healthcare facility"
            ),
            "type": amenity,
            "latitude": latitude,
            "longitude": longitude,
            "distance_km": round(
                distance,
                2
            )
        })

    facilities.sort(
        key=lambda item:
        item["distance_km"]
    )

    return facilities


def query_overpass(
    latitude,
    longitude,
    radius_km=10
):

    query = build_overpass_query(
        latitude,
        longitude,
        radius_km
    )

    errors = []

    for server in OVERPASS_SERVERS:

        print(
            f"Trying healthcare source: {server}"
        )

        try:

            headers = {
                "User-Agent": USER_AGENT,
                "Referer": REFERER,
                "Accept": "application/json",
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
                "Connection": "close"
            }

            response = requests.post(
                server,
                data={
                    "data": query
                },
                headers=headers,
                timeout=30
            )

            print(
                "Status:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            print(
                "Live healthcare data received."
            )

            return data.get(
                "elements",
                []
            )

        except Exception as error:

            errors.append(
                str(error)
            )

            print(
                "Failed:",
                error
            )

    raise RuntimeError(
        "All live healthcare sources failed"
    )


def save_cache(result):

    CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )


def load_cache():

    if not CACHE_FILE.exists():
        return None

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return None


def get_healthcare_context(
    latitude,
    longitude,
    radius_km=10
):

    try:

        elements = query_overpass(
            latitude,
            longitude,
            radius_km
        )

        facilities = parse_facilities(
            elements,
            latitude,
            longitude
        )

        if not facilities:

            result = {
                "healthcare_access": None,
                "healthcare_facilities": 0,
                "nearest_healthcare_km": None,
                "healthcare_facilities_list": [],
                "healthcare_data_status": "available"
            }

            save_cache(result)

            return result

        nearest_distance = (
            facilities[0]["distance_km"]
        )

        healthcare_access = max(
            0.0,
            min(
                100.0,
                100.0
                - (
                    nearest_distance * 2
                )
            )
        )

        result = {
            "healthcare_access": round(
                healthcare_access,
                1
            ),
            "healthcare_facilities": len(
                facilities
            ),
            "nearest_healthcare_km": (
                nearest_distance
            ),
            "healthcare_facilities_list": (
                facilities[:10]
            ),
            "healthcare_data_status": (
                "available"
            )
        }

        save_cache(result)

        return result

    except Exception as error:

        print(
            "Live healthcare lookup failed."
        )

        cached = load_cache()

        if cached:

            print(
                "Using cached healthcare data."
            )

            cached[
                "healthcare_data_status"
            ] = "cached"

            return cached

        return {
            "healthcare_access": None,
            "healthcare_facilities": None,
            "nearest_healthcare_km": None,
            "healthcare_facilities_list": [],
            "healthcare_data_status": (
                "unavailable"
            ),
            "healthcare_error": str(error)
        }


def get_healthcare_data(
    latitude,
    longitude,
    radius_km=10
):

    return get_healthcare_context(
        latitude,
        longitude,
        radius_km
    )


if __name__ == "__main__":

    print("=" * 60)
    print("HEALTHCARE LIVE DATA TEST")
    print("=" * 60)

    result = get_healthcare_data(
        latitude=19.8135,
        longitude=85.8312,
        radius_km=10
    )

    print()
    print("RESULT:")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )