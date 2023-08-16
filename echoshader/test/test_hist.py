from .. import core
import panel

MVBS_ds = core.xarray.open_mfdataset(
    paths="./echoshader/test/concatenated_MVBS.nc",
    data_vars="minimal",
    coords="minimal",
    combine="by_coords",
)

MVBS_ds.eshader.control_mode_select.value = False

track_panel = panel.Row(
    panel.Column(MVBS_ds.eshader.tile_select), MVBS_ds.eshader.track()
)

echogram_panel = panel.Row(
    panel.Column(MVBS_ds.eshader.Sv_range_slider, MVBS_ds.eshader.colormap),
    MVBS_ds.eshader.echogram(),
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

stats_panel = panel.Row(
    panel.Column(MVBS_ds.eshader.bin_size_input, MVBS_ds.eshader.overlay_layout_toggle),
    panel.Column(
        MVBS_ds.eshader.hist(),
        MVBS_ds.eshader.table(),
    ),
)

panel.Column(
    MVBS_ds.eshader.control_mode_select,
    track_panel,
    echogram_panel,
    tricolor_echogram_panel,
    stats_panel,
).show()
