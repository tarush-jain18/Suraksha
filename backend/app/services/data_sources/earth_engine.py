import ee
from datetime import datetime, timedelta


PROJECT_ID = "krishi-kalyan-cb17c"


def initialize_earth_engine():
    ee.Initialize(project=PROJECT_ID)

def check_chirps():
    initialize_earth_engine()

    collection = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate("2026-01-01", "2026-09-27")
        .select("precipitation")
    )

    count = collection.size().getInfo()

    first_image = collection.first()

    if count > 0:
        first_date = ee.Date(
            first_image.get("system:time_start")
        ).format("YYYY-MM-dd").getInfo()
    else:
        first_date = None

    return {
        "image_count": count,
        "first_date": first_date
    }

def check_chirps_latest():
    initialize_earth_engine()

    collection = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(
            ee.Geometry.Point([82.3, 16.3])
        )
        .select("precipitation")
        .sort("system:time_start", False)
    )

    count = collection.size().getInfo()

    if count == 0:
        return {
            "image_count": 0,
            "latest_date": None
        }

    latest = collection.first()

    latest_date = ee.Date(
        latest.get("system:time_start")
    ).format("YYYY-MM-dd").getInfo()

    return {
        "image_count": count,
        "latest_date": latest_date
    }
def get_rainfall(
    latitude: float,
    longitude: float,
    days: int = 30
):
    initialize_earth_engine()

    point = ee.Geometry.Point([
        longitude,
        latitude
    ])

    # Get latest available CHIRPS image date
    collection = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(point)
        .select("precipitation")
        .sort("system:time_start", False)
    )

    image_count = collection.size().getInfo()

    if image_count == 0:
        return 0.0

    latest_image = collection.first()

    latest_date = ee.Date(
        latest_image.get("system:time_start")
    )

    # Calculate start date from latest available observation
    start_date = latest_date.advance(-days, "day")

    rainfall_collection = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(point)
        .filterDate(
            start_date,
            latest_date.advance(1, "day")
        )
        .select("precipitation")
    )

    rainfall_image = rainfall_collection.sum()

    rainfall = rainfall_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=5566,
        bestEffort=True
    ).get("precipitation")

    rainfall_value = rainfall.getInfo()

    if rainfall_value is None:
        return 0.0

    return round(float(rainfall_value), 2)