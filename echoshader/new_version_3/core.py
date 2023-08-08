from typing import List, Union

import holoviews
import panel
import param
import xarray
from box import get_box_plot, get_box_stream
from curtain import curtain_plot
from echogram import single_echogram, tricolor_echogram
from hist import hist_plot, table_plot
from map import convert_EPSG, get_track_corners, tile_plot, track_plot
from utils import curtain_opts, tiles

import logging
import warnings
from bokeh.util.warnings import BokehUserWarning
warnings.simplefilter(action="ignore", category=BokehUserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger("param").setLevel(logging.CRITICAL)

panel.extension("pyvista")
holoviews.extension("bokeh", logo=False)


@xarray.register_dataset_accessor("eshader")
class Echoshader(param.Parameterized):
    def __init__(self, MVBS_ds: xarray.Dataset):
        super().__init__()

        self.MVBS_ds = MVBS_ds

        self._init_widget()

        self._init_param()

    def _init_widget(self):
        self.colormap = panel.widgets.LiteralInput(
            name="Colormap", value="jet", type=(str, list)
        )

        self.Sv_range_slider = panel.widgets.EditableRangeSlider(
            name="Sv Range Slider",
            start=self.MVBS_ds.Sv.actual_range[0],
            end=self.MVBS_ds.Sv.actual_range[-1],
            value=(self.MVBS_ds.Sv.actual_range[0], self.MVBS_ds.Sv.actual_range[-1]),
            step=0.01,
        )

        self.tile_select = panel.widgets.Select(
            name="Map Tile Select", value="OSM", options=tiles
        )

        self.channel_select = panel.widgets.Select(
            name="Channel Select", options=self.MVBS_ds.channel.values.tolist()
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

        self.control_mode_select = panel.widgets.Select(
            name="Control Mode Select",
            options={
                "Echograms Control": True,
                "Tracks Control": False,
            },
        )

    def _init_param(self):
        self.gram_box_stream = holoviews.streams.BoundsXY()

        self.gram_bounds = get_box_plot(self.gram_box_stream)

        self.update_gram_flag = holoviews.streams.Counter()

        self.update_track_flag = holoviews.streams.Counter()

        self.MVBS_ds_in_gram_box = self.MVBS_ds

        self.MVBS_ds_in_track_box = self.MVBS_ds

    def echogram(
        self,
        channel: List[str] = None,
        cmap: Union[str, List[str]] = None,
        vmin: float = None,
        vmax: float = None,
        rgb_composite: bool = False,
        **kwargs,
    ):
        if cmap is not None:
            self.colormap.value = cmap

        data_vmin = self.Sv_range_slider.value[0]
        data_vmax = self.Sv_range_slider.value[1]

        self.Sv_range_slider.value = (
            vmin if vmin is not None else data_vmin,
            vmax if vmax is not None else data_vmax,
        )

        if rgb_composite is True:
            if channel is None or len(channel) != 3:
                raise ValueError(
                    "Must have exactly 3 frequency channels for tricolor echogram."
                )

            self.tri_channel = channel

            return self._tricolor_echogram_plot

        else:
            if channel is None:
                self.channel = self.MVBS_ds.channel.values
            else:
                self.channel = channel

            self.channel_select.options = self.channel

            return self._echogram_plot

    def _update_gram_box(self, bounds):
        self.gram_box_stream.update(bounds=bounds)
        
        self.MVBS_ds_in_gram_box = self._extract_data_from_gram_box(bounds)

        if self.control_mode_select.value is True:
            self.update_track_flag.event()

    def _update_gram_reset(self, resetting):

        self.update_gram_flag.event()

    def _extract_data_from_gram_box(self, bounds):
        if bounds is None:
            MVBS_ds_in_gram_box = self.MVBS_ds

        else:
            MVBS_ds_in_gram_box = self.MVBS_ds.sel(
                ping_time=slice(bounds[0], bounds[2]),
                echo_range=slice(bounds[1], bounds[3])
                if bounds[3] > bounds[1]
                else slice(bounds[3], bounds[1]),
            )

        return MVBS_ds_in_gram_box

    @param.depends(
        "Sv_range_slider.value",
        "update_gram_flag.counter",
    )
    def _tricolor_echogram_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds
        else:
            MVBS_ds = self.MVBS_ds_in_track_box

        rgb_map = {}
        rgb_map[self.tri_channel[0]] = "R"
        rgb_map[self.tri_channel[1]] = "G"
        rgb_map[self.tri_channel[2]] = "B"

        echogram = tricolor_echogram(
            MVBS_ds,
            self.Sv_range_slider.value[0],
            self.Sv_range_slider.value[1],
            rgb_map,
        )

        # get box stream from echogram
        box_stream = get_box_stream(echogram)

        # add subscriber to update unified box select
        box_stream.add_subscriber(self._update_gram_box)

        # set inital value of box stream
        self._update_gram_box(tuple(echogram.lbrt))

        reset_stream = holoviews.streams.PlotReset(source = bounds)

        reset_stream.add_subscriber(self._update_gram_reset)

        bounds  =  self.gram_bounds

        return echogram * bounds

    @param.depends(
        "Sv_range_slider.value",
        "colormap.value",
        "update_gram_flag.counter",
    )
    def _echogram_plot(self):        
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds
        else:
            MVBS_ds = self.MVBS_ds_in_track_box

        echograms_list = []

        for channel in self.channel:
            echogram = single_echogram(
                MVBS_ds, 
                channel, 
                self.colormap.value, 
                self.Sv_range_slider.value
            )

            # get box stream from echogram
            box_stream = get_box_stream(echogram)

            # add subscriber to update unified box select
            box_stream.add_subscriber(self._update_gram_box)

            echograms_list.append(echogram)


        # set inital value of box stream
        self._update_gram_box(tuple(echograms_list[0].lbrt))

        reset_stream = holoviews.streams.PlotReset(source = echograms_list[0])

        reset_stream.add_subscriber(self._update_gram_reset)

        # get echograms stack
        echograms = holoviews.Layout(echograms_list).cols(1)

        bounds = self.gram_bounds
 
        return  echograms * bounds

    def track(
        self, 
        tile: str = None, 
        **kwargs,
    ):
        if tile is not None:
            self.tile_select.value = tile

        return self._track_tile_plot

    def _extract_data_from_track_box(self, bounds):
        if bounds is None or (bounds[0] == bounds[2] or bounds[1] == bounds[3]):
            self.MVBS_ds_in_track_box = self.MVBS_ds
        else:
            self.MVBS_ds_in_track_box = self.MVBS_ds.where(
                (self.MVBS_ds.longitude > bounds[0])
                & (self.MVBS_ds.latitude > bounds[1])
                & (self.MVBS_ds.longitude < bounds[2])
                & (self.MVBS_ds.latitude < bounds[3])
            )

            # self.MVBS_ds_in_track_box = MVBS_ds_in_track_box.dropna(dim="ping_time", how="all")

        return self.MVBS_ds_in_track_box

    def _update_track_reset(self, resetting):
        self.update_track_flag.event()

    def _update_track_box(self, bounds):
        self.MVBS_ds_in_track_box = self._extract_data_from_track_box(bounds)

        if self.control_mode_select.value is False:
            self.update_gram_flag.event()

    @param.depends(
        "tile_select.value",
        "update_track_flag.counter",
    )
    def _track_tile_plot(self):
        track = self._track_plot() * self._tile_plot()

        return track

    def _tile_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds_in_gram_box
        else:
            MVBS_ds = self.MVBS_ds

        tile = tile_plot(self.tile_select.value)

        left, bottom, right, top = get_track_corners(MVBS_ds)

        bottom, left = convert_EPSG(lat=bottom, lon=left, mercator_to_coord=False)
        top, right = convert_EPSG(lat=top, lon=right, mercator_to_coord=False)

        center_lon = (left + right) / 2
        center_lat = (bottom + top) / 2
        center = (center_lon, center_lat, center_lon, center_lat)

        self.tile_box_stream = get_box_stream(tile, center)

        tile_bounds = get_box_plot(self.tile_box_stream)

        reset_stream = holoviews.streams.PlotReset(source = tile_bounds)

        reset_stream.add_subscriber(self._update_track_reset)

        return tile * tile_bounds

    def _track_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds_in_gram_box
        else:
            MVBS_ds = self.MVBS_ds

        track = track_plot(MVBS_ds)

        left, bottom, right, top = get_track_corners(MVBS_ds)

        self.track_box_stream = get_box_stream(track, (left, bottom, right, top))

        self.track_box_stream.add_subscriber(self._update_track_box)

        self._update_track_box((left, bottom, right, top))

        return track

    def curtain(
        self,
        channel: str = None,
        ratio: float = None,
    ):
        if channel is not None:
            self.channel_select.value = channel

        if ratio is not None:
            self.curtain_ratio.value = ratio

        return self._curtain_plot

    @param.depends(
        "colormap.value",
        "Sv_range_slider.value",
        "channel_select.value",
        "curtain_ratio.value",
        "update_gram_flag.counter",
        "update_track_flag.counter",
    )
    def _curtain_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds_in_gram_box
        else:
            MVBS_ds = self.MVBS_ds_in_track_box

        curtain = curtain_plot(
            MVBS_ds=MVBS_ds.sel(channel=self.channel_select.value),
            cmap=self.colormap.value,
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
        "update_gram_flag.counter",
        "update_track_flag.counter",
    )
    def _hist_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds_in_gram_box
        else:
            MVBS_ds = self.MVBS_ds_in_track_box

        hist = hist_plot(
            MVBS_ds,
            bins=self.bin_size_input.value,
            overlay=self.overlay_layout_toggle.value,
        )

        return hist

    def table(self):
        return self._table_plot

    @param.depends(
        "update_gram_flag.counter",
        "update_track_flag.counter",
    )
    def _table_plot(self):
        if self.control_mode_select.value is True:
            MVBS_ds = self.MVBS_ds_in_gram_box
        else:
            MVBS_ds = self.MVBS_ds_in_track_box

        table = table_plot(MVBS_ds=MVBS_ds)

        return table