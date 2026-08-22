import geoviews
import numpy
import pandas
import xarray
from pyproj import Transformer

from echoshader.utils import EPSG_coordsys, EPSG_mercator


def track(
    MVBS_ds: xarray.Dataset,
    tile: str | None = "OSM",
):
    """
    Create a ship-track or moored-location visualization.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        Dataset containing longitude, latitude, and ping_time.
    tile : str or None, optional
        GeoViews background tile. If None, no tile is added.

    Returns
    -------
    holoviews/geoviews object
        Track visualization.
    """
    data = _to_dataframe(MVBS_ds)

    if data.empty:
        raise ValueError(
            "No valid longitude/latitude positions are available."
        )

    if (
        data["Longitude"].nunique() == 1
        and data["Latitude"].nunique() == 1
    ):
        plot = _point(data)
    else:
        plot = _path(data)

    if tile is None:
        return plot

    return _tile(tile) * plot


def _to_dataframe(
    MVBS_ds: xarray.Dataset,
):
    """Convert track coordinates to a DataFrame."""
    return (
        pandas.DataFrame(
            {
                "Longitude": MVBS_ds.longitude.values,
                "Latitude": MVBS_ds.latitude.values,
                "Ping Time": MVBS_ds.ping_time.values,
            }
        )
        .dropna()
    )


def _path(data: pandas.DataFrame):
    """Create a ship path and starting point."""
    starting_data = data.iloc[0]

    starting_point = geoviews.Points(
        [
            (
                starting_data["Longitude"],
                starting_data["Latitude"],
                starting_data["Ping Time"],
            )
        ],
        kdims=[
            "Longitude",
            "Latitude",
        ],
        vdims=[
            "Ping Time",
        ],
    )

    ship_path = geoviews.Path(
        [data],
        kdims=[
            "Longitude",
            "Latitude",
        ],
        vdims=[
            "Ping Time",
        ],
    )

    return ship_path * starting_point


def _point(data: pandas.DataFrame):
    """Create a point for a stationary/moored instrument."""
    starting_data = data.iloc[0]

    return geoviews.Points(
        [
            (
                starting_data["Longitude"],
                starting_data["Latitude"],
                starting_data["Ping Time"],
            )
        ],
        kdims=[
            "Longitude",
            "Latitude",
        ],
        vdims=[
            "Ping Time",
        ],
    )


def _tile(
    map_tiles: str,
):
    """Return a GeoViews tile source."""
    try:
        return getattr(
            geoviews.tile_sources,
            map_tiles,
        )
    except AttributeError as exc:
        raise ValueError(
            f"Unknown map tile source: {map_tiles!r}."
        ) from exc


def get_track_corners(
    MVBS_ds: xarray.Dataset,
):
    """Return left, bottom, right, and top geographic bounds."""
    return (
        numpy.nanmin(MVBS_ds.longitude.values),
        numpy.nanmin(MVBS_ds.latitude.values),
        numpy.nanmax(MVBS_ds.longitude.values),
        numpy.nanmax(MVBS_ds.latitude.values),
    )


def convert_epsg(
    lat: float,
    lon: float,
    mercator_to_coord: bool = True,
):
    """Convert between geographic and Web Mercator coordinates."""
    if mercator_to_coord:
        transformer = Transformer.from_crs(
            EPSG_mercator,
            EPSG_coordsys,
        )
        lat, lon = transformer.transform(
            xx=lon,
            yy=lat,
        )

    else:
        transformer = Transformer.from_crs(
            EPSG_coordsys,
            EPSG_mercator,
        )
        lon, lat = transformer.transform(
            xx=lat,
            yy=lon,
        )

    return lat, lon