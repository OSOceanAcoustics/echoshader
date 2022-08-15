"""echo_curtain.py module

to get 3D curtains
"""
import panel
panel.extension('vtk')

import pyvista
import numpy


def plot_curtain(MVBS_ds, cmp='jet', clim = None ,ratio=0.001):
    '''Drape a 2.5D Sv curatin using Pyvista

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'
        MVBS Dataset with a specific frequncy
        MVBS Dataset has been combined with longitude & latitude coordinates using echopype
    
    cmp : str, default: 'jet'
        Colormap
    
    clim : tuple, default: None
        Lower and upper bound of the color scale

    ratio : float, default: 0.001
        Z spaceing
        When the value is larger, the height of map stretches more

    Returns
    -------
    curtain : pyvista.Plotter
        Create a pyVista structure made up of 'grid' and 'curtain' 
        Use plotter.show() to display the curtain in Jupyter cell
        Use panel.Row(plotter) to display the curtain in panel
        See more in:
        https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.html?highlight=plotter#pyvista.Plotter
        
    Examples
    --------
        MVBS_ds_ = MVBS_ds.sel(channel='GPT  18 kHz 009072058c8d 1-1 ES18-11')
        
        plotter = plot_curtain(MVBS_ds_, 'jet', (-80, -30), 0.001)
        
        plotter.show() // Simply show in jupyter
        
        widget_panel = panel.Row(plotter) // Get panel where the curtain is chiseled in
        
    '''
    
    data = MVBS_ds.Sv.values[1:].T

    lon = MVBS_ds.longitude.values[1:]
    lat = MVBS_ds.latitude.values[1:]
    path = numpy.array([lon, lat, numpy.full(len(lon), 0)]).T

    assert len(
        path
    ) in data.shape, "Make sure coordinates are present for every trace."

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

    pyvista.global_theme.jupyter_backend = 'panel'
    pyvista.global_theme.background = 'gray'

    curtain = pyvista.Plotter()
    curtain.add_mesh(grid, cmap=cmp, clim=clim)
    curtain.add_mesh(pyvista.PolyData(path), color='white')

    curtain.show_grid()
    curtain.show_axes()

    curtain.view_xy()

    return curtain