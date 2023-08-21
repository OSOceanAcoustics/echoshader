import panel
import xarray

import echoshader

# When the bug is fixed, set this to True
echoshader.utils.gram_opts["Image"]["invert_yaxis"] = False  

MVBS_ds = xarray.open_mfdataset(
    paths="./echoshader/test/concatenated_MVBS.nc",
    data_vars="minimal",
    coords="minimal",
    combine="by_coords",
)

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

tricolor_echogram_panel.show()
