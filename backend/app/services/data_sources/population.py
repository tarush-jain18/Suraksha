import ee


PROJECT_ID = "krishi-kalyan-cb17c"


def initialize_earth_engine():
    ee.Initialize(project=PROJECT_ID)


def get_population_data(
    latitude: float,
    longitude: float
):
    initialize_earth_engine()

    point = ee.Geometry.Point([
        longitude,
        latitude
    ])

    population = (
        ee.ImageCollection(
            "WorldPop/GP/100m/pop"
        )
        .filterBounds(point)
        .filterDate(
            "2020-01-01",
            "2021-01-01"
        )
        .mosaic()
    )

    result = population.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=100,
        bestEffort=True
    )

    population_value = result.get(
        "population"
    ).getInfo()

    if population_value is None:
        population_value = 0.0

    return {
        "population_density": round(
            float(population_value),
            2
        )
    }