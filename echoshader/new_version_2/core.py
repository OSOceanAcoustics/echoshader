from typing import Dict, List, Union

import panel
import param
import xarray
from box import get_box_plot, get_box_stream, get_lasso_stream
from echogram import echogram_single_frequency, tricolor_echogram
from map import track_plot
from utils import tiles


@xarray.register_dataset_accessor("eshader")
class Echoshader(param.Parameterized):
    def __init__(self, MVBS_ds: xarray.Dataset):
        super().__init__()

        self.MVBS_ds = MVBS_ds

        self.MVBS_ds_box = MVBS_ds

        self._init_color_map()

        self._init_Sv_range_slider()

        self._init_echogram()

        self._init_tile_select()

    def _init_color_map(self):
        self.color_map_dict = {}

        for _, channel in enumerate(self.MVBS_ds.channel.values):
            color_map = panel.widgets.LiteralInput(
                name="Color Map:" + channel, value="jet", type=(str, list)
            )

            self.color_map_dict[channel] = color_map

    def _init_Sv_range_slider(self):
        self.Sv_range_slider_dict = {}

        for _, channel in enumerate(self.MVBS_ds.channel.values):
            start = self.MVBS_ds.sel(channel=channel).Sv.actual_range[0]
            end = self.MVBS_ds.sel(channel=channel).Sv.actual_range[-1]

            Sv_range_slider = panel.widgets.EditableRangeSlider(
                name="Sv Range Slider:" + channel,
                start=start,
                end=end,
                value=(start, end),
                step=0.01,
            )

            self.Sv_range_slider_dict[channel] = Sv_range_slider

    def echogram_with_bound(
        self,
        MVBS_ds: xarray,
        channel: str,
        cmap: Union[str, List[str]],
        value_range: tuple[float, float],
    ):
        echogram = echogram_single_frequency(MVBS_ds, channel, cmap, value_range)

        # get box stream from echogram
        self.box = get_box_stream(echogram)

        # get lasso stream from echogram
        self.lasso = get_lasso_stream(echogram)

        # plot box using bounds
        bounds = get_box_plot(self.box)

        return echogram * bounds

    def _init_echogram(self):
        self.echogram_dict = {}

        for _, channel in enumerate(self.MVBS_ds.channel.values):
            echogram = panel.bind(
                self.echogram_with_bound,
                MVBS_ds=self.MVBS_ds,
                channel=channel,
                cmap=self.color_map_dict[channel],
                value_range=self.Sv_range_slider_dict[channel],
            )
            self.echogram_dict[channel] = echogram

    def _init_tile_select(self):
        self.tile_select = panel.widgets.Select(
            name="Map Tile Select", value="OSM", options=tiles
        )

    def color_map(self, channel: List[str]):
        color_map_list = []

        for ch in channel:
            color_map_list.append(self.color_map_dict[ch])

        return color_map_list

    def Sv_range_slider(self, channel: List[str]):
        Sv_range_slider_list = []

        for ch in channel:
            Sv_range_slider_list.append(self.Sv_range_slider_dict[ch])

        return Sv_range_slider_list

    def echogram(
        self,
        channel: List[str],
        cmap: Union[str, List[str]] = "jet",
        vmin: float = -80,
        vmax: float = -30,
        rgb_composite: bool = False,
        rgb_map: Dict[str, str] = {},
    ):
        if rgb_composite is True:
            if len(channel) != 3:
                raise ValueError(
                    "Must have exactly 3 frequency channels for tricolor echogram."
                )

            return tricolor_echogram(self.MVBS_ds, vmin, vmax, rgb_map)

        echogram_list = []

        for ch in channel:
            self.color_map_dict[ch].value = cmap
            self.Sv_range_slider_dict[ch].value = (vmin, vmax)
            echogram_list.append(self.echogram_dict[ch])

        if len(echogram_list) == 1:
            return echogram_list[0]
        else:
            return echogram_list

    @param.depends("box.bounds")
    def track(self, map_tiles: str = "OSM"):
        self.tile_select.value = map_tiles

        self.MVBS_ds_box = self.extract_data_from_box()

        self.track_map = panel.bind(
            track_plot, self.MVBS_ds_box, map_tiles=self.tile_select
        )

        return self.track_map

    def extract_data_from_box(self):
        return self.MVBS_ds.sel(
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[1], self.box.bounds[3])
            if self.box.bounds[3] > self.box.bounds[1]
            else slice(self.box.bounds[3], self.box.bounds[1]),
        )
