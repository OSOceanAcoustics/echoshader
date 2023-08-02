from typing import List, Union

import panel
import param
import xarray
from box import get_box_plot, get_box_stream
from curtain import curtain_plot
from echogram import single_echogram, tricolor_echogram
from hist import hist_plot, table_plot
from map import track_plot
from utils import curtain_opts, tiles

import logging
import warnings
from bokeh.util.warnings import BokehUserWarning

warnings.simplefilter(action="ignore", category=BokehUserWarning)
logging.getLogger("param").setLevel(logging.CRITICAL)


@xarray.register_dataset_accessor("eshader")
class Echoshader(param.Parameterized):
    """
    A class for interactive echogram visualization and track plotting using HoloViews and Panel.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        A dataset containing the data for echogram visualization and track plotting.

    Attributes
    ----------
    color_map : panel.widgets.LiteralInput
        A widget to select the colormap for echogram visualization.
    Sv_range_slider : panel.widgets.EditableRangeSlider
        A widget to adjust the range of Sv values for echogram visualization.
    tile_select : panel.widgets.Select
        A widget to select the map tile for track plotting.
    curtain_ratio : panel.widgets.FloatInput
        A widget to adjust the vertical spacing (Z-axis) for 3D curtain(not currently used).
    bin_size_input : panel.widgets.IntInput
        A widget to input the bin size for echogram histogram plots (not currently used).
    overlay_layout_toggle : panel.widgets.Toggle
        A widget to toggle the overlay and layout of echogram plots.

    Methods
    -------
    echogram(channel: Union[str, List[str]], cmap: Union[str, List[str]] = None,
             vmin: float = None, vmax: float = None, rgb_composite: bool = False, *args, **kwargs)
        Create and display an echogram visualization for the specified channel(s).

    track(channel: str, tile: str = None, *args, **kwargs)
        Create and display a track plot for the specified channel.

    extract_data_from_gram_box()
        Extract data from the selected region on the echogram
        (not directly used in user interface).

    _tricolor_echogram_plot()
        Internal method to generate a tricolor echogram plot (internal to echogram() method).

    _echogram_plot()
        Internal method to generate an echogram plot (internal to echogram() method).

    _track_plot()
        Internal method to generate a track plot (internal to track() method).


    Example
    -------
    panel.Column(MVBS_ds.eshader.color_map,
                MVBS_ds.eshader.Sv_range_slider,
                MVBS_ds.eshader.echogram(channel=['GPT  18 kHz 009072058c8d 1-1 ES18-11',
                                                'GPT 120 kHz 00907205a6d0 4-1 ES120-7C',],
                                        )
                )

    panel.Column(MVBS_ds.eshader.tile_select,
                MVBS_ds.eshader.track('GPT 120 kHz 00907205a6d0 4-1 ES120-7C'),
    )
    """

    def __init__(self, MVBS_ds: xarray.Dataset):
        super().__init__()

        self.MVBS_ds = MVBS_ds

        self._init_widget()

        self._init_param()

    def _init_widget(self):
        self.color_map = panel.widgets.LiteralInput(
            name="Color Map", value="jet", type=(str, list)
        )

        self.Sv_range_slider = panel.widgets.EditableRangeSlider(
            name="Sv Range Slider",
            start=self.MVBS_ds.Sv.actual_range[0],
            end=self.MVBS_ds.Sv.actual_range[-1],
            value=(self.MVBS_ds.Sv.actual_range[0], self.MVBS_ds.Sv.actual_range[-1]),
            step=0.01,
        )

        self.channel_select = panel.widgets.Select(
            name="Channel Select", options=self.MVBS_ds.channel.values.tolist()
        )

        self.tile_select = panel.widgets.Select(
            name="Map Tile Select", value="OSM", options=tiles
        )

        self.curtain_ratio = panel.widgets.FloatInput(
            name="Ratio Input (Z Spacing)", value=0.001, step=1e-5, start=0
        )

        self.bin_size_input = panel.widgets.IntInput(
            name="Bin Size Input", value=24, step=10, start=0
        )

        self.overlay_layout_toggle = panel.widgets.Toggle(
            name="Overlay & Layout Toggle", value=True
        )

        self.update_echogram_button = panel.widgets.Button(
            name="Update Echogram 🔈", button_type="primary"
        )

        self.update_track_button = panel.widgets.Button(
            name="Update Positions 🗺️", button_type="primary"
        )

        self.update_stats_button = panel.widgets.Button(
            name="Update Positions 📊", button_type="primary"
        )

        self.reset_button = panel.widgets.Button(name="Reset 🔁", button_type="primary")

    def _init_param(self):
        self.box_dict = {}

        self.gram_box = None

        self.track_box = None

        self.MVBS_ds_gram_box = self.MVBS_ds

        self.MVBS_ds_track_box = self.MVBS_ds

    def echogram(
        self,
        channel: List[str],
        cmap: Union[str, List[str]] = None,
        vmin: float = None,
        vmax: float = None,
        rgb_composite: bool = False,
        *args,
        **kwargs
    ):
        if cmap is not None:
            self.color_map.value = cmap

        data_vmin = self.Sv_range_slider.value[0]
        data_vmax = self.Sv_range_slider.value[1]

        self.Sv_range_slider.value = (
            vmin if vmin is not None else data_vmin,
            vmax if vmax is not None else data_vmax,
        )

        if rgb_composite is True:
            if len(channel) != 3:
                raise ValueError(
                    "Must have exactly 3 frequency channels for tricolor echogram."
                )

            self.tri_channel = channel

            return self._tricolor_echogram_plot

        else:
            self.channel = channel

            return self._echogram_plot

    @param.depends(
        "Sv_range_slider.value",
        "update_echogram_button.value",
    )
    def _tricolor_echogram_plot(self):
        rgb_map = {}
        rgb_map[self.tri_channel[0]] = "R"
        rgb_map[self.tri_channel[1]] = "G"
        rgb_map[self.tri_channel[2]] = "B"

        echogram = tricolor_echogram(
            self.MVBS_ds,
            self.Sv_range_slider.value[0],
            self.Sv_range_slider.value[1],
            rgb_map,
        )

        # get box stream from echogram
        self.box_dict["rgb_composite"] = get_box_stream(echogram)

        # plot box using bounds
        bounds = get_box_plot(get_box_stream(echogram))

        return echogram * bounds

    @param.depends(
        "Sv_range_slider.value",
        "color_map.value",
        "update_echogram_button.value",
    )
    def _echogram_plot(self):
        echograms = single_echogram(
            self.MVBS_ds,
            self.channel[0],
            self.color_map.value,
            self.Sv_range_slider.value,
        )

        # get box stream from echogram
        self.box_dict[self.channel[0]] = get_box_stream(echograms)

        # plot box using bounds
        bounds = get_box_plot(get_box_stream(echograms))

        echograms *= bounds

        for ch in self.channel:
            if ch == self.channel[0]:
                continue

            echogram = single_echogram(
                self.MVBS_ds, ch, self.color_map.value, self.Sv_range_slider.value
            )

            # get box stream from echogram
            self.box_dict[ch] = get_box_stream(echogram)

            # plot box using bounds
            bounds = get_box_plot(get_box_stream(echogram))

            echograms += echogram * bounds

        if len(self.channel) == 1:
            return echograms

        return echograms.cols(1)

    def track(self, channel: str, tile: str = None, *args, **kwargs):
        if tile is not None:
            self.tile_select.value = tile

        self.gram_box = self.box_dict[channel]

        return self._track_plot

    @param.depends("tile_select.value", "update_track_button.value")
    def _track_plot(self):
        self.MVBS_ds_gram_box = self.extract_data_from_gram_box()

        track = track_plot(
            MVBS_ds=self.MVBS_ds_gram_box, map_tiles=self.tile_select.value
        )

        return track

    def curtain(
        self,
        ratio: float = None,
    ):
        if ratio is not None:
            self.curtain_ratio.value = ratio

        return self._curtain_plot

    @param.depends(
        "color_map.value",
        "Sv_range_slider.value",
        "curtain_ratio.value",
    )
    def _curtain_plot(self):
        self.MVBS_ds_gram_box = self.extract_data_from_gram_box()

        curtain = curtain_plot(
            MVBS_ds=self.MVBS_ds_gram_box,
            cmap=self.color_map.value,
            clim=self.Sv_range_slider.value,
            ratio=self.curtain_ratio.value,
        )

        curtain_panel = panel.panel(
            curtain.ren_win,
            height=curtain_opts["height"],
            width=curtain_opts["width"],
            orientation_widget=True,
        )

        return curtain_panel

    def hist(self, bins: int = None, overlay: bool = None):
        if bins is not None:
            self.bin_size_input.value = bins

        if overlay is not None:
            self.overlay_layout_toggle.value = overlay

        return self._hist_plot

    @param.depends(
        "bin_size_input.value",
        "overlay_layout_toggle.value",
        "update_stats_button.value",
    )
    def _hist_plot(self):
        MVBS_ds_in_box = self.extract_data_from_gram_box()

        hist = hist_plot(
            MVBS_ds_in_box,
            bins=self.bin_size_input.value,
            overlay=self.overlay_layout_toggle.value,
        )

        return hist

    def table(self):
        return self._table_plot

    @param.depends("update_stats_button.value")
    def _table_plot(self):
        MVBS_ds_in_box = self.extract_data_from_gram_box()

        table = table_plot(MVBS_ds=MVBS_ds_in_box)

        return table

    @param.depends("reset.value")
    def reset(self):
        pass

    def extract_data_from_gram_box(self):
        MVBS_ds_in_gram_box = self.MVBS_ds.sel(
            ping_time=slice(self.gram_box.bounds[0], self.gram_box.bounds[2]),
            echo_range=slice(self.gram_box.bounds[1], self.gram_box.bounds[3])
            if self.gram_box.bounds[3] > self.gram_box.bounds[1]
            else slice(self.gram_box.bounds[3], self.gram_box.bounds[1]),
        )

        return MVBS_ds_in_gram_box

    def extract_data_from_track_box(self):
        MVBS_ds_in_track_box = self.MVBS_ds.sel(
            ping_time=slice(self.track_box.bounds[0], self.track_box.bounds[2]),
            echo_range=slice(self.track_box.bounds[1], self.track_box.bounds[3])
            if self.track_box.bounds[3] > self.track_box.bounds[1]
            else slice(self.track_box.bounds[3], self.track_box.bounds[1]),
        )

        return MVBS_ds_in_track_box

    def extract_data_from_box(self):
        pass
