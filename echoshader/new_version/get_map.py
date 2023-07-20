from typing import List, Union

import geoviews
import numpy
import pandas
import pyvista
import xarray
from pyproj import Transformer

opt_lines = geoviews.opts(
    width=600, height=400, color="red", tools=["hover"], line_width=1
)

opt_point = geoviews.opts(width=600, height=400, color="blue", tools=["hover"], size=10)

opt_tile = geoviews.opts(tools=["box_select"])

EPSG_mercator = "EPSG:3857"

EPSG_coordsys = "EPSG:4326"


<<<<<<< HEAD
def get_track_corners(MVBS_ds):
    left = numpy.nanmin(MVBS_ds.longitude.values)
    bottom = numpy.nanmin(MVBS_ds.latitude.values)
    right = numpy.nanmax(MVBS_ds.longitude.values)
    top = numpy.nanmax(MVBS_ds.latitude.values)

    return left, bottom, right, top


=======
>>>>>>> origin/dev
def convert_EPSG(
    lat: Union[int, float], lon: Union[int, float], mercator_to_coord: bool = True
):
    """
    Converts coordinates between EPSG coordinate reference systems (CRS).

    Args:
        lat (int, float): Latitude value.
        lon (int, float): Longitude value.
        mercator_to_coord (bool, optional):
            If True, converts from EPSG Mercator to coordinate system.
            If False, converts from coordinate system to EPSG Mercator. Default is True.

    Returns:
        tuple: A tuple containing the converted latitude and longitude values.

    Example usage:
        # Convert from EPSG Mercator to coordinate system
        lat, lon = convert_EPSG(0, 0)

        # Convert from coordinate system to EPSG Mercator
        lat, lon = convert_EPSG(40, -75, False)
    """
    if mercator_to_coord is True:
        transformer = Transformer.from_crs(EPSG_mercator, EPSG_coordsys)
        (lat, lon) = transformer.transform(xx=lon, yy=lat)
    else:
        transformer = Transformer.from_crs(EPSG_coordsys, EPSG_mercator)
        (lon, lat) = transformer.transform(xx=lat, yy=lon)

    return lat, lon


def get_tile_options():
    """
    Get a list of available tile options for map visualization.

    Returns:
        list: A list of available tile options.

    Example usage:
        tile_options = get_tile_options()
        print(tile_options)
    """
    return [
        "CartoDark",
        "CartoEco",
        "CartoLight",
        "CartoMidnight",
        "ESRI",
        "EsriImagery",
        "EsriNatGeo",
        "EsriOceanBase",
        "EsriOceanReference",
        "EsriReference",
        "EsriTerrain",
        "EsriUSATopo",
        "OSM",
        "OpenTopoMap",
        "StamenLabels",
        "StamenTerrain",
        "StamenTerrainRetina",
        "StamenToner",
        "StamenTonerBackground",
        "StamenWatercolor",
    ]


def plot_tiles(map_tiles: str = "OSM"):
    """
    Plot map tiles using GeoViews.

    Parameters:
        map_tiles (str, optional): The type of map tiles to plot.
            Defaults to "OSM".
            See more in : https://holoviews.org/reference/elements/bokeh/Tiles.html

    Returns:
        geoviews.element: Map tiles object from GeoViews representing the specified map tiles.
    """
    tiles = getattr(geoviews.tile_sources, map_tiles).opts(opt_tile)

    return tiles


def plot_positions(
    MVBS_ds: xarray.Dataset,
    opts_line: geoviews.opts = opt_lines,
    opts_point: geoviews.opts = opt_point,
):
    """
    Plot track and starting point using GeoViews.

    Parameters:
        MVBS_ds (xarray.Dataset):
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
            MVBS Dataset with values 'latitude', 'longitude'.

        opts_line (geoviews.opts, optional): Options for styling the track line.

        opts_point (geoviews.opts, optional): Options for styling the starting point.

    Returns:
        holoviews.Overlay: Combined chart consisting of lines and starting point.
    """

    # convert xarray data to geoviews data
    all_pd_data = pandas.concat(
        [
            pandas.DataFrame(MVBS_ds.longitude.values, columns=["Longitude"]),
            pandas.DataFrame(MVBS_ds.latitude.values, columns=["Latitude"]),
            pandas.DataFrame(MVBS_ds.ping_time.values, columns=["Ping Time"]),
        ],
        axis=1,
    )

    all_pd_data = all_pd_data.dropna(axis=0, how="any")

    # plot start node
    starting_data = all_pd_data.iloc[0].values.tolist()

    starting_node = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(opts_point)

    # check if all rows has the same latitude and Longitude
    if all_pd_data["Longitude"].nunique() == 1 & all_pd_data["Latitude"].nunique() == 1:
        return starting_node

    # plot path
    line = geoviews.Path(
        [all_pd_data],
        kdims=["Longitude", "Latitude"],
        vdims=["Ping Time", "Longitude", "Latitude"],
    ).opts(opts_line)

    return line * starting_node


def plot_curtain(
    MVBS_ds: xarray.Dataset,
    cmap: Union[str, List[str]] = "jet",
    clim: tuple = None,
    ratio: float = 0.001,
):
    """Drape a 2.5D Sv curtain using Pyvista

    Parameters:
        MVBS_ds (xarray.Dataset):
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
            MVBS Dataset with values 'latitude', 'longitude'.
            MVBS Dataset with a specific frequency.

        cmap (str, List[str], optional): The colormap(s) to be used for color mapping.

        clim (tuple, default: None): Lower and upper bound of the color scale.

        ratio (float, default: 0.001): Z spacing.
            When the value is larger, the height of the map stretches more.

    Returns:
        curtain (pyvista.Plotter):
            Create a pyVista structure made up of 'grid' and 'curtain'.
            Use plotter.show() to display the curtain in a Jupyter cell.
            Use panel.Row(plotter) to display the curtain in panel.
            See more in:
            https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.html?highlight=plotter#pyvista.Plotter
    """

    data = MVBS_ds.Sv.values[1:].T

    lon = MVBS_ds.longitude.values[1:]
    lat = MVBS_ds.latitude.values[1:]
    path = numpy.array([lon, lat, numpy.full(len(lon), 0)]).T

    assert len(path) in data.shape, "Make sure coordinates are present for every trace."

    # Grab the number of samples (in Z dir) and number of traces/soundings
    nsamples, ntraces = data.shape

    # Define the Z spacing of your 2D section
    z_spacing = ratio

    # Create structured points draping down from the path
    points = numpy.repeat(path, nsamples, axis=0)
    # repeat the Z locations across
    tp = numpy.arange(0, z_spacing * nsamples, z_spacing)
    tp = path[:, 2][:, None] - tp
    points[:, -1] = tp.ravel()

    grid = pyvista.StructuredGrid()
    grid.points = points
    grid.dimensions = nsamples, ntraces, 1

    # Add the data array - note the ordering!
    grid["values"] = data.ravel(order="F")

    pyvista.global_theme.jupyter_backend = "panel"
    pyvista.global_theme.background = "gray"

    curtain = pyvista.Plotter()
    curtain.add_mesh(grid, cmap=cmap, clim=clim)
    curtain.add_mesh(pyvista.PolyData(path), color="white")

    curtain.show_grid()
    curtain.show_axes()

    curtain.view_xy()

    return curtain
