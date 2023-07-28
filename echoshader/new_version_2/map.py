import geoviews
import pandas
import xarray
from utils import gram_opts


def convert_MVBS_to_pandas(MVBS_ds: xarray.Dataset):
    """
    Convert MVBS (Multibeam Backscatter) data from xarray.Dataset to a pandas DataFrame.

    The DataFrame will have columns for "Longitude", "Latitude", and "Ping Time".

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
        It should include variables 'longitude', 'latitude', and 'ping_time'.

    Returns
    -------
    pandas.DataFrame
        A pandas DataFrame with columns "Longitude", "Latitude", and "Ping Time".
        The DataFrame will exclude rows with any missing (NaN) values.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Convert the MVBS data to a pandas DataFrame
    mvbs_df = convert_MVBS_to_pandas(MVBS_ds)

    # Now you can work with the data as a pandas DataFrame
    print(mvbs_df.head())
    """
    all_pd_data = pandas.concat(
        [
            pandas.DataFrame(MVBS_ds.longitude.values, columns=["Longitude"]),
            pandas.DataFrame(MVBS_ds.latitude.values, columns=["Latitude"]),
            pandas.DataFrame(MVBS_ds.ping_time.values, columns=["Ping Time"]),
        ],
        axis=1,
    )

    all_pd_data = all_pd_data.dropna(axis=0, how="any")

    return all_pd_data


def tile_plot(map_tiles: str):
    """
    Load and customize map tiles from GeoViews tile sources.

    This function loads a specific map tile layer from GeoViews tile sources module
    and applies the specified `gram_opts` (plotting options) to customize the appearance.

    Parameters
    ----------
    map_tiles : str
        The name of the map tile layer to load. It should be one of the supported
        tile source names available in the GeoViews tile_sources module.
        Source: https://holoviews.org/reference/elements/bokeh/Tiles.html

    Returns
    -------
    geoviews.element.Tiles
        A customized map tile layer (tiles) loaded from GeoViews tile sources,
        rendered with the provided `gram_opts`.

    Examples
    --------
    # Load and customize the "OSM" (OpenStreetMap) map tiles
    osm_tiles = tile_plot("OSM")
    """
    tiles = getattr(geoviews.tile_sources, map_tiles).opts(gram_opts)

    return tiles


def track_plot(MVBS_ds: xarray.Dataset, map_tiles: str):
    """
    Plot the ship's track on a map using GeoViews.

    This function takes an xarray.Dataset containing MVBS (Multibeam Backscatter) data,
    converts it into a pandas DataFrame, and plots the ship's track on a map using GeoViews.
    The starting point of the ship's track is plotted as a single point, and the entire path
    of the ship's track is plotted as a line on the map.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
        It should include variables 'longitude', 'latitude', and 'ping_time'.

    Returns
    -------
    geoviews.element.Path * geoviews.element.Points
        The ship's track plotted as a line (ship_path) and the starting point plotted as
        a point (starting_point).
        Both elements are combined and rendered using GeoViews with the provided `gram_opts`.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Plot the ship's track on a map using GeoViews
    track_plot = track_plot(MVBS_ds)

    # Load and customize the "OSM" (OpenStreetMap) map tiles
    osm_tiles = tile_plot("OSM")

    # Display the ship's track using Panel
    panel.Column(track_plot * osm_tiles)
    """
    all_pd_data = convert_MVBS_to_pandas(MVBS_ds)

    starting_data = all_pd_data.iloc[0].values.tolist()

    # plot starting point
    starting_point = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(gram_opts)

    # plot ship path
    ship_path = geoviews.Path(
        [all_pd_data],
        kdims=["Longitude", "Latitude"],
        vdims=["Ping Time", "Longitude", "Latitude"],
    ).opts(gram_opts)

    return ship_path * starting_point * tile_plot(map_tiles)


def point_plot(MVBS_ds: xarray.Dataset):
    """
    Plot a moored point on a map using GeoViews.

    This function takes an xarray.Dataset containing MVBS (Multibeam Backscatter) data,
    converts it into a pandas DataFrame, and plots a moored point on a map using GeoViews.
    The moored point represents the location at the starting data point in the dataset.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
        It should include variables 'longitude', 'latitude', and 'ping_time'.

    Returns
    -------
    geoviews.element.Points
        A moored point plotted on a map using GeoViews with the provided `gram_opts`.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Plot a moored point on a map using GeoViews
    moored_point_plot = point_plot(MVBS_ds)

    # Load and customize the "OSM" (OpenStreetMap) map tiles
    osm_tiles = tile_plot("OSM")

    # Display the moored point using Panel
    Panel.Row(moored_point_plot * osm_tiles)
    """
    all_pd_data = convert_MVBS_to_pandas(MVBS_ds)

    starting_data = all_pd_data.iloc[0].values.tolist()

    # plot moored point
    moored_point = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(gram_opts)

    return moored_point
