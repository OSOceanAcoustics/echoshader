from typing import Dict, Union

import holoviews
import panel
import param
import xarray


@xarray.register_dataset_accessor("eshader")
class Echogram(param.Parameterized):
    def __init__(self, MVBS_ds):
        super().__init__()

        self.MVBS_ds = MVBS_ds

        self.gram_opts = {
            "Image": {
                "cmap": "jet",
                "colorbar": True,
                "cmap": "jet",
                "tools": ["box_select", "lasso_select", "hover"],
                "invert_yaxis": False,
                "width": 600,
            }
        }

    def echogram(
        self,
        cmap: str = "jet",
        layout: Union[
            str("single_frequency"), str("multiple_frequency"), str("composite")
        ] = "single_frequency",
        vmin: float = None,
        vmax: float = None,
        rgb_map: Dict[str, str] = None,
        *args,
        **kwargs
    ):
        if vmin == None:
            vmin = self.MVBS_ds.Sv.actual_range[0]

        if vmax == None:
            vmax = self.MVBS_ds.Sv.actual_range[-1]

        self.gram_opts["Image"]["clim"] = (vmin, vmax)
        self.gram_opts["Image"]["cmap"] = cmap

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
            if rgb_map == None:
                pass
