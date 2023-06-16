import geoviews
import pandas
import numpy

opt_lines=geoviews.opts(width=600, 
                        height=400, 
                        color="red", 
                        tools=["hover", "box_select"], 
                        line_width=1)

opt_start_point=geoviews.opts(color="red", 
                              size=8)

opt_point=geoviews.opts(color="blue", 
                        tools=["hover"], 
                        size=12)

def plot_tiles(map_tiles="OSM"):
    """
    Plot map tiles using GeoViews.

    Parameters:
        map_tiles (str, optional): The type of map tiles to plot.
            Defaults to "OSM". 
            See more in : https://holoviews.org/reference/elements/bokeh/Tiles.html

    Returns:
        geoviews.element: Map tiles object from GeoViews representing the specified map tiles.
    """
    tiles = getattr(geoviews.tile_sources, map_tiles)

    return tiles

def plot_track(
    MVBS_ds,
    opts_line=opt_lines,
    opts_point=opt_start_point,
):
    """
    Plot a track using GeoViews.

    Parameters
    ----------
    MVBS_ds (xarray.Dataset): 
        MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
        MVBS Dataset with values 'latitue', 'longtitue'.

    opts_line (geoviews.opts, optional): Options for styling the track line.

    opts_line (geoviews.opts, optional): Options for styling the starting point.

    Returns
    -------
    holoviews.Overlay: Combined chart consisting of the ship track lines and starting point.
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

    # plot path
    line = geoviews.Path(
        [all_pd_data],
        kdims=["Longitude", "Latitude"],
        vdims=["Ping Time", "Longitude", "Latitude"],
    ).opts(opts_line)

    # plot start node
    start_data = all_pd_data.iloc[0].values.tolist()

    start_node = geoviews.Points(
        [start_data],
        kdims=["Longitude", "Latitude"],
    ).opts(opts_point)

    return line * start_node


def plot_point(
    MVBS_ds,
    opts_point=opt_point,
):
    """

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'
        MVBS Dataset has been combined with longitude & latitude coordinates using echopype

    opts_line : geoviews.opts

    opts_point : geoviews.opts

    map_tiles : str, default : 'OSM'
        See more in : https://holoviews.org/reference/elements/bokeh/Tiles.html

    Returns
    -------
    holoviews.Overlay
        Combined chart(track, start point and map tile)

    """

    # get the first non-null node
    index = get_first_non_null_index(MVBS_ds.longitude.values)

    point = geoviews.Points(
        [
            [MVBS_ds.longitude.values[index], 
             MVBS_ds.latitude.values[index], 
             MVBS_ds.ping_time.values[index]]
        ],
        kdims=["Longitude", "Latitude"],
    ).opts(opts_point)

    return point


def get_first_non_null_index(data):
    """
    Get the first index of non-null data from a one-dimensional NumPy ndarray.

    Parameters:
        data (numpy.ndarray): The input one-dimensional ndarray.

    Returns:
        int or None: The index of the first non-null value from the ndarray, or None if no non-null value is found.
    """
    mask = numpy.isnan(data)  # Create boolean mask for null values
    if numpy.all(mask):  # Check if all values are null
        return None
    return numpy.argmax(~mask)  # Find index of first non-null value using argmax
