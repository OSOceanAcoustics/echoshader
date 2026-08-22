import holoviews
import numpy
import xarray


def echogram(
    MVBS_ds: xarray.Dataset,
    channel: str | list[str] | None = None,
    vert_dim: str = "echo_range",
):
    """
    Create single- or multi-channel echograms.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        Dataset containing the ``Sv`` variable.
    channel : str or list[str], optional
        Channel or channels to plot. If None, all channels are plotted.
    vert_dim : str, optional
        Name of the vertical dimension. Default is ``"echo_range"``.

    Returns
    -------
    holoviews.Image or holoviews.Layout
        A single echogram or a vertical layout of echograms.
    """
    if channel is None:
        channels = MVBS_ds.channel.values.tolist()
    elif isinstance(channel, str):
        channels = [channel]
    else:
        channels = channel

    echograms = [
        single_echogram(
            MVBS_ds=MVBS_ds,
            channel=ch,
            vert_dim=vert_dim,
        )
        for ch in channels
    ]

    if len(echograms) == 1:
        return echograms[0]

    return holoviews.Layout(echograms).cols(1)


def single_echogram(
    MVBS_ds: xarray.Dataset,
    channel: str,
    vert_dim: str = "echo_range",
):
    """Create an echogram for one acoustic channel."""
    dataset = holoviews.Dataset(
        MVBS_ds.sel(channel=channel)
    )

    return (
        dataset.to(
            holoviews.Image,
            kdims=["ping_time", vert_dim],
            vdims=["Sv"],
        )
        .relabel(str(channel))
        .opts(invert_yaxis=True)
    )


def tricolor_echogram(
    MVBS_ds: xarray.Dataset,
    channel: list[str],
    vmin: float,
    vmax: float,
    vert_dim: str = "echo_range",
):
    """
    Create a tricolor RGB echogram.

    ``vmin`` and ``vmax`` are data-normalization limits here,
    rather than ordinary display limits.
    """
    if len(channel) != 3:
        raise ValueError(
            "Exactly 3 channels are required for a tricolor echogram."
        )

    rgb = [
        _convert_to_color(
            MVBS_ds=MVBS_ds,
            channel=ch,
            vmin=vmin,
            vmax=vmax,
            vert_dim=vert_dim,
        )
        for ch in channel
    ]

    return holoviews.RGB(
        (
            MVBS_ds["ping_time"].data,
            MVBS_ds[vert_dim].data,
            rgb[0],
            rgb[1],
            rgb[2],
        )
    ).opts(invert_yaxis=True)


def _convert_to_color(
    MVBS_ds: xarray.Dataset,
    channel: str,
    vmin: float,
    vmax: float,
    vert_dim: str = "echo_range",
):
    """Normalize one Sv channel to [0, 1] for RGB display."""
    if vmax <= vmin:
        raise ValueError("vmax must be greater than vmin.")

    sv = MVBS_ds["Sv"].sel(channel=channel)
    sv = sv.clip(min=vmin, max=vmax)

    normalized = (sv - vmin) / (vmax - vmin)

    return numpy.asarray(
        normalized.transpose(
            vert_dim,
            "ping_time",
        ).data
    )