import requests


def get_elevation(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/elevation"

    params = {
        "latitude": latitude,
        "longitude": longitude
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    elevation = data["elevation"][0]

    return {
        "elevation_m": float(elevation)
    }