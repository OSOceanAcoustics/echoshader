import xarray
import panel
from .. import core

MVBS_ds = xarray.open_mfdataset(
    paths = './echoshader/test/concatenated_MVBS.nc', 
    data_vars = 'minimal', coords='minimal',
    combine = 'by_coords'
)

echogram_panel = panel.Row(
                panel.Column(MVBS_ds.eshader.Sv_range_slider,
                             MVBS_ds.eshader.colormap),
                MVBS_ds.eshader.echogram(),
            )

echogram_panel.show()
