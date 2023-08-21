from pathlib import Path

import panel
import xarray

import echoshader

DATA_DIR = Path("./echoshader/test_data/concatenated_MVBS.nc")

def test_panel():
    # Set the invert_yaxis option to False
    echoshader.utils.gram_opts["Image"]["invert_yaxis"] = False
    
    # Load sample data for testing
    MVBS_ds = xarray.open_mfdataset(
        paths=DATA_DIR,
        data_vars="minimal",
        coords="minimal",
        combine="by_coords",
    )
    
    # Create the echogram panel
    echogram_panel = panel.Row(
        panel.Column(MVBS_ds.eshader.Sv_range_slider, MVBS_ds.eshader.colormap),
        MVBS_ds.eshader.echogram(),
    )
    
    # Check if the panel is created without raising an exception
    assert isinstance(echogram_panel, panel.Row)
