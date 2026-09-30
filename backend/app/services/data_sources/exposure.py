import ee


PROJECT_ID = "krishi-kalyan-cb17c"


def initialize_earth_engine():
    ee.Initialize(project=PROJECT_ID)


def get_agriculture_data(
    latitude: float,
    longitude: float
):
    initialize_earth_engine()

    point = ee.Geometry.Point([
        longitude,
        latitude
    ])

    radius = 5000

    area = point.buffer(radius)

    landcover = ee.ImageCollection(
        "ESA/WorldCover/v200"
    ).first()

    agriculture = landcover.eq(40)

    agriculture_area = agriculture.multiply(
        ee.Image.pixelArea()
    ).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=area,
        scale=10,
        maxPixels=1e9
    ).get("Map")

    total_area = ee.Image.pixelArea().reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=area,
        scale=10,
        maxPixels=1e9
    ).get("area")

    agriculture_area_value = agriculture_area.getInfo()
    total_area_value = total_area.getInfo()

    if not agriculture_area_value or not total_area_value:
        agriculture_percentage = 0.0
    else:
        agriculture_percentage = (
            agriculture_area_value /
            total_area_value
        ) * 100

    return {
        "agriculture_percentage": round(
            float(agriculture_percentage),
            2
        )
    }

def get_infrastructure_data(
    latitude: float,
    longitude: float
):
    initialize_earth_engine()

    point = ee.Geometry.Point([
        longitude,
        latitude
    ])

    radius = 5000
    area = point.buffer(radius)

    landcover = ee.ImageCollection(
        "ESA/WorldCover/v200"
    ).first()

    built_up = landcover.eq(50)

    built_up_area = built_up.multiply(
        ee.Image.pixelArea()
    ).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=area,
        scale=10,
        maxPixels=1e9
    ).get("Map")

    total_area = ee.Image.pixelArea().reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=area,
        scale=10,
        maxPixels=1e9
    ).get("area")

    built_up_value = built_up_area.getInfo()
    total_area_value = total_area.getInfo()

    if not built_up_value or not total_area_value:
        infrastructure_density = 0.0
    else:
        infrastructure_density = (
            built_up_value /
            total_area_value
        ) * 100

    return {
        "infrastructure_density": round(
            float(infrastructure_density),
            2
        )
    }


def get_exposure_data(
    latitude: float,
    longitude: float
):
    agriculture = get_agriculture_data(
        latitude,
        longitude
    )

    infrastructure = get_infrastructure_data(
        latitude,
        longitude
    )

    return {
        **agriculture,
        **infrastructure,

        # Temporary value
        "healthcare_access": 70.0
    }