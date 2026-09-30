import pandas as pd
import math
import geopandas as gpd
from shapely.geometry import Point

IBTRACS_FILE = "data/historical/raw/ibtracs.NI.list.v04r01.csv"
ODISHA_FILE = "data/geospatial/odisha.geojson"


def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2) - math.radians(lon1)

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


def knots_to_kmph(knots):
    if pd.isna(knots):
        return None

    return round(float(knots) * 1.852, 1)


def load_odisha_geometry():
    gdf = gpd.read_file(ODISHA_FILE)

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    gdf = gdf.to_crs("EPSG:4326")

    return gdf.geometry.union_all()


def find_odisha_cyclones():
    df = pd.read_csv(
        IBTRACS_FILE,
        skiprows=[1],
        low_memory=False
    )

    numeric_columns = [
        "LAT",
        "LON",
        "WMO_WIND",
        "WMO_PRES"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df["SEASON"] = pd.to_numeric(
        df["SEASON"],
        errors="coerce"
    )

    df["ISO_TIME"] = df["ISO_TIME"].astype(str)

    df = df.dropna(
        subset=["LAT", "LON", "SEASON"]
    )

    odisha = load_odisha_geometry()

    affected_storms = {}

    for _, row in df.iterrows():

        point = Point(
            row["LON"],
            row["LAT"]
        )

        inside_odisha = odisha.contains(point)

        sid = row["SID"]

        if sid not in affected_storms:
            affected_storms[sid] = {
                "sid": sid,
                "name": str(row["NAME"]),
                "year": int(row["SEASON"]),
                "track": [],
                "track_intersects_odisha": False,
                "minimum_distance_to_odisha_km": None,
                "max_wind_kt": None,
                "max_wind_kmph": None,
                "min_pressure_hpa": None
            }

        storm = affected_storms[sid]

        wind_kt = (
            float(row["WMO_WIND"])
            if not pd.isna(row["WMO_WIND"])
            else None
        )

        pressure = (
            float(row["WMO_PRES"])
            if not pd.isna(row["WMO_PRES"])
            else None
        )

        storm["track"].append({
            "timestamp": row["ISO_TIME"],
            "latitude": round(float(row["LAT"]), 4),
            "longitude": round(float(row["LON"]), 4),
            "wind_kt": wind_kt,
            "wind_kmph": knots_to_kmph(wind_kt),
            "pressure_hpa": pressure
        })

        if inside_odisha:
            storm["track_intersects_odisha"] = True

        if wind_kt is not None:
            if (
                storm["max_wind_kt"] is None
                or wind_kt > storm["max_wind_kt"]
            ):
                storm["max_wind_kt"] = wind_kt
                storm["max_wind_kmph"] = knots_to_kmph(wind_kt)

        if pressure is not None:
            if (
                storm["min_pressure_hpa"] is None
                or pressure < storm["min_pressure_hpa"]
            ):
                storm["min_pressure_hpa"] = pressure

    # Calculate actual minimum distance to Odisha boundary
    projected_odisha = gpd.GeoSeries(
        [odisha],
        crs="EPSG:4326"
    ).to_crs("EPSG:32645").iloc[0]

    for storm in affected_storms.values():

        minimum_distance = None

        for track_point in storm["track"]:

            point = Point(
                track_point["longitude"],
                track_point["latitude"]
            )

            projected_point = gpd.GeoSeries(
                [point],
                crs="EPSG:4326"
            ).to_crs("EPSG:32645").iloc[0]

            distance_m = projected_point.distance(
                projected_odisha.boundary
            )

            distance_km = distance_m / 1000

            if (
                minimum_distance is None
                or distance_km < minimum_distance
            ):
                minimum_distance = distance_km

        storm["minimum_distance_to_odisha_km"] = (
            round(minimum_distance, 2)
            if minimum_distance is not None
            else None
        )

        storm["track_points"] = len(
            storm["track"]
        )

    storms = list(affected_storms.values())

    # Only retain systems that either entered Odisha
    # or came within 100 km of the Odisha boundary.
    storms = [
        storm
        for storm in storms
        if storm["track_intersects_odisha"]
        or (
            storm["minimum_distance_to_odisha_km"] is not None
            and storm["minimum_distance_to_odisha_km"] <= 100
        )
    ]

    storms.sort(
        key=lambda x: x["year"],
        reverse=True
    )

    return storms