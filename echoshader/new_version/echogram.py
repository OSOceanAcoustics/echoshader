from typing import Dict, List, Literal, Union

import holoviews
import numpy
import panel
import param
import xarray
from get_box import get_box_plot, get_box_stream, get_lasso_stream
from get_map import (
    convert_EPSG,
    get_tile_options,
    plot_curtain,
    plot_positions,
    plot_tiles,
)
from get_rgb import convert_to_color
from get_stats import plot_hist, plot_table

holoviews.extension("bokeh", logo=False)


@xarray.register_dataset_accessor("eshader")
class Echogram(param.Parameterized):
    """
    A class for creating echogram visualizations from MVBS datasets.
    """

    def __init__(self, MVBS_ds: xarray.Dataset):
        """
        Initialize the Echogram object.

        Args:
            MVBS_ds (xarray.Dataset): The MVBS dataset.
        """
        super().__init__()

        self.MVBS_ds = MVBS_ds

        self.gram_opts = {
            "Image": {
                "cmap": "jet",
                "colorbar": True,
                "tools": ["box_select", "lasso_select", "hover"],
                "invert_yaxis": False,
                "width": 600,
            },
            "RGB": {"tools": ["hover"], "invert_yaxis": False, "width": 600},
        }

        self.curtain_width = 700

        self.curtain_height = 500

        self._init_widget()

    def _init_widget(self):
        """
        Initialize the interactive widgets for controlling the echogram visualization.
        """
        self.channel_select = panel.widgets.Select(
            name="Channel Select", options=self.MVBS_ds.channel.values.tolist()
        )

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

        self.tile_select = panel.widgets.Select(
            name="Map Tile Select", value="OSM", options=get_tile_options()
        )

        self.curtain_ratio = panel.widgets.FloatInput(
            name="Ratio Input (Z Spacing)", value=0.001, step=1e-5, start=0
        )

        self.link_mode_select = panel.widgets.Select(
            name="Link Mode Select",
            options={
                "Track controled by Echogram": True,
                "Echogram controled by Track": False,
            },
        )

        self.update_echogram_button = panel.widgets.Button(
            name="Update/Reset Echogram 🔈", button_type="primary"
        )

        self.update_positions_button = panel.widgets.Button(
            name="Update/Reset Positions 🗺️", button_type="primary"
        )

        self.bin_size_input = panel.widgets.IntInput(
            name="Bin Size Input", value=24, step=10, start=0
        )

        self.overlay_layout_toggle = panel.widgets.Toggle(
            name="Overlay & Layout Toggle", value=True
        )

    def echogram_multiple_frequency(
        self,
        cmap: Union[str, List[str]] = "jet",
        vmin: float = None,
        vmax: float = None,
        layout: Literal[
            "single_frequency", "multiple_frequency", "composite"
        ] = "single_frequency",
        rgb_map: Dict[str, str] = {},
        *args,
        **kwargs
    ):
        """
        Generate general echogram visualizations without specified channel and control widgets.

        Args:
            cmap (str or list, optional): The colormap(s) to use.
            Input list like ['#0000ff'] to customize. Defaults to 'jet'.
            vmin (float, optional): The minimum value for the color range. Defaults to None.
            vmax (float, optional): The maximum value for the color range. Defaults to None.
            layout (str, optional): The layout of the echogram visualizations.
                Must be one of 'single_frequency', 'multiple_frequency', or 'composite'.
                Defaults to 'single_frequency'.
            rgb_map (Dict[str, str], optional): The mapping of channels to RGB color channels
                for composite visualization. Defaults to an empty dictionary.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            panel.Tabs or panel.Column or holoviews.RGB: The generated visualizations.
        """
        self.gram_opts["Image"]["cmap"] = cmap

        if vmin is None:
            vmin = self.MVBS_ds.Sv.actual_range[0]

        if vmax is None:
            vmax = self.MVBS_ds.Sv.actual_range[-1]

        self.gram_opts["Image"]["clim"] = (vmin, vmax)

        if layout == str("single_frequency"):
            tabs = panel.Tabs()

            for index, channel in enumerate(self.MVBS_ds.channel.values):
                plot = (
                    holoviews.Dataset(self.MVBS_ds.sel(channel=channel))
                    .to(
                        holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"]
                    )
                    .opts(self.gram_opts)
                )
                tab = panel.Column(panel.pane.Markdown("## " + channel), plot)
                tabs.append(("channel" + " " + str(index + 1), tab))

            return tabs

        elif layout == str("multiple_frequency"):
            col = panel.Column()

            for index, channel in enumerate(self.MVBS_ds.channel.values):
                plot = (
                    holoviews.Dataset(self.MVBS_ds.sel(channel=channel))
                    .to(
                        holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"]
                    )
                    .opts(self.gram_opts)
                )

                col.append(panel.pane.Markdown("## " + channel))
                col.append(plot)

            return col

        elif layout == str("composite"):
            if rgb_map == {}:
                rgb_map[self.MVBS_ds.channel.values[0]] = "R"
                rgb_map[self.MVBS_ds.channel.values[1]] = "G"
                rgb_map[self.MVBS_ds.channel.values[2]] = "B"

            rgb_ch = {"R": None, "G": None, "B": None}

            for ch, color in rgb_map.items():
                rgb_ch[color] = convert_to_color(
                    self.MVBS_ds, channel_sel=ch, th_bottom=vmin, th_top=vmax
                )

            rgb = holoviews.RGB(
                (
                    self.MVBS_ds.ping_time.data,
                    self.MVBS_ds.echo_range.data,
                    rgb_ch["R"],
                    rgb_ch["G"],
                    rgb_ch["B"],
                )
            ).opts(self.gram_opts)

            return rgb

    @param.depends(
        "channel_select.value",
        "Sv_range_slider.value",
        "color_map.value",
        "update_echogram_button.value",
    )
    def echogram_single_frequency(
        self,
        channel: str = None,
        cmap: Union[str, List[str]] = None,
        vmin: float = None,
        vmax: float = None,
        link_to_track: bool = None,
        *args,
        **kwargs
    ):
        """
        Generate an echogram visualization for a specific channel and settings.

        Args:
            channel (str, optional): The channel to visualize. Defaults to None.
            cmap (str or list, optional): The colormap(s) to use.
            Input list like ['#0000ff'] to customize. Defaults to None.
            vmin (float, optional): The minimum value for the color range. Defaults to None.
            vmax (float, optional): The maximum value for the color range. Defaults to None.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            holoviews.DynamicMap: The generated echogram visualization with bounds.
        """
        if channel is not None:
            self.channel_select.value = channel

        if cmap is not None:
            self.color_map.value = cmap

        self.gram_opts["Image"]["cmap"] = self.color_map.value

        data_vmin = self.Sv_range_slider.value[0]
        data_vmax = self.Sv_range_slider.value[1]
        self.Sv_range_slider.value = (
            vmin if vmin is not None else data_vmin,
            vmax if vmax is not None else data_vmax,
        )
        self.gram_opts["Image"]["clim"] = self.Sv_range_slider.value

        if link_to_track is not None:
            self.link_mode_select.value = not link_to_track

        if self.link_mode_select.value is False and self.positions_box is not None:
            echogram = (
                holoviews.Dataset(
                    self.MVBS_ds.where(
                        (self.MVBS_ds.longitude > self.positions_box.bounds[0])
                        & (self.MVBS_ds.latitude > self.positions_box.bounds[1])
                        & (self.MVBS_ds.longitude < self.positions_box.bounds[2])
                        & (self.MVBS_ds.latitude < self.positions_box.bounds[3])
                    ).sel(channel=self.channel_select.value)
                )
                .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
                .opts(self.gram_opts)
            )

        else:
            echogram = (
                holoviews.Dataset(self.MVBS_ds.sel(channel=self.channel_select.value))
                .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
                .opts(self.gram_opts)
            )

        # get box stream from echogram
        self.box = get_box_stream(echogram)

        # get lasso stream from echogram
        self.lasso = get_lasso_stream(echogram)

        # plot box using bounds
        bounds = get_box_plot(self.box)

        return echogram * bounds

    def extract_data_from_box(self, all_channels: bool = True):
        """
        Get MVBS data with a specific frequency from the selected box

        Parameters:
            all_channels (bool, optional): Flag
                indicating whether to extract data from all channels or not.
                Defaults to True.

        Returns:
            xarray.Dataset: A subset of the MVBS dataset containing data within the specified box.
                The subset is determined by the selected channels, ping time, and echo range.
        """

        return self.MVBS_ds.sel(
            channel=self.MVBS_ds.channel.values
            if all_channels is True
            else self.channel_select.value,
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[1], self.box.bounds[3])
            if self.box.bounds[3] > self.box.bounds[1]
            else slice(self.box.bounds[3], self.box.bounds[1]),
        )

    @param.depends("update_positions_button.value")
    def positions(self, link_to_echogram: bool = None):
        """
        Generates a ship track or moored point plot based on the selected options.

        Args:
            link_to_echogram (bool, optional): Whether to link the positions plot to the echogram.

        Returns:
            holoviews.Overlay: The generated ship or moored point positions plot and starting point.
        """
        if link_to_echogram is not None:
            self.link_mode_select.value = link_to_echogram

        if self.link_mode_select.value is True and self.box is not None:
            time_range = slice(self.box.bounds[0], self.box.bounds[2])
            positions_plot = plot_positions(
                MVBS_ds=self.MVBS_ds.sel(ping_time=time_range)
            )
        else:
            positions_plot = plot_positions(MVBS_ds=self.MVBS_ds)

        left = numpy.nanmin(self.MVBS_ds.longitude.values)
        bottom = numpy.nanmin(self.MVBS_ds.latitude.values)
        right = numpy.nanmax(self.MVBS_ds.longitude.values)
        top = numpy.nanmax(self.MVBS_ds.latitude.values)

        # get box stream
        self.positions_box = get_box_stream(positions_plot, (left, bottom, right, top))

        return positions_plot

    @param.depends(
        "tile_select.value",
        "update_positions_button.value",
    )
    def tile(self, map_tiles: str = None):
        """
        Generates a tile plot based on the selected map tiles and bounds with box select.

        Args:
            map_tiles (str, optional): The selected map tiles.

        Returns:
            holoviews.DynamicMap: A geoviews dynamic object.
        """
        if map_tiles is not None:
            self.tile_select.value = map_tiles

        tile_plot = plot_tiles(self.tile_select.value)

        left = numpy.nanmin(self.MVBS_ds.longitude.values)
        bottom = numpy.nanmin(self.MVBS_ds.latitude.values)
        right = numpy.nanmax(self.MVBS_ds.longitude.values)
        top = numpy.nanmax(self.MVBS_ds.latitude.values)

        bottom, left = convert_EPSG(lat=bottom, lon=left, mercator_to_coord=False)
        top, right = convert_EPSG(lat=top, lon=right, mercator_to_coord=False)

        # get box stream
        tile_box = get_box_stream(tile_plot, (left, bottom, right, top))

        # plot box using bounds
        bounds = get_box_plot(tile_box)

        return tile_plot * bounds

    @param.depends(
        "tile_select.value",
        "update_positions_button.value",
    )
    def positions_with_tile(self, link_to_echogram: bool = None, map_tiles: str = None):
        return self.positions(link_to_echogram) * self.tile(map_tiles)

    @param.depends(
        "curtain_ratio.value",
        "update_echogram_button.value",
        "update_positions_button.value",
    )
    def curtain(
        self,
        channel: str = None,
        cmap: Union[str, List[str]] = None,
        vmin: float = None,
        vmax: float = None,
        ratio: float = None,
        linked: bool = True,
    ):
        """
        Generates a curtain plot based on the provided parameters.

        Args:
            channel (str, optional): The channel to be displayed in the curtain plot.
            cmap (str, List[str], optional): The colormap(s) to be used for color mapping.
            vmin (float, optional): The minimum value for color mapping.
            vmax (float, optional): The maximum value for color mapping.
            ratio (float, optional): The aspect ratio of the curtain plot.
            linked (bool, optional): Link to echogram and positions plot. Default is True.

        Returns:
            panel.panel: A Panel panel object containing the generated curtain plot.
        """
        if channel is not None:
            self.channel_select.value = channel

        if cmap is not None:
            self.color_map.value = cmap

        if vmin is not None:
            self.Sv_range_slider.value[0] = vmin

        if vmax is not None:
            self.Sv_range_slider.value[1] = vmax

        if ratio is not None:
            self.curtain_ratio.value = ratio

        self.curatin_link = linked

        if (
            self.link_mode_select.value is True
            and self.box is not None
            and self.curatin_link
        ):
            ping_time = slice(self.box.bounds[0], self.box.bounds[2])

            echo_range = (
                slice(self.box.bounds[1], self.box.bounds[3])
                if self.box.bounds[3] > self.box.bounds[1]
                else slice(self.box.bounds[3], self.box.bounds[1])
            )

            curtain = plot_curtain(
                MVBS_ds=self.MVBS_ds.sel(
                    channel=self.channel_select.value,
                    ping_time=ping_time,
                    echo_range=echo_range,
                ),
                cmap=self.color_map.value,
                clim=self.Sv_range_slider.value,
                ratio=self.curtain_ratio.value,
            )

        elif (
            self.link_mode_select.value is False
            and self.positions_box is not None
            and self.curatin_link
        ):
            curtain = plot_curtain(
                MVBS_ds=self.MVBS_ds.where(
                    (self.MVBS_ds.longitude > self.positions_box.bounds[0])
                    & (self.MVBS_ds.latitude > self.positions_box.bounds[1])
                    & (self.MVBS_ds.longitude < self.positions_box.bounds[2])
                    & (self.MVBS_ds.latitude < self.positions_box.bounds[3])
                ).sel(
                    channel=self.channel_select.value,
                ),
                cmap=self.color_map.value,
                clim=self.Sv_range_slider.value,
                ratio=self.curtain_ratio.value,
            )

        else:
            curtain = plot_curtain(
                MVBS_ds=self.MVBS_ds.sel(
                    channel=self.channel_select.value,
                ),
                cmap=self.color_map.value,
                clim=self.Sv_range_slider.value,
                ratio=self.curtain_ratio.value,
            )

        curtain_panel = panel.panel(
            curtain.ren_win,
            height=self.curtain_height,
            width=self.curtain_width,
            orientation_widget=True,
        )

        return curtain_panel
    
    @param.depends(
        "box.bounds",
        "bin_size_input.value",
        "overlay_layout_toggle.value",
    )
    def histogram(self,
                  bins: int = None,
                  overlay: bool = None,
                  ):
        
        if bins is not None:
            self.bin_size_input.value = bins
        
        if overlay is not None:
            self.overlay_layout_toggle.value = overlay

        ping_time = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = (
            slice(self.box.bounds[1], self.box.bounds[3])
            if self.box.bounds[3] > self.box.bounds[1]
            else slice(self.box.bounds[3], self.box.bounds[1])
        )

        return plot_hist(
            MVBS_ds=self.MVBS_ds.sel(
                ping_time=ping_time,
                echo_range=echo_range,
            ),
            bins = self.bin_size_input.value,
            overlay = self.overlay_layout_toggle.value
        )
    
    @param.depends("box.bounds")
    def table(self):
        ping_time = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = (
            slice(self.box.bounds[1], self.box.bounds[3])
            if self.box.bounds[3] > self.box.bounds[1]
            else slice(self.box.bounds[3], self.box.bounds[1])
        )

        return plot_table(
            MVBS_ds=self.MVBS_ds.sel(
                ping_time=ping_time,
                echo_range=echo_range,
            )
        )
        
