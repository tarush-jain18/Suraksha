import json
from pathlib import Path

from app.services.normalization import normalize_cyclone


DATA_PATH = Path("data/raw/cyclone_demo.json")


def load_cyclone_data():

    with open(DATA_PATH, "r") as file:
        cyclone = json.load(file)

    return normalize_cyclone(cyclone)


def get_cyclone_by_id(cyclone_id: str):

    cyclone = load_cyclone_data()

    if cyclone["id"] == cyclone_id:
        return cyclone

    return None