from typing import Dict, List, Literal, Union

import holoviews
import numpy as np
import panel
import param
import xarray

from .get_box import get_box_plot, get_box_stream
from .get_rgb import convert_to_color
from .get_string_list import convert_string_to_list

holoviews.extension("bokeh", logo=False)


@xarray.register_dataset_accessor("eshader")
class Echogram(param.Parameterized):
    """
    A class for creating echogram visualizations from MVBS datasets.
    """

    def __init__(self, MVBS_ds):
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
                "width": 1800,
                "height": 350,
                "yticks": self._get_inverted_echo_range(),
            },
            "RGB": {
                "tools": ["hover"],
                "invert_yaxis": False,
                "width": 1800,
                "height": 800,
                "yticks": self._get_inverted_echo_range(),
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

        self.Sv_range_slider = panel.widgets.EditableRangeSlider(
            name="Sv Range Slider",
            start=self.MVBS_ds.Sv.actual_range[0],
            end=self.MVBS_ds.Sv.actual_range[-1],
            value=(self.MVBS_ds.Sv.actual_range[0], self.MVBS_ds.Sv.actual_range[-1]),
            step=0.01,
        )

        self.color_map = panel.widgets.TextInput(
            name="Color Map", value="jet", placeholder="jet"
        )

    def _get_inverted_echo_range(self):
        echo_range_max = self.MVBS_ds["echo_range"].data[0]
        yticks_labels = np.arange(0, echo_range_max, 50)
        yticks_values = echo_range_max - yticks_labels
        return list(zip(yticks_values, yticks_labels.astype(int).astype(str)))

    def echogram_multiple_frequency(
        self,
        cmap: Union[str, List[str]] = "jet",
        vmin: float = None,
        vmax: float = None,
        layout: Literal[
            "single_frequency", "multiple_frequency", "composite"
        ] = "single_frequency",
        rgb_map: Dict[str, str] = {},
        clipping_colors: dict = {},
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
        self.gram_opts["Image"]["clipping_colors"] = clipping_colors

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

                col.append(panel.pane.Markdown("### " + channel))
                col.append(plot)

            return col

        elif layout == str("composite"):
            if rgb_map == {}:
                rgb_map[self.MVBS_ds.channel.values[2]] = "R"
                rgb_map[self.MVBS_ds.channel.values[1]] = "G"
                rgb_map[self.MVBS_ds.channel.values[0]] = "B"

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

    @param.depends("channel_select.value", "Sv_range_slider.value", "color_map.value")
    def echogram_single_frequency(
        self,
        channel: str = None,
        cmap: Union[str, List[str]] = None,
        vmin: float = None,
        vmax: float = None,
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

        list_camp = convert_string_to_list(self.color_map.value)
        self.gram_opts["Image"]["cmap"] = (
            list_camp if list_camp is not False else self.color_map.value
        )

        if vmin is not None and vmax is not None:
            self.Sv_range_slider.start = vmin
            self.Sv_range_slider.end = vmax
            self.Sv_range_slider.value = (vmin, vmax)

        elif vmin is not None:
            self.Sv_range_slider.start = vmin
            old_vmax = self.Sv_range_slider.value[1]
            self.Sv_range_slider.value = (vmin, old_vmax)

        elif vmax is not None:
            self.Sv_range_slider.end = vmax
            old_vmin = self.Sv_range_slider.value[0]
            self.Sv_range_slider.value = (old_vmin, old_vmax)

        self.gram_opts["Image"]["clim"] = self.Sv_range_slider.value

        echogram = (
            holoviews.Dataset(self.MVBS_ds.sel(channel=self.channel_select.value))
            .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
            .opts(self.gram_opts)
        )

        # get box from echogram
        self.box = get_box_stream(echogram)

        # plot box
        bounds = get_box_plot(self.box)

        return echogram * bounds

    def extract_data_from_box(self, all_channels: bool = True):
        """
        Get Sv data with a specific frequency from the selected box

        Parameters:
            all_channels (bool, optional): Indicate whether to extract data from all channels.
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
