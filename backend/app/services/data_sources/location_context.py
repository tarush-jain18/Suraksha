from app.services.data_sources.earth_engine import get_rainfall
from app.services.data_sources.elevation import get_elevation
from app.services.data_sources.coastal import get_coastal_data
from app.services.data_sources.population import get_population_data
from app.services.data_sources.exposure import get_exposure_data
from app.services.data_sources.healthcare import get_healthcare_data


def get_location_context(latitude: float, longitude: float):
    rainfall = get_rainfall(latitude, longitude)
    elevation = get_elevation(latitude, longitude)
    coastal = get_coastal_data(latitude, longitude)
    population = get_population_data(latitude, longitude)
    exposure = get_exposure_data(latitude, longitude)
    healthcare = get_healthcare_data(latitude, longitude)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "rainfall_mm": rainfall,
        **elevation,
        **coastal,
        **population,
        **exposure,
        **healthcare
    }