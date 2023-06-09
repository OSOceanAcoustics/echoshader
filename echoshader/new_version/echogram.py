from typing import Dict, Union

import holoviews
import panel
import param
import xarray
from get_rgb import convert_to_color


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
                "width": 600,
            },
            "RGB": {"tools": ["hover"], "invert_yaxis": False, "width": 600},
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

    def echograms(
        self,
        cmap: str = "jet",
        vmin: float = None,
        vmax: float = None,
        layout: Union[
            str("single_frequency"), str("multiple_frequency"), str("composite")
        ] = "single_frequency",
        rgb_map: Dict[str, str] = {},
        *args,
        **kwargs
    ):
        """
        Generate general echogram visualizations without specified channel and control widgets.

        Args:
            cmap (str, optional): The colormap to use. Defaults to 'jet'.
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

        if layout == "single_frequency":
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

        elif layout == "multiple_frequency":
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

        elif layout == "composite":
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

    @param.depends("channel_select.value", "Sv_range_slider.value", "color_map.value")
    def echogram(
        self,
        channel: str = None,
        cmap: str = None,
        vmin: float = None,
        vmax: float = None,
        *args,
        **kwargs
    ):
        """
        Generate an echogram visualization for a specific channel and settings.

        Args:
            channel (str, optional): The channel to visualize. Defaults to None.
            cmap (str, optional): The colormap to use. Defaults to None.
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

        plot = (
            holoviews.Dataset(self.MVBS_ds.sel(channel=self.channel_select.value))
            .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
            .opts(self.gram_opts)
        )

        return plot
