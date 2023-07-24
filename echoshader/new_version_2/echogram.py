from typing import List, Union

import holoviews
from utils import gram_opts

holoviews.extension("bokeh", logo=False)


def echogram_single_frequency(
    self,
    channel: str,
    cmap: Union[str, List[str]],
    vmin: float,
    vmax: float,
):
    gram_opts["Image"]["cmap"] = cmap

    gram_opts["Image"]["clim"] = (vmin, vmax)

    echogram = (
        holoviews.Dataset(self.MVBS_ds.sel(channel=channel))
        .to(holoviews.Image, vdims=["Sv"], kdims=["ping_time", "echo_range"])
        .opts(gram_opts)
    )

    return echogram
