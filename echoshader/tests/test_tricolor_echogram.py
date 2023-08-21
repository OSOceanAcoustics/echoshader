from pathlib import Path

import panel
import xarray

import echoshader

DATA_DIR = Path("./echoshader/test_data/concatenated_MVBS.nc")


def test_panel():
    # When the bug is fixed, set this to True
    echoshader.utils.gram_opts["Image"]["invert_yaxis"] = False

    MVBS_ds = xarray.open_mfdataset(
        paths=DATA_DIR,
        data_vars="minimal",
        coords="minimal",
        combine="by_coords",
    )

    # Create the tricolor echogram panel
    tricolor_echogram_panel = panel.Row(
        panel.Column(MVBS_ds.eshader.Sv_range_slider),
        MVBS_ds.eshader.echogram(
            channel=[
                "GPT  18 kHz 009072058c8d 1-1 ES18-11",
                "GPT  38 kHz 009072058146 2-1 ES38B",
                "GPT 120 kHz 00907205a6d0 4-1 ES120-7C",
            ],
            rgb_composite=True,
        ),
    )

    # Check if the panel is created without raising an exception
    assert isinstance(tricolor_echogram_panel, panel.Row)
