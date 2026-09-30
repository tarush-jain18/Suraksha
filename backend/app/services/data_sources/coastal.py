import geopandas as gpd
from shapely.geometry import Point


COASTLINE_FILE = "data/geospatial/odisha.geojson"


def load_odisha_geometry():
    gdf = gpd.read_file(COASTLINE_FILE)

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")

    return gdf.to_crs("EPSG:4326").geometry.union_all()


def get_coastal_data(
    latitude: float,
    longitude: float
):
    odisha_geometry = load_odisha_geometry()

    point = Point(
        longitude,
        latitude
    )

    # Project both geometries to Web Mercator
    # for approximate distance calculation.
    geometry_projected = gpd.GeoSeries(
        [odisha_geometry],
        crs="EPSG:4326"
    ).to_crs("EPSG:3857").iloc[0]

    point_projected = gpd.GeoSeries(
        [point],
        crs="EPSG:4326"
    ).to_crs("EPSG:3857").iloc[0]

    distance_m = point_projected.distance(
        geometry_projected.boundary
    )

    distance_km = distance_m / 1000

    return {
        "distance_from_coast_km": round(
            float(distance_km),
            2
        )
    }