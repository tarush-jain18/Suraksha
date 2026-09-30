import requests


def get_weather_data(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation",
        "forecast_days": 3,
        "timezone": "auto"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    hourly_precipitation = data.get(
        "hourly", {}
    ).get(
        "precipitation", []
    )

    # Total precipitation forecast over the next 72 hours
    rainfall_mm = sum(
        value for value in hourly_precipitation
        if value is not None
    )

    return {
        "rainfall_mm": round(float(rainfall_mm), 2)
    }