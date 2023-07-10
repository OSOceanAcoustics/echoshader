from typing import Dict, List, Literal, Union

import holoviews
import panel
import param
import xarray
import numpy

from get_rgb import convert_to_color
from get_box import get_box_stream, get_lasso_stream, get_box_plot
from get_map import get_tile_options, convert_EPSG
from get_map import plot_tiles, plot_track, plot_point, plot_curtain

holoviews.extension("bokeh", logo=False)

@xarray.register_dataset_accessor("eshader")
class Echogram(param.Parameterized):
    """
    A class for creating echogram visualizations from MVBS datasets.
    """

    def __init__(self, 
                 MVBS_ds: xarray.Dataset):
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

            "RGB": {"tools": ["hover"], 
                    "invert_yaxis": False, 
                    "width": 600
                    },
        }

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
            name="Map Tile Select",
            value="OSM",
            options=get_tile_options()
        )

        self.curtain_ratio = panel.widgets.FloatInput(
            name="Ratio Input (Z Spacing)", value=0.001, step=1e-5, start=0
        )

        self.link_mode_select = panel.widgets.select(
            name='Link Mode Select', 
            options={'Track controled by Echogram': True, 
                     'Echogram controled by Track': False},
        )

        self.update_map_button = panel.widgets.Button(
            name="Update 🗺️", button_type="primary"
        )

        self.update_stats_button = panel.widgets.Button(
            name="Update 📊", button_type="primary"
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

    @param.depends("channel_select.value", 
                   "Sv_range_slider.value", 
                   "color_map.value"
                   "link_mode_select.value")
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
            holoviews.Image: The generated echogram visualization.
        """
        if channel is not None:
            self.channel_select.value = channel

        if cmap is not None:
            self.color_map.value = cmap

        self.gram_opts["Image"]["cmap"] = self.color_map.value

        old_vmin = self.Sv_range_slider.value[0]
        old_vmax = self.Sv_range_slider.value[1]
        self.Sv_range_slider.value = (vmin if vmin is not None else old_vmin, 
                                      vmax if vmax is not None else old_vmax)
        self.gram_opts["Image"]["clim"] = self.Sv_range_slider.value

        if link_to_track is not None:
            self.link_mode_select.value = not link_to_track
        
        if self.link_mode_select.value is False and self.track_box is not None:
            gram_plot = (
                holoviews.Dataset(self.MVBS_ds.where().sel(channel=self.channel_select.value))
                .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
                .opts(self.gram_opts)
            )            
            
        else:
            gram_plot = (
                holoviews.Dataset(self.MVBS_ds.sel(channel=self.channel_select.value))
                .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
                .opts(self.gram_opts)
            )

        # get box stream from echogram
        self.box = get_box_stream(gram_plot)

        # get lasso stream from echogram
        self.lasso = get_lasso_stream(gram_plot)

        # plot box using bounds
        bounds = get_box_plot(self.box)

        return gram_plot * bounds
    

    def extract_data_from_box(self, 
                              all_channels: bool = True):
        """
        Get MVBS data with a specific frequency from the selected box
        
        Parameters:
            all_channels (bool, optional): Flag indicating whether to extract data from all channels or not.
                Defaults to True.
                
        Returns:
            xarray.Dataset: A subset of the MVBS dataset containing data within the specified box.
                The subset is determined by the selected channels, ping time, and echo range.
        """

        return self.MVBS_ds.sel(
            channel = self.MVBS_ds.channel.values 
            if all_channels is True else self.channel_select.value,
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[1], self.box.bounds[3])
            if self.box.bounds[3] > self.box.bounds[1]
            else slice(self.box.bounds[3], self.box.bounds[1]),
        )
    
    @param.depends("update_map_button.value")    
    def ship_track(self,
                   link_to_echogram: bool = None):
        
        if link_to_echogram is not None:
            self.link_mode_select.value = link_to_echogram
            
        if self.link_mode_select.value is True:
            time_range = slice(self.box.bounds[0], self.box.bounds[2])
            track_plot = plot_track(MVBS_ds = self.MVBS_ds.sel(ping_time=time_range)) 
        else:
            track_plot = plot_track(MVBS_ds = self.MVBS_ds)

        l = numpy.nanmin(self.MVBS_ds.longitude.values)
        b = numpy.nanmin(self.MVBS_ds.latitude.values)
        r = numpy.nanmax(self.MVBS_ds.longitude.values)
        t = numpy.nanmax(self.MVBS_ds.latitude.values)

        # get box stream
        self.track_box = get_box_stream(track_plot, (l, b, r, t))

        return track_plot
        
    @param.depends("update_map_button.value")
    def moored_point(self):
        point_plot = plot_point(self.MVBS_ds)
        return point_plot
    
    @param.depends("update_map_button.value")
    def tile(self, 
             map_tiles: str = None):
        if map_tiles is not None:
            self.tile_select.value = map_tiles

        tile_plot = plot_tiles(self.tile_select.value)

        l = numpy.nanmin(self.MVBS_ds.longitude.values)
        b = numpy.nanmin(self.MVBS_ds.latitude.values)
        r = numpy.nanmax(self.MVBS_ds.longitude.values)
        t = numpy.nanmax(self.MVBS_ds.latitude.values)

        b, l = convert_EPSG(lat = b, lon = l, mercator_to_coord = False)
        t, r = convert_EPSG(lat = t, lon = r, mercator_to_coord = False)

        # get box stream
        map_box = get_box_stream(tile_plot, (l, b, r, t))

        # plot box using bounds
        bounds = get_box_plot(map_box)

        return tile_plot * bounds
    
    @param.depends("update_map_button.value")
    def curtain(self, 
                channel: str = None, 
                cmap: Union[str, List[str]] = None, 
                vmin: float = None,
                vmax: float = None,
                ratio: float = None,
                link_to_echogram: bool = True):

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
        
        if link_to_echogram is True:
            ping_time = slice(self.box.bounds[0], self.box.bounds[2])
        
            echo_range = (
                slice(self.box.bounds[1], self.box.bounds[3])
                if self.box.bounds[3] > self.box.bounds[1]
                else slice(self.box.bounds[3], self.box.bounds[1])
            )

        curtain = plot_curtain(
            MVBS_ds = self.MVBS_ds.sel(
                channel=self.channel_select.value, 
                ping_time=ping_time, 
                echo_range=echo_range
            ) if link_to_echogram is True else 
            self.MVBS_ds.sel(
                echo_range=echo_range
            ),
            colormap=self.color_map.value,
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