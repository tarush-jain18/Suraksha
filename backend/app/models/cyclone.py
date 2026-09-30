from pydantic import BaseModel
from typing import List


class CyclonePoint(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    wind_kmph: float
    pressure_hpa: float


class Cyclone(BaseModel):
    id: str
    name: str
    category: str
    max_wind_kmph: float
    min_pressure_hpa: float
    track: List[CyclonePoint]