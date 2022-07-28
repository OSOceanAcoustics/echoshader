"""echo_curtains.py module

to get 3D curtains
"""

import pyvista
import numpy
import panel

panel.extension('vtk')


def plot_curtain(MVBS_ds, cmp='jet', ratio=0.001):
    '''Get an echogram and histgram with control widgets

    Parameters
    ----------
    MVBS : xr.Dataset
        MVBS_ds data set or ds_Sv data array with a specific frequncy
        like MVBS_ds.sel(channel='GPT  18 kHz 009072058c8d 1-1 ES18-11')

    Returns
    -------
    type: None
        
    describe:
        ctreate a pyVista structure 'grid' and 'curtain' 
        call show() to display the 3D curtain
    
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
    curtain.add_mesh(grid, cmap=cmp)
    curtain.add_mesh(pyvista.PolyData(path), color='white')
    curtain.show_grid()
    curtain.show_axes()
    curtain.view_xy()
    curtain.show()