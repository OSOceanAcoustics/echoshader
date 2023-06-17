import geoviews
import pandas
import numpy
import pyvista
# import panel

# panel.extension("vtk")

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

    Parameters:
        MVBS_ds (xarray.Dataset): 
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
            MVBS Dataset with values 'latitude', 'longitude'.

        opts_line (geoviews.opts, optional): Options for styling the track line.

        opts_point (geoviews.opts, optional): Options for styling the starting point.

    Returns:
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
    Plot a track using GeoViews.

    Parameters:
        MVBS_ds (xarray.Dataset): 
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
            MVBS Dataset with values 'latitude', 'longitude'.

        opts_point (geoviews.opts, optional): Options for styling the starting point.

    Returns:
        geoviews.Points: Stationary point of moored platform.
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

def plot_curtain(MVBS_ds, 
                 colormap="jet", 
                 clim=None, 
                 ratio=0.001):
    """Drape a 2.5D Sv curtain using Pyvista

    Parameters:
        MVBS_ds (xarray.Dataset):
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'.
            MVBS Dataset with values 'latitude', 'longitude'.
            MVBS Dataset with a specific frequency.

        colormap (str, default: 'jet'): Colormap.

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

    Examples:
        MVBS_ds_ = MVBS_ds.sel(channel='GPT  18 kHz 009072058c8d 1-1 ES18-11')

        plotter = plot_curtain(MVBS_ds_, 'jet', (-80, -30), 0.001)

        plotter.show()  # Simply show in Jupyter

        widget_panel = panel.Row(plotter)  # Get panel where the curtain is displayed
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
    curtain.add_mesh(grid, cmap=colormap, clim=clim)
    curtain.add_mesh(pyvista.PolyData(path), color="white")

    curtain.show_grid()
    curtain.show_axes()

    curtain.view_xy()

    return curtain
